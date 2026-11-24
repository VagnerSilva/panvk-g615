# Plano de implementação corrigido: sync_file via KCPU e CQS64 (006-kbase-kcpu-gpu-fence-wait.patch)

> **Para execução por agentes:** usar a skill instalada `executing-plans`, tarefa por tarefa. Este documento não autoriza aplicação de patches Mesa, alterações de contratos/perfis, testes no dispositivo, commits ou publicação sem aprovação explícita.

**Objetivo:** permitir que submissões PanVK elegíveis aguardem `sync_file` sem bloquear a thread de submit, preservando dependências, propagação de erros e vida útil dos recursos.

**Arquitetura proposta:** uma fila KCPU de importação dedicada por `panvk_gpu_queue`, evitando uma FIFO compartilhada entre filas Vulkan independentes. A ponte executa três `ioctl`s FIFO: `FENCE_WAIT`, `CQS_SET_OPERATION` na célula A (payload/erro), depois `CQS_SET_OPERATION` na célula B (done). Ambas são slots CSF_EVENT distintos, alinhados a 64 bytes e exclusivos da fila. As subfilas CSF devem aguardar B, ler o erro de A e impedir qualquer `CALL`/dispatch dependente em erro. A ordenação CPU/GPU e a integração desse controle ainda precisam ser demonstradas.

**Tecnologias:** Mesa 27 (`13baeb70c066a9f82d2bcfb29f06e4865212affa`), PanVK v11, Kbase CSF 1.21 (`mali_kbase_mt6878_r44` / `mali-r44p1`), C, Meson/Ninja, Android/Bionic, Linux/glibc e `unittest` com mocks C.

**Estado:** preparação inativa de submissão, guarda e conclusão da Tarefa 3 autorizada separadamente pelo usuário em 2026-11-24, com 95 testes host PASS. O patch 006 inclui essa integração, mas não tem seleção de build; o knob de runtime tem default false. Gate de segurança 1.3 continua `BLOCKED`: mocks e encoding não qualificam publicação CPU/GPU, término real CSF, builds ou hardware.

---

## Restrições globais

- Mesa fixada em `13baeb70c066a9f82d2bcfb29f06e4865212affa`, conforme `sources.lock`; não mudar a revisão.
- Perfil único `g615-v11-csf`, `PAN_ARCH 11`, Kbase CSF 1.21; não introduzir JM ou suporte a outras GPUs.
- Moto G86 (`ZF525GRGXD` / Mali-G615 MC2 / MT6878 / kernel `6.1.157-android14-11`) é o alvo operacional. Poco X6 Pro (Mali-G615 MC6) é referência histórica; novos testes nele exigem aprovação de escopo.
- Android/Bionic e glibc no chroot do aparelho têm gates separados. Nenhum resultado de um ABI ou aparelho qualifica outro.
- Preservar as fontes originais e alterações do usuário. Não remover ou resetar `work/` (incluindo `work/mali_kbase`). Preparar o delta Mesa em cópia descartável e aplicá-lo somente após autorização explícita.
- Manter `002–005` na série padrão. O novo `006` deve ser experimental e explicitamente selecionado (`--with-kbase-gpu-fence-waits`, variante `kbase-sync-002-006`).
- Limitar valores reservados na mesma célula a `1 .. UINT32_MAX`, sem reutilização ou wraparound. Esgotamento usa fallback CPU com diagnóstico explícito, sem enqueue ou publicação de staging da ponte; não zerar o contador para contornar o limite.
- Não usar `ERROR_BARRIER` para tratar falha de fence: ele limpa o estado de erro, não cancela nem impede trabalho dependente. Erro assíncrono não pode ser convertido em sucesso ou recuperado implicitamente.
- Não criar commits nem publicar alterações durante a execução deste plano sem autorização específica.

---

## 1. Diagnóstico e Evidências de Kernel (Tarefa 1 — BLOCKED)

### 1.1 Evidência do Aparelho e Módulo Kernel

Identidade e configuração do aparelho informadas pelo usuário; não foram consultadas no dispositivo nesta execução. Observações nas fontes são evidência estática, não validação de runtime.

- **Dispositivo alvo:** Moto G86 (`ZF525GRGXD`)
- **Kernel & ABI:** `6.1.157-android14-11-g5a734836436c SMP preempt mod_unload modversions aarch64`
- **Módulo ativo:** `/vendor/lib/modules/mali_kbase_mt6878_r44.ko` (`srcversion: 865651A7DB16256801B8202`, `/dev/mali0` `10:109`)
- **Configuração confirmada:** `CONFIG_SYNC_FILE=y`
- **Fonte DDK de referência:** `work/mali_kbase` (`NothingOSS/android_kernel_modules_nothing_mt6878`, branch `mt6878/Tetris/u`, `gpu/gpu_mali/mali_avalon/mali-r44p1/drivers/gpu/arm/midgard`)

### 1.2 Observações Estáticas e Contratos Exigidos (`work/mali_kbase/csf/mali_kbase_csf_kcpu.c`)

| Contrato                                    | Comportamento Verificado no Kernel (`mali-r44p1`)                                                                                                                                                                                            | Regra Imposta à Implementação                                                                                                                                                                                                                          |
| ------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Aceitação e Atomicidade (`ENQUEUE`)** | `kbase_csf_kcpu_queue_enqueue` rejeita `nr_commands != 1` (`-EINVAL`). Capacidade `KBASEP_KCPU_QUEUE_SIZE = 256`; não há consulta de espaço livre ou rollback entre `ioctl`s. | Três enqueues FIFO. Falha no 1º = `REJECTED`; falha no 2º/3º = `FATAL`, exigindo futura integração com `vk_queue_set_lost`. Até 85 triplas rastreadas; avanço em B devolve créditos, mantendo margem de um comando final ainda não retirado. |
| **Posse do FD (`FENCE_WAIT`)**              | `kbase_kcpu_fence_wait_prepare` chama `sync_file_get_fence(fence.basep.fd)` síncronamente no `ENQUEUE`.                                                                                                                                      | Fechar a duplicata `CLOEXEC` imediatamente após o `ENQUEUE` retornar (sucesso ou falha).                                                                                                                                                               |
| **Propagação de Erro (`fence->error < 0`)** | O dispatcher de `kcpu_queue_process` marca `queue->has_error` quando `kbase_kcpu_fence_wait_process` retorna status negativo. SET grava primeiro `val`, depois o campo `error`; `ERROR_BARRIER` apenas limpa `has_error`. A publicação consistente do par valor/erro ao consumidor ainda não está demonstrada. | Impedir trabalho dependente no próprio caminho GPU antes de executá-lo, com mecanismo e ordenação comprovados. Consultar erro na CPU antes de retornar sucesso na conclusão e marcar a fila perdida. Não enfileirar `ERROR_BARRIER` como tratamento de falha. |
| **Término Seguro (`DELETE`)** | `delete_queue` drena os comandos, inclusive SET pendentes, e chama `cancel_work_sync`/`destroy_workqueue`. DELETE não é rollback: pode escrever no CQS antes de retornar. | Manter o BO vivo até término seguro comprovado; verificar callbacks, timers e workers da configuração efetiva. DELETE sempre antes de liberar `kbase_seqnos`; falha de DELETE não autoriza liberar/reutilizar recursos. |
| **Faixa de Sequência & Visibilidade U64** | O scheduler local lê 32 bits inferiores de `panvk_cs_sync64`; SET exige alinhamento de 16 bytes e notifica o firmware. A falha de reavaliação no limite de 2³² foi reproduzida em host com a função real. | Publicar somente `1 .. UINT32_MAX`, sem reutilização; fallback CPU no esgotamento. Reservar slot completo alinhado a 64 bytes em memória `BASE_MEM_CSF_EVENT`, sem sobreposição. Alinhamento/notificação não provam publicação atômica de valor e erro. |

### 1.3 Gate para avançar à implementação

- **Desenho especificado para os testes da Tarefa 3:** duas células exclusivas da fila, A (`cqs_payload_addr`, payload/erro) e B (`cqs_done_addr`, conclusão). Em `kbase_subqueue_emit_job`, usar somente os quatro registradores não preservados: `addr64` ocupa dois; `val32` e `val64` compartilham os outros dois.
  1. Carregar o endereço de B em `addr64` e `target_seqno - 1` em `val64`; emitir `cs_sync64_wait(&b, false, MALI_CS_CONDITION_GREATER, val64, addr64)`.
  2. Emitir `cs_flush_caches` com CLEAN_AND_INVALIDATE para L2/LSC e INVALIDATE para os demais caches, seguido de `cs_wait_slot(&b, SB_ID(IMM_FLUSH))`, antes de ler A, inclusive quando `BASE_MEM_CSF_EVENT` estiver cached.
  3. Carregar o endereço de A em `addr64`; emitir `cs_load32_to(&b, val32, addr64, offsetof(struct panvk_cs_sync64, error))` e `cs_wait_slot(&b, SB_ID(LS))`.
  4. Usar `cs_if(&b, MALI_CS_CONDITION_EQUAL, val32)` para envolver o `cs_call(&b, addr64, val32)` dependente, carregando seus operandos somente dentro do ramo de sucesso. `cs_else(&b)` não executa o CALL em erro. Manter `assert(entry_size <= KBASE_RING_JOB_MAX_SIZE)`; não ampliar o ring para contornar estouro.
- **Conclusão e pré-validação:** após B atingir `target_seqno`, invalidar o cache CPU das células quando necessário e verificar `cell_a->error` antes de aceitar sucesso, inclusive quando o seqno de conclusão já foi atingido. Erro chama `vk_queue_set_lost` e retorna `VK_ERROR_DEVICE_LOST`, sem sinalizar sucesso nas saídas e sem depender de nova submissão.
- **Teardown exigido:** terminar consumidores CSF antes de destruir a fila KCPU; chamar `kbase_kmod_csf_fence_import_queue_destroy(queue->kbase_import_queue)` antes de `pan_kmod_bo_put(queue->kbase_seqnos.bo)`. O protótipo real da Tarefa 2 recebe o handle, não `&queue->kbase_import_queue`. Somente retorno 0 permite liberar o BO e limpar os handles; falha retém handle/BO e registra diagnóstico fatal.
- **Correção de localização confirmada no patch 007:** o hunk `@@ -599,6 +1857,10 @@` pertence a `cleanup_queue`, não ao término de `panvk_gpu_queue_finish`. No hunk `@@ -1487,10 +3181,25 @@`, o caller chama `cleanup_queue(queue)` antes de `kbase_destroy_group(queue)`. Portanto, não é válido presumir que o grupo já terminou no ponto de liberação do BO. A integração deve corrigir a ordem e cobrir também inicialização parcial e falhas de término, sem liberar memória ainda acessível ao kernel.

- [ ] Demonstrar que uma fence pendente que sinaliza com erro não libera nenhum `CALL`/dispatch dependente. Especificar os comandos/controle de fluxo GPU e a propagação da falha à conclusão PanVK, sem depender de uma submissão futura.
- [ ] Fechar a ordenação de publicação de valor e erro. Em `work/mali_kbase/csf/mali_kbase_csf_kcpu.c:1243`, SET escreve o valor antes do erro e só depois notifica. Uma leitura GPU de `error` após observar o valor não está, por si só, comprovada como snapshot consistente; não presumir que a doorbell impede observação intermediária.
- [ ] Comprovar término de callbacks, timers e workers nos caminhos normais, de erro e aceitação parcial, para a configuração efetiva do kernel. Confirmar que não haverá futuras escritas antes de liberar/reutilizar o BO.

**Decisão:** manter o caminho ativo de espera CPU e o gate `BLOCKED` enquanto faltar qualquer contrato acima. O desenho define critérios de aceitação, não prova publicação CPU/GPU ou término seguro. A autorização posterior permite preparar call sites PanVK apenas no draft inativo, com testes host; não permite ativação nem declarar os contratos fechados com base nos mocks.

**Correções ao desenho fornecido:** `cs_sync64_wait(b, reject_error, cond, ref, addr)` não recebe escopo SYSTEM na Mesa fixada. Regiões coerentes/uncached não provam, isoladamente, ordenação entre células. Gravar `cell_a.error = 1` antes do DELETE não é proteção, pois o SET drenado sobrescreve o campo com `queue->has_error`; é necessário confirmar a terminação dos consumidores antes do drain.

### 1.4 Execução do gate de publicação em 2026-11-24

- **Inputs:** repositório `de5675b8026f43e35a944a0ace7b225472cdb7c3`,
  Mesa fixada em `13baeb70c066a9f82d2bcfb29f06e4865212affa`;
  `work/mali_kbase/SOURCE_REV.txt` declara
  `5f75a3b13e8135d45b4b0b70ec893345144f70df`.
  SHA-256 do `csf/mali_kbase_csf_kcpu.c` examinado:
  `dd42ae5d789e0190955ba000956dab77ca16a01809ea2247b74c97e875d8c348`.
- **Método:** fixture host temporária extraiu sem alterações os helpers
  SET32/SET64 e `kbase_kcpu_cqs_set_operation_process` da fonte real.
  Compilação com `cc -std=c11 -Wall -Wextra -Werror`, incluindo o header
  UAPI local. Mapping, locks, notificações e trace foram substituídos por mocks.
  O ponto de trace entre o store do valor e o store do erro executou um
  observador intercalado que testa `value > 6` seguido de `error == 0`.
- **Controle:** SET de fence sem erro publicou valor 7 e erro 0; o leitor
  intermediário observou essa mesma combinação.
- **REPRODUCED no modelo host:** com `queue->has_error=true`, o leitor
  intermediário também observou valor 7 e erro 0. Só depois o handler
  escreveu erro 1 e notificou. Assim, esperar o valor e ler o erro dessa
  mesma célula não distingue sucesso de publicação ainda incompleta.
  O processo terminou com código 0 porque reproduziu o caso esperado;
  isso não é PASS do protocolo de sincronização.
- **Limite da evidência:** a observação GPU/firmware dessa janela é `UNKNOWN`,
  não foi executada. O comentário em
  `work/mali_kbase/csf/mali_kbase_csf_event.c:127` informa que qualquer
  CS/GLB doorbell reavalia waits pendentes; não há exclusividade de
  notificação estabelecida que feche a janela para o protocolo atual.
- **Resultado:** checagem valor/erro na mesma célula `FAIL` no modelo;
  gate de publicação `BLOCKED`. Interrompido no primeiro gate causal,
  antes da implementação, replay, builds ou hardware. Término seguro
  continua pendente e não foi aprovado por esse teste.
- **Próxima decisão:** manter espera CPU ou autorizar investigação de um
  protocolo distinto de publicação, por exemplo com marcador de conclusão
  separado do payload de erro. Essa hipótese exige prova de ordenação e
  revisão explícita; não está aprovada nem implementada e não autoriza
  alterar o DDK ou presumir que um comando/slot extra basta.

### 1.5 Preparação isolada da Tarefa 2 em 2026-11-24

- **Autorização:** o usuário aprovou avançar aos testes RED e à ponte isolada; os resultados negativos da seção 1.4 permanecem como evidência histórica do desenho de célula única.
- **Base:** cópia de apenas três arquivos do snapshot Mesa previamente preparado em `wait-any-build/build/mesa-candidate`, na revisão fixada. Os inputs do manifest foram comparados ao repositório: a única divergência foi sync 005, que modifica somente `panvk_physical_device.c`, fora dos três destinos desta etapa. Não reaplicamos patches nem alteramos os snapshots originais.
- **RED:** a compilação da fixture falhou por ausência da UAPI SET e das funções de importação (exit 1).
- **GREEN / HOST_TEST_PASS:** `python3 -m unittest discover -s tests -p test_kbase_gpu_fence_wait.py -v`: 18 testes, zero falhas. Fixture compilada com `cc -std=c11 -Wall -Wextra -Werror`, extraindo a implementação real do patch 006.
- **Regressão compartilhada:** discovery com `-p 'test_kbase_*wait*.py'` executou 19 testes, incluindo WAIT_ANY, sem falhas.
- **Aplicabilidade estática:** `git apply --cached --check --whitespace=error -v` passou contra o índice baseline da cópia isolada, sem offsets. Não foi aplicação ou replay da série completa. Revisão independente do escopo da Tarefa 2 não encontrou problemas significativos.
- **Proveniência:** `compute-patch-series-id.py --profile g615-v11-csf` recalculou `sha256:be5e8d3de756c5db3b668dd5cc7de9242919f173f94afccda76c30fd9fd81289`. Esse digest inclui o draft não selecionado; não identifica um binário testado. `sources.lock`, perfil e configuração de release não foram alterados.
- **Cobertura:** três comandos FIFO, erros no primeiro/segundo/terceiro enqueue, IDs independentes com progresso modelado separado, FD consumido inclusive em rejeição, errno causal, DELETE falho com handle retido, limite UINT32_MAX sem reutilização, saturação de 85 triplas e done publicado antes da retirada do último comando.
- **Limites:** FIFO, conclusão e escritas de DELETE usam mocks. Não é prova de coerência/ordenação CPU-GPU, término real de consumidores, propagação da falha à conclusão Vulkan ou eficácia de uma guarda GPU. O resultado de publicação de duas células informado pelo usuário não foi reproduzido pela fixture desta etapa.
- **Entrega:** 006 contém somente UAPI e ponte Kmod (três destinos); os quatro destinos PanVK, a seleção e os builds permanecem não implementados. Seu header o identifica como DRAFT inativo.

---

## 2. Mapa de Arquivos

### 2.1 Delta Mesa (`patches/experimental-kbase-sync/006-kbase-kcpu-gpu-fence-wait.patch`)

O patch conterá **somente** estes sete destinos na cópia Mesa preparada:

| Destino Mesa                                   | Responsabilidade                                                                                                                                                                                                         |
| ---------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `include/drm-uapi/mali_kbase_ioctl.h`          | Definições `BASEP_CQS_SET_OPERATION_ADD/SET`, `base_cqs_set_operation_info` (24B), `base_kcpu_command_cqs_set_operation_info` (16B) e membro na `union info` (mantendo `base_kcpu_command` com 24B, `info` no offset 8). |
| `src/panfrost/lib/kmod/kbase_kmod.h`           | Handle opaco `struct kbase_kmod_csf_fence_import_queue`, enum `kbase_kmod_csf_fence_import_result` e protótipos `create`/`import`/`destroy`.                                                                             |
| `src/panfrost/lib/kmod/kbase_kmod.c` | Criação, enfileiramento em 3 etapas, créditos conservadores, FD consumido, `OK`/`REJECTED`/`FATAL`, preservação de `error_out` e DELETE retryable com handle retido; sem `ERROR_BARRIER`. Preparado na Tarefa 2; terminação dos consumidores é pré-condição da futura integração. |
| `src/panfrost/vulkan/panvk_physical_device.h`  | Protótipo `panvk_kbase_sync_dup_sync_file_fd`; preparado no draft inativo da Tarefa 3. |
| `src/panfrost/vulkan/panvk_physical_device.c`  | Snapshot sob `ks->mutex` e duplicação `F_DUPFD_CLOEXEC`, preparado e testado em host. Lifetime continua externamente sincronizado; não autoriza destruição concorrente. |
| `src/panfrost/vulkan/csf/panvk_queue.h`        | Handle `kbase_import_queue` e contador monotônico `kbase_import_seqno` por `panvk_gpu_queue`.                                                                                                                            |
| `src/panfrost/vulkan/csf/panvk_vX_gpu_queue.c` | Slot CQS reservado, knob `PANVK_KBASE_GPU_FENCE_WAITS` (default `false`), faixa `1 .. UINT32_MAX`, staging transacional e prevenção de execução dependente em erro conforme gate 1.3; conclusão verifica erro antes de sucesso e teardown termina KCPU antes de liberar `kbase_seqnos`. |

### 2.2 Alterações Diretas no Repositório `panvk-kbase-android`

- `scripts/apply-patches.sh`: flag `--with-kbase-gpu-fence-waits` (apenas para `g615-v11-csf`; prevalece sobre `--with-kbase-sync`).
- `scripts/build_provenance.py`: variante `kbase-sync-002-006` com inputs ordenados `002..006`.
- `scripts/build-glibc.sh`: encaminhamento da flag experimental na preparação e manifest.
- `tests/test_anb_dma_buf_fd.py` e `tests/test_g615_build_series.py`: cobertura para padrão (`002..005`), legado (`002..005`) e experimental (`002..006`).
- `tests/test_kbase_gpu_fence_wait.py`: suíte C compilada com mocks para contratos UAPI, Kmod e PanVK.
- `patches/experimental-kbase-sync/README.md` e `patches/README.md`: documentação da variante experimental e evidência `mali-r44p1`.

---

## 3. Tarefas de Implementação

### Tarefa 1: Confirmar contrato do kernel e desenho de progresso — **[PARCIAL / BLOCKED]**

- [x] Confirmar aparelho (`Moto G86`), módulo (`mali_kbase_mt6878_r44`), kernel (`6.1.157-android14-11`) e `CONFIG_SYNC_FILE=y`.
- [x] Auditar `kbase_csf_kcpu_queue_enqueue`, `kbase_kcpu_fence_wait_prepare/process`, `kbase_kcpu_cqs_set_operation_process` e `delete_queue` (`cancel_work_sync` + `destroy_workqueue`) em `work/mali_kbase/csf/mali_kbase_csf_kcpu.c`.
- [x] Definir fila KCPU dedicada por `panvk_gpu_queue` e faixa `1 .. UINT32_MAX`.
- [ ] Fechar os três contratos da seção 1.3 antes da integração ativa. Preparação isolada da Tarefa 2 autorizada separadamente; não marcar segurança PASS apenas por adicionar um requisito ou mock.

### Tarefa 2: UAPI e ponte KCPU isolada (Ciclo TDD: RED -> GREEN)

**Escopo autorizado:** testes host e patch parcial inativo, sem exigir aprovação fictícia do gate 1.3. `OK` comprova aceitação dos três comandos, não sinalização ou sucesso da fence; `REJECTED` exige nenhum comando aceito e `FATAL` cobre aceitação parcial. Preservar o erro causal em `error_out`, independentemente do cleanup. `import` consome o FD duplicado em todos os retornos; `destroy` exige consumidores terminados e retém handle/BO em falha.

- [x] **RED:** Criar `tests/test_kbase_gpu_fence_wait.py` com harness C compilado testando:
  - `test_uapi_struct_sizes_and_offsets` (`sizeof(struct base_kcpu_command) == 24`, `offsetof(info) == 8`)
  - `test_partial_enqueue_is_fatal` (1º `ENQUEUE` OK, 2º falha -> `KBASE_CSF_FENCE_IMPORT_FATAL` + `error_out` preservado)
  - `test_first_enqueue_rejected_is_rejected` (1º `ENQUEUE` falha -> `KBASE_CSF_FENCE_IMPORT_REJECTED`)
  - `test_independent_queues_make_progress` (filas independentes criam IDs KCPU distintos sem bloqueio mútuo)
  - `test_pending_destroy_keeps_cqs_alive` (DELETE modelado pode escrever nas células; falha retém o handle. Vida útil do BO no caller PanVK permanece na Tarefa 3)
  - `test_fence_error_is_not_success` (fence inicialmente pendente depois sinaliza com erro; SET propaga `err != 0` e o retorno síncrono `OK` não é interpretado como sucesso da fence; integração impeditiva do trabalho é testada na Tarefa 3)
  - `test_invalid_args_rejected_without_ioctl` (`fd < 0`, `cqs_addr & 15 != 0`, `target_seqno == 0` ou `target_seqno > UINT32_MAX`)
  - `test_last_valid_target_and_out_of_range` (último alvo `UINT32_MAX` é válido; alvo acima do limite é rejeitado antes de qualquer ioctl)
- [x] Rodar discovery da suíte e confirmar falha **RED** pela ausência das funções/UAPI.
- [x] **GREEN:** Implementar UAPI e ponte em cópia isolada; gerar 006 parcial sem aplicá-lo.
- [x] Rodar `python3 -m unittest discover -s tests -p test_kbase_gpu_fence_wait.py -v` e confirmar **GREEN** (18 casos, incluindo terceiro enqueue, capacidade e falhas de close).

### Tarefa 3: Snapshot `sync_file` e integração transacional PanVK

**Pré-requisito da integração GREEN:** fechar os contratos da seção 1.3; os testes host da Tarefa 2 não os substituem. O início dos testes RED foi solicitado separadamente pelo usuário.

- [ ] **RED:** Expandir `tests/test_kbase_gpu_fence_wait.py` com casos PanVK:
  - `panvk_kbase_sync_dup_sync_file_fd` (payload não elegível, `SIGNALED`, `PENDING` com `F_DUPFD_CLOEXEC`, falha de `fcntl` retornando `VkResult` de erro sem mascarar).
  - Pré-validação de `staged` (saturação de 6 waits em uma subfila, mesclagem por endereço com `MAX2(seqno)`, `has_gpu_work == false`, knob `PANVK_KBASE_GPU_FENCE_WAITS=0` vs `1`).
  - `test_pending_fence_error_prevents_dependent_work` (trabalho dependente já submetido enquanto fence está pendente; após erro, nenhum `CALL`/dispatch dependente executa, nenhuma saída sinaliza sucesso e a fila é reportada perdida, sem exigir nova submissão).
  - `test_completion_error_precedes_seqno_success` (seqno atingido com erro retorna falha, não sucesso; repetir com fence já sinalizada com erro).
  - `test_value_visible_before_error_is_not_success` (consumidor observa atualização do valor antes do erro; o protocolo aprovado no gate 1.3 não permite executar trabalho com o erro antigo).
  - `test_import_seqno_exhaustion_uses_cpu_fallback` (último alvo `UINT32_MAX` usa referência `UINT32_MAX - 1`; a importação seguinte usa fallback CPU sem enqueue, reset do contador ou publicação de staging da ponte).
  - Aceitação parcial no último alvo exige `FATAL`/fila perdida, sem reutilização do valor; não transformar fila perdida em fallback utilizável.
  - Destruição e falha posterior de emissão/kick mantêm o CQS vivo até término KCPU seguro; falha de cleanup preserva o erro inicial.
  - `test_group_termination_precedes_import_delete_and_bo_release`: terminar consumidores/grupos antes de DELETE KCPU e liberar BO somente após DELETE retornar 0. Falha de término ou DELETE retém recursos e emite diagnóstico; não presumir a ordem a partir do hunk de `cleanup_queue`.
- [ ] **GREEN:** Implementar snapshot e integração somente pelo mecanismo aprovado no gate 1.3, sem ampliar concorrência de destruição nem usar `ERROR_BARRIER` como recuperação.
- [ ] Executar as suítes relevantes com `PYTHONPATH=tests`, incluindo `test_kbase_gpu_fence_wait` e `test_kbase_wait_any`; exigir GREEN dos casos previstos. Build, replay, runtime e estabilidade têm gates separados e não são certificados por mocks.

#### Início do RED da Tarefa 3 em 2026-11-24

- **Escopo executado:** seis casos de snapshot: tipo de sync estrangeiro, payload pendente não sync_file, SIGNALED, duplicação CLOEXEC sob mutex, falha de fcntl sem consumo do payload e propagação de FAILED/DEVICE_LOST.
- **RED confirmado:** `python3 -m unittest discover -s tests -p 'test_kbase_gpu_fence_wait.py' -k PanVKSyncFileSnapshotTests -v`: seis falhas (exit 1), todas pela ausência de `panvk_kbase_sync_dup_sync_file_fd` no draft 006. A extração falha antes da compilação C; ainda não há evidência de execução dos asserts do harness.
- **Regressões PASS:** `PYTHONPATH=tests python3 -m unittest test_kbase_gpu_fence_wait.GPUFenceImportTests test_kbase_wait_any -v`: 19 testes, zero falhas.
- **Whitespace:** `git diff --check` passou para as alterações não staged desta etapa. `git diff --cached --check` falhou em seis linhas de contexto do patch 006 já staged antes desta etapa; esse patch não foi alterado.
- **Ruling:** a premissa de grupos já terminados no hunk 1857 foi rejeitada pela ordem real do caller no patch 007. O requisito permanece término CSF, DELETE KCPU, liberação do BO, nessa ordem. Uma interpretação incorreta permite acesso do kernel a BO liberado.
- **Pendente:** demais casos RED de staging, emissão GPU, conclusão, esgotamento e teardown; integração GREEN; prova de publicação e término. Tarefa 3 não concluída. Nenhum patch Mesa foi aplicado ou modificado; builds, replay, hardware, commits e publicação não executados.

#### Correção isolada do snapshot da Tarefa 3 em 2026-11-24

- **Autorização e limite:** o usuário pediu análise e correção do helper. Preparado somente o snapshot e seu protótipo no draft 006, sem aplicar patches, ativar a ponte, alterar perfis/contratos ou implementar call sites de submissão.
- **Análise confirmada:** `get_device_sync_types_kbase` copia `kbase_cpu_sync_type` para o dispositivo. O helper identifica Kbase pelo callback `wait_many`, seguindo os helpers peek existentes; comparação com o endereço do tipo estático seria incorreta. A fixture foi corrigida para usar um tipo copiado por dispositivo.
- **Contrato:** `PENDING` com callback sync_file e waiter válido duplica o FD sob mutex. O original, estado e payload são preservados. `FAILED` propaga o resultado armazenado; SIGNALED, RESET, WAITING e payload não elegível não produzem FD. `VK_SUCCESS` com FD `-1` não declara a dependência satisfeita: o caller mantém o caminho CPU existente. Lifetime continua externamente sincronizado.
- **Erros:** waiter ausente ou FD negativo retornam erro diagnosticado. A duplicação salva errno antes do unlock e classifica EMFILE/ENFILE como TOO_MANY_OBJECTS, EBADF como INVALID_EXTERNAL_HANDLE, ENOMEM como OUT_OF_HOST_MEMORY e demais como UNKNOWN.
- **RED observado:** dez métodos com 15 casos falharam pela ausência do helper antes de sua implementação. **GREEN / AUTOMATED_TEST_VALIDATED:** `PYTHONPATH=tests python3 -m unittest test_kbase_gpu_fence_wait test_kbase_wait_any -v` passou 29 testes. Os casos snapshot incluem mutex, estado/payload preservados, errno alterado pelo mock de unlock e FD_CLOEXEC real com pipe host sobrevivendo ao fechamento do original. O pipe não valida sync_file ou GPU.
- **Aplicabilidade estática PASS:** `git apply --check --whitespace=error -v` e o equivalente `--cached --check` passaram, sem offsets, contra cinco arquivos copiados do snapshot preparado em `wait-any-build/build/mesa-candidate`. O blob de physical_device.c é exatamente `d5dd3357c0b5d2ef889f11d6bc30ab452d06b680`, post-005 atual; os três blobs Kmod/UAPI correspondem aos índices base do draft 006. Nenhum patch foi aplicado à cópia ou aos originais.
- **Whitespace PASS nesta correção:** `git diff --check` passou para o delta não staged. As seis linhas de contexto já staged no draft anterior permanecem; não foram alteradas fora do escopo.
- **Proveniência recalculada:** `compute-patch-series-id.py --profile g615-v11-csf`: `sha256:16641299993cd5e42d3985a63056dc3b06ce05136c844c2553c1fe694d08e662`. Inclui o draft inativo; não identifica um binário validado. `sources.lock`, perfil e seleção de build não foram alterados.
- **Ruling:** autorização para corrigir o snapshot permite apenas esta preparação isolada; não fecha nem contorna o gate 1.3. WAITING fica no caminho CPU, sem ampliar o contrato de concorrência. Se um futuro caller interpretar ausência de FD como conclusão, poderá executar trabalho antes da dependência.
- **Pendente:** staging, guarda GPU, conclusão, esgotamento e teardown da Tarefa 3. Build Mesa Android/glibc, replay completo, hardware e estabilidade `NOT EXECUTED`; gate 1.3 `BLOCKED`.

#### Expansão dos testes RED da integração PanVK em 2026-11-24

- **Autorização e escopo:** o usuário pediu os testes da próxima etapa. Adicionados 20 casos em `PanVKFenceIntegrationTests` e a fixture C `tests/kbase_gpu_fence_wait_panvk.c`. Nenhum patch Mesa, perfil ou fonte preparada foi alterado ou aplicado; sem acesso ao dispositivo.
- **Fonte sob teste:** `PANVK_KBASE_TEST_MESA` seleciona explicitamente uma árvore Mesa preparada, lida sem alterações. O runner confere HEAD contra `sources.lock` e extrai as funções reais de emissão, espera de conclusão, staging/submissão, registro do callback de saída, cleanup e destruição. A árvore examinada é `wait-any-build/build/mesa-candidate`, HEAD `13baeb70c066a9f82d2bcfb29f06e4865212affa`, post-002--005, sem integração de submissão 006. Blobs Git: `panvk_vX_gpu_queue.c` = `a48e72e6077e333d4d8d82e07e54e170dffc8467`; `panvk_queue.h` = `6da111c2d88b01affae451ae2378011b62ecdccc`, inalterados após os testes.
- **Método:** as funções extraídas são compiladas com `cc -std=c11 -Wall -Wextra -Werror`. Stubs substituem operações de kernel, cache, BO e publicação. O interpretador simbólico executa os builder calls, modelando espera pendente, erro cached, registradores de 32 bits compartilhados e callback de conclusão. Não executa nem valida ISA, firmware ou ordenação CPU/GPU real.
- **RED observado:** `PANVK_KBASE_TEST_MESA=<árvore preparada> PYTHONPATH=tests python3 -m unittest test_kbase_gpu_fence_wait.PanVKFenceIntegrationTests -v`: 20 testes executados, 15 falhas de comportamento esperadas, cinco controles PASS; nenhum erro de compilação/setup. As falhas observam CALL após fence em erro, sucesso antes da inspeção de erro, callback de saída retornando sucesso, teardown fora de ordem e ausência do caminho de importação assíncrona/contador.
- **Controles PASS:** fence sem erro executa exatamente um CALL; saturação de seis waits não publica staging parcial; endereço repetido usa MAX2(seqno) mesmo no limite; ausência de trabalho GPU e knob desligado mantêm espera CPU.
- **Regressões PASS:** `PYTHONPATH=tests python3 -m unittest test_kbase_gpu_fence_wait.GPUFenceImportTests test_kbase_gpu_fence_wait.PanVKSyncFileSnapshotTests test_kbase_wait_any -v`: 29 testes, zero falhas. Discovery sem árvore selecionada: 28 testes executam e 20 casos de integração são explicitamente SKIP, não PASS.
- **Ruling:** a nova suíte recebe uma árvore preparada por variável de ambiente, em vez de aplicar 006 ou copiar uma implementação para os testes. Isso preserva a fronteira de autorização e mantém os checks ligados às funções reais. A seleção de uma árvore desatualizada testa essa árvore, não o draft; a revisão e os blobs precisam acompanhar qualquer resultado futuro.
- **Limites e pendências:** as condições posteriores à aceitação parcial/importação e o fallback após o último alvo ainda não são alcançados nesta árvore, que falha antes por não integrar 006. A preservação do erro causal durante cleanup combinado e os caminhos de inicialização parcial exigem cobertura adicional quando o mecanismo de integração estiver definido. Tarefa 3 não concluída; gate 1.3 `BLOCKED`, builds/replay completo/hardware/estabilidade `NOT EXECUTED`.

#### Teardown verificado preparado no 006

- **Escopo autorizado:** o usuário escolheu corrigir a ordem e propagar falhas
  CSF no próprio 006, com testes das funções reais. A preparação continua
  inativa; não autoriza integração de submissão, mudança do gate 1.3 ou testes
  novos no aparelho.
- **Correção:** `cleanup_queue` mantém `kbase_seqnos.bo`. Os callers reais
  `create_gpu_queue`/`destroy_gpu_queue` terminam grupos CSF, limpam tiler,
  executam `kbase_finish_fence_import_and_seqnos` e liberam o BO somente após
  DELETE bem-sucedido. Inicialização parcial dos grupos passa pelo caller
  comum, sem cleanup interno que esconda falhas.
- **Correção da revisão:** não apenas o BO de eventos, mas também contextos,
  buffers de subfila, descriptor ring e syncobjs permanecem vivos até o
  término CSF verificado. Em Kbase, `init_queue` delega cleanup de erro ao
  caller; uma flag local protege o caso em que sua inicialização não começou.
  A ordem de cleanup Panthor é preservada.
- **APIs reais:** `kbase_destroy_group`, `kbase_kmod_csf_queue_term` e
  `kbase_kmod_csf_group_destroy` antes eram void; o mock int não comprovava
  propagação real. O 006 passa a verificar retornos, preservar errno e reter
  USER_IO/ring BO em falha de término/unmap. Sucesso do ioctl não certifica
  término efetivo de firmware.
- **Falha fatal:** reter fila KCPU, BO de eventos e alocação da fila driver.
  Marcar a fila Vulkan perdida e executar `vk_queue_finish` para removê-la da
  lista do dispositivo, sem liberar recursos visíveis ao kernel. Isso evita
  novo teardown pelo cleanup da inicialização. Preservar o VkResult causal;
  a retenção é uma limitação de reclamabilidade, não autorização para retry
  através da fila Vulkan finalizada.
- **RED -> GREEN / host:** oito métodos em `CheckedFenceTeardownTests`,
  cobrindo 15 cenários, extraem funções reais Kmod/PanVK e mockam somente
  syscalls/recursos. A regressão de finalização/desvinculação Vulkan falhou em
  sete cenários antes da correção. A suíte focada com os três casos anteriores
  de teardown e regressões bridge/snapshot/WAIT_ANY passou 40 testes.
  A regressão adicional extrai o `init_queue` real e rejeita cleanup de memória
  enquanto consumidores estão vivos, inclusive após falha da espera de
  conclusão. Nove cenários falharam antes de adiar cleanup; a suíte focada
  voltou a passar 40 testes após a correção.
- **Integração restante:** a suíte completa de 20 casos da Tarefa 3 executou
  oito PASS e 12 RED para submissão, guarda GPU, conclusão e erros. Não marcar
  a Tarefa 3 GREEN completa.
- **Aplicabilidade:** draft ampliado para sete arquivos, gerado com
  `git diff --binary --full-index` contra o índice post-série padrão. Check
  estrito sem offsets/fuzz e reverse-check confirmaram o delta na cópia.
  Originais de `work/mesa` preservados. Builds Mesa Android/glibc e hardware
  desta revisão NOT EXECUTED; gate 1.3 permanece BLOCKED.
  ID calculado da série nesta revisão, sem alterar lock/profile:
  `sha256:94f2aac28fbbd2e589c838f9ae10bdfbe92c06c97be4f4350f4e3bba2673008c`.

#### Correção dos 12 casos RED em preparação inativa

- **Autorização posterior:** o usuário escolheu explicitamente preparar a
  integração no draft inativo e testes host, sem fechar o gate. Não houve
  seleção de build, aplicação de patch, acesso ao aparelho ou commit.
- **Implementação:** staging local da submissão inteira, fila KCPU lazy,
  contador monotônico UINT32_MAX, fallback CPU diagnosticado antes de aceitação,
  perda da fila após aceitação parcial ou falha posterior. Os slots 3/4 de
  64 bytes do BO CSF_EVENT existente são payload/done.
- **Guarda e conclusão:** cada entrada aguarda done antes de invalidar caches,
  ler payload.error e executar CALL somente no ramo de sucesso; também vale
  para entradas futuras sem waits novos. Não há ERROR_BARRIER nesse caminho.
  Pré-validação e callbacks CPU verificam erro antes do sucesso, inclusive
  com seqno já atingido. Semáforo de outra fila que usou importação conserva
  espera CPU para não perder propagação de erro.
- **RED -> GREEN:** suíte expandida inicialmente executou 30 testes com 21
  falhas comportamentais, incluindo os 12 casos originais. A suíte final tem
  38 métodos de integração; junto a teardown, snapshot, bridge, WAIT_ANY e
  harness nativo, 95 testes passaram.
- **Encoding real:** packer/builder v11 compilados com helpers Mesa;
  seis waits estrangeiros mais guarda em três subfilas: máximo 384 bytes
  normal, 432 com diagnóstico, mantendo limite 512. O teste diagnóstico
  reproduziu overflow antes de remover somente breadcrumbs opcionais
  pre/post-CALL das entradas guardadas; diagnóstico de conclusão permanece.
- **Rulings:** preparação host não equivale a Tarefa 3 GREEN de segurança.
  O ramo de erro não precisa de `cs_else` vazio: ausência de CALL fora do
  `cs_if` preserva o contrato sem instruções extras. O teste real cobre a faixa
  UINT32_MAX exigida para importação e VAs de 48 bits; não qualifica sequências
  arbitrárias de 64 bits do mecanismo anterior de semáforos.
- **Revisão final:** identificou exportação `sync_file` ignorando o callback
  e aceitando apenas seqno de trabalho cujo CALL foi suprimido. Extração do
  exportador real reproduziu três falhas (erro pendente, controle de sucesso
  que deveria esperar e sinal sem targets); o controle não importado passou.
  Sinais de fila com importação omitem endereços GPU, exigindo callback CPU
  antes da exportação mesmo sem targets. Quatro casos GREEN e suíte 95/95.
  O custo deliberado é exportação potencialmente bloqueante nesse caminho;
  exportações normais sem importação permanecem assíncronas.
- **Proveniência:** série calculada
  `sha256:1a05f1c69d3b88e763e55e2248b3a5504a6d2fe980de7f503968985c1e37ac5a`,
  sem alterar lock/perfil. Builds Android/glibc, execução de fence negativa
  real, visibilidade GPU e término firmware NOT EXECUTED/BLOCKED conforme
  gate; fontes originais preservadas.

### Preparação autorizada: harness nativo e produtor controlado

Escopo: preparar código e validar em host; sem aplicar patches, acessar aparelho,
alterar kernel, montar debugfs ou criar dispositivos.

- [x] Testar em RED os casos success/error, refresh CPU após B, DELETE pendente,
  falhas em cada ENQUEUE, DELETE falho, provider ausente, UAPI/page size e timeout.
- [x] Implementar `tests/sync/kcpu_fence_wait_test.c`: CLI
  `<sw_sync-path> <success|error|pending-delete> [--cached]`, uma importação,
  alvo 1, células A/B separadas de 64 bytes, três ENQUEUEs individuais e DELETE
  antes de munmap. Reter mapping/contexto se DELETE falhar.
- [x] Verificar pending/success/negative por `SYNC_IOC_FILE_INFO`. Fechar uma
  timeline própria produz erro em Linux 6.1; comprovar isso em preflight antes
  de abrir Mali no caso error. Provider ausente ou incompatível retorna 77.
- [x] Compilar com warnings como erros, executar mocks e regressões relacionadas;
  documentar comandos futuros e separar publicação KCPU dos gates GPU/PanVK.

Ruling: este primeiro harness não cria grupos nem consumidores GPU. Ele testa
somente publicação KCPU/CPU e drenagem DELETE; não fecha ordem L2/LSC, guard CALL,
propagação PanVK ou terminação CSF. O custo desta fronteira é manter gate 1.3
BLOCKED até preparar e executar o consumidor GPU e a integração.

Resultados desta preparação:

- RED observado: skeleton compilou e falhou em 15 cenários comportamentais.
  Dois casos adicionais observaram RED separado: publicação durante a janela
  pending e rejeição de MEM_SYNC em memória system-coherent.
- GREEN host: `PYTHONPATH=tests python3 -m unittest
  test_kbase_native_fence_wait test_kbase_gpu_fence_wait.GPUFenceImportTests
  test_kbase_gpu_fence_wait.PanVKSyncFileSnapshotTests test_kbase_wait_any -v`:
  42 testes PASS, incluindo 13 métodos/17 cenários do novo harness.
- Compilação `-std=c11 -Wall -Wextra -Werror`: GCC host, Clang host e
  `aarch64-linux-gnu-gcc` PASS. ELF AArch64 tem intérprete glibc
  `/lib/ld-linux-aarch64.so.1`; não é Bionic. Build Bionic NOT EXECUTED.
- `SW_SYNC_IOC_INC` e close de timeline são implementados; testes mockados
  não provam disponibilidade nem comportamento da ROM. O preflight negativo
  precede abertura Mali; ausência/incompatibilidade BLOCKED com exit 77.
- Ruling de cache: seguir flags retornados, não inferir cache pelo pedido.
  `--cached` rejeita downgrade; system-coherent não usa MEM_SYNC, seguindo
  contrato do backend. PASS dessa modalidade não valida LS/L2/LSC GPU.
- Hardware, GPU guard, conclusão PanVK e terminação CSF NOT EXECUTED.
  Sem aplicação de patches, mudanças em fontes originais, commits ou aparelho.
- Revisão final independente, limitada ao novo harness/testes/documentação:
  nenhuma questão significativa encontrada. Whitespace das alterações e dos
  dois arquivos novos PASS. Binários temporários de validação removidos; código
  e comandos de build permanecem no repositório.
- ELF glibc inspecionado requer GLIBC_2.34. Isso não qualifica o chroot alvo;
  ABI/contexto e provider precisam ser verificados antes de execução autorizada.
