# Etapa 4 — Auditoria independente DOCUMENTAL

Data: 2026-11-23. Auditoria técnica independente, sem subagentes.

## 1. Disposição

**PARTIAL DOCUMENTAL.**

A proposta integrada é tecnicamente utilizável para investigação limitada e
preserva as barreiras de autorização. Não foi encontrado defeito documental
**BLOQUEANTE** de segurança, escopo ou afirmação técnica central. Restam duas
imprecisões documentais não críticas e o aceite explícito do contrato proposto
não está estabelecido pelos inputs desta auditoria.

Não emitir `APPROVED` final enquanto essas pendências não forem corrigidas ou
formalmente aceitas, conforme os critérios do plano. `NOT APPROVED` seria
desproporcional: as limitações de runtime estão identificadas, não ocultadas.
Esta disposição não homologa driver, ICD, hardware, kernel, firmware ou glibc.

Resumo priorizado:

1. **MÉDIA, operacional:** o workflow de memória/sync manda interromper em
   qualquer timeout, mas seu fixture exige um `VK_TIMEOUT` deliberado seguido
   de sinalização.
2. **BAIXA, rastreabilidade:** duas remissões E-ID do baseline histórico ainda
   apontam para registros diferentes dos assuntos descritos.
3. **PENDÊNCIA DE PROCESSO:** requisitos continuam propostos; autorização para
   avançar uma etapa ou auditar não é evidência de aprovação do contrato.

## 2. Autoridade, inputs e método

Autoridades examinadas:

- `AGENTS.md`, arquitetura do projeto e plano atual
  `.agents/skills/mali-kernel-platform/plan.md`, inclusive fases 5–8 e critérios
  finais. O plano preexistente do usuário não foi substituído pelo do índice.
- Snapshot bruto `files/etapa2-docs-worktree`, requisitos propostos e patch
  cumulativo exato. A prévia exportada não foi usada como autoridade técnica.
- Relatórios etapas 1/2/3 e os três relatórios separados Etapa 2, usados como
  pistas. Afirmações críticas foram confrontadas com headers, overlays,
  patches, seletores, manifests e procedimentos originais.
- Skills existentes Mesa/Mali e PanVK, incluindo os dois textos integrados.
  A nova skill foi examinada como proposta, não instalada nem ativada.

Identidades confirmadas por leitura/comandos:

| Input | Identidade |
|---|---|
| Projeto | `feat-migration`; HEAD `b64d2fb10e191a8f5666bb509a27b4422df6030f` |
| Mesa limpo | `13baeb70c066a9f82d2bcfb29f06e4865212affa`; `27.0.0-devel`; status porcelain vazio |
| Série de inputs | `sha256:3e20d28a3753e671f6cbfe164372e71b55ecf407dec039f56c05232c53bf2060`; recálculo coincide com lock |
| SHA-256 plano | `a38771aab08193ac101e6e04e3826c98fd6472ea31901e390b1f32ab1788da92` |
| SHA-256 lock | `5f8c59dcdee50a60f6be96dd437b6e5d2d7dcd16ecb4d3709beed7b6a24db987` |
| SHA-256 patch | `8fc86a3cb2511594f778f7791ff36bdcdcc2c80fe74ef535af2af702fe5fb95e` |

O escopo foi G15 como designação do plano, Moto G86/G615 MC2, PAN_ARCH 11,
Android/Bionic e glibc em chroot no mesmo Android. Não foram reabertos F0–F5,
builds antigos, causalidade AHB ou investigação de outras GPUs.

Foi feita uma passagem documental completa pelo conjunto integrado e pelos
dez cenários. As situações dos walkthroughs são entradas simuladas, não
experimentos, logs novos ou autorizações de hardware.

## 3. Escopo do patch e verificação estrutural

**PASS estrutural no modelo de links/locators da proposta:**

- 27 caminhos no patch: 16 arquivos novos da skill, nove caminhos documentais
  e duas skills roteadoras existentes.
- Nenhuma alteração de `plan.md`, `sources.lock`, perfil, código Mesa, política
  ou `work/`; nenhuma deleção, rename ou mudança de modo de arquivo existente.
  Os 16 novos arquivos usam modo `100644`.
- Reconstrução **somente em memória** das pós-imagens de cada hunk a partir
  dos originais: 27/27 coincidem em bytes com o snapshot bruto; zero erros de
  contexto, remoção ou correspondência. Nenhuma pós-imagem foi aplicada/salva.
- Entry point: 97 linhas, frontmatter com nome e descrição, dez referências,
  cinco workflows. Frontmatter das duas integrações também está presente.
- 28 documentos Markdown no snapshot: 220 referências locais; 74 locators
  `arquivo:linha`; 12 referências com âncora. Zero alvos ausentes, linhas fora
  do arquivo, âncoras ausentes ou erros de whitespace/final newline detectados.
- Referências não copiadas ao snapshot foram resolvidas no original. Referências
  copiadas foram resolvidas no snapshot, nunca substituídas silenciosamente
  pelo documento original anterior.

Os sufixos `:linha` foram tratados como **locators**, separando caminho e
linha, como fazem os relatórios anteriores; não como nomes literais de arquivos.
Isso verifica rastreabilidade, não comportamento de clique em todos os
renderizadores Markdown. Não foi executado navegador/editor para certificar
a navegação visual da prévia.

`git apply --check --whitespace=error -v` passou para os 27 caminhos, sem
offset/fuzz e **sem aplicação**. O resultado confirma apenas aplicabilidade
documental ao estado examinado, não replay da série Mesa.

## 4. Confronto técnico das afirmações centrais

Locators nesta seção são relativos ao **repo original**, salvo indicação.
Linhas de `.patch` são linhas do arquivo de patch, não de fonte final aplicada.

| Afirmação da proposta | Fonte confrontada | Resultado documental |
|---|---|---|
| G15 não significa PAN_ARCH 15; glibc é chroot no Android; MC2 não define produto/CSI | `docs/superpowers/specs/2026-11-21-g615-only.md:3`; `profiles/g615-v11-csf.json`; `docs/superpowers/plans/2026-11-22-ahb-app-uid-investigation.md:97–108` | Correta. Identidade Moto é relato/documentação existente, não inventário físico executado agora. Perfil MC6 permanece input, não identidade Moto. |
| Mesa limpo, downstream Kbase e seleção/aplicação/binário são diferentes | `work/mesa/src/panfrost/lib/kmod/meson.build:7–11`; `work/mesa/src/panfrost/compiler/meson.build:37–48`; `scripts/apply-patches.sh:27–33,53–87`; `scripts/compute-patch-series-id.py:54–70`; `scripts/build_provenance.py:26–48` | Correta. Kraid condicionalmente ligado não contradiz a migração concluída como decisão arquitetural. Hash global inclui experimentais, mas não demonstra variante aplicada. |
| CSF 1.21 prevê group 32→112→40, heap 16→24 e ALLOC_EX com fallback restrito | `patches/csf-v11/110-select-kbase-csf-uapi-layouts-and-16k-pages.patch:139–283,450–558`; header consumido `patches/kbase-common/files/include/drm-uapi/mali_kbase_ioctl.h` | Correta como seleção de fonte. Group/heap avançam só em EINVAL/ENOTTY e cacheiam aceite. ALLOC_EX só admite fallback inicial sem caminho aceito; ENOMEM/EPERM/EACCES não autorizam forçar ABI. Guard de fault report é >=1.25, falso para 1.21. |
| USER_IO usa três páginas CPU; BIND cookie não é GPU VA e não é reescalado | patch 110 `:287–301,566–609`; `patches/kbase-common/files/src/panfrost/lib/kmod/kbase_kmod.c:691–758` | Correta. Granule GPU e página CPU são distintos. O overlay inicial de 4 KiB não é confundido com o ajuste posterior. Layout/page efetivamente aceitos no Moto continuam desconhecidos nesta evidência. |
| Um group por subqueue/CSI0; submit/SetEvent não provam conclusão/notificação | `patches/csf/007-gpu-queue-kbase.patch:706–738,1013–1124`; backend `:604–688,761–821`; patches 085 `:22–46` e 111 `:39–94` | Correta. Latch é de dispositivo; heap TERM é separado. A justificativa de “próximo tick” da patch 111 não foi promovida a garantia do firmware Moto. |
| SAME_VA/NEED_MMAP ainda conflados no import examinado | overlay README `:12–17`; backend `:1507–1563,1723–1738`; pesquisa dirigida nos `.patch` de flags/VA | Correta como discrepância estática: `same_va` junta flags e `gpu_va` usa mapping incondicional. Cleanup depende dessa classificação. Nenhum fault/leak físico Moto foi fabricado. |
| FD de memória CLOEXEC; placed precisa backing compartilhado; bo_wait não espera fence; coerência não elimina fences | backend `:1452–1470,1747–1873`; patch 091 `:38–55`; patch 237 `:64–172` | Correta. EXEC/JIT inicializam zonas, não alocam 128 GiB físicos. ION selecionável não equivale a qualificação Moto. Alias/TLS/grow-on-fault não habilitam sparse Vulkan. |
| Default perde waiter em sucesso; dup sync-file não preserva CLOEXEC; poll/deadline/revents e KCPU parcial têm limites | `patches/kbase-common/004-physical-device-kbase.patch:475–493,608–680`; patch 075 `:29–114,334–338`; experimental 004 `:26–35,44–89` | Correta. Poll calcula intervalo uma vez, não rejeita POLLNVAL e pode retornar sucesso sem POLLIN. KCPU espera/sinaliza em enqueues separados; rollback/cancelamento não demonstrados. Lifetime 004 é opt-in e não repara todos os outros pontos. |
| Experimental 002–004 não são promoção/correção global | `scripts/apply-patches.sh:16–18,33,57–62`; experimental 002 `:52–102,179–260`; experimental 003 `:16–139`; README experimental | Correta. 002 stages waits userspace com fallback; não faz rollback KCPU. 003 coalescing não prova visibilidade/ordenação. 001 não é selecionado. |
| Bionic e glibc têm loader/ABI/dependências/contexto/gates próprios | `docs/ARCHITECTURE.md:3–24`; `scripts/build-android.sh:20–55`; `scripts/build-glibc.sh:86–116`; loader de teste `:28–100`; histórico glibc `validation/g615-v11-csf/beta3-phase8-glibc-runtime-2026-09-19.txt:1–10` | Correta. Nome de wrapper não prova glibc; JSON resolve no guest. Android PASS não certifica glibc, headless não certifica WSI, hash ZIP não identifica necessariamente ICD carregado. |
| Históricos a273/a06b e c453/7d02 não qualificam 3e20 | investigação AHB `:134–147,168–193`; `validation/mesa27-large-draw-initializer-fix.json:3–12,74–80`; `tests/README.md:250–264` | Correta. Manifest initializer exclui AHB/apresentação/full CTS; native release tem outro par de binários. Associação raw-manifest de a273 permanece incompleta. |
| AHB externo app UID é FAIL histórico adiado; firmware/kernel internos desconhecidos não bloqueiam drafting | investigação AHB `:117–166`; requisitos snapshot `:30–35,48–61`; referências firmware/security | Correta e operacionalmente segura. A causa conhecida foi apenas confrontada documentalmente, não reinvestigada. Não há bypass, cookie em buffer externo ou autorização presumida. |

## 5. Findings e correções mínimas

### D4-01 — Timeout deliberado versus interrupção incondicional

- **Severidade:** MÉDIA, não bloqueante para uso documental limitado.
- **Arquivo:linha no snapshot:** `.agents/skills/mali-kernel-platform/workflows/memory-sync-audit.md:40–43,52–54`.
- **Evidência:** PASS requer FD pending antes/depois do timeout e conclusão
  após sinalização, mas a condição de parada diz simplesmente “timeout”.
  Fonte original `tests/README.md:222–229` especifica o `VK_TIMEOUT` inicial;
  `tests/sync/sync_file_test.c:250–254` exige esse resultado e só depois sinaliza.
- **Efeito:** leitura literal pode encerrar/classificar FAIL um estágio esperado
  ou tornar contraditória a instrução “no retries” com a reespera intencional.
  Não cria autorização insegura nem novo falso PASS, mas reduz determinismo.
- **Correção mínima:** dizer “timeout inesperado ou do prazo total”; explicitar
  que o `VK_TIMEOUT` inicial previsto no fixture e sua reespera serial fazem
  parte do caso, sem autorizar retry após falha real, timeout externo ou hang.
- **Hipótese delimitada:** a intenção provavelmente era interromper apenas
  timeouts inesperados. Essa interpretação não está escrita na regra de parada.

### D4-02 — Remissões históricas E-ID parcialmente incorretas

- **Severidade:** BAIXA, não bloqueante; não invalida o achado central atual.
- **Arquivo:linha no snapshot:** `docs/engineering/mali-kernel-platform/TECHNICAL_BASELINE.md:106–112`.
- **Evidência:** trecho placed-map remete a E-007/E-013, mas o registro principal
  de placed-map é E-006; E-007 descreve async submission. O trecho async remete
  a E-008/E-013, mas E-008 descreve snapshot modificado e o registro principal
  de async é E-007. Conferido em `EVIDENCE_REGISTER.md:22–24,29`.
- **Efeito:** um leitor que siga os IDs encontra outro assunto antes da fonte
  relevante. E-013 ainda fornece os dois worklogs, portanto não é ausência
  total de rastreabilidade nem confusão de evidência runtime atual.
- **Correção mínima:** anotação de reconciliação preservando o histórico:
  placed-map → E-006/E-013; async → E-007/E-013. Não renumerar/apagar IDs
  ou substituir a auditoria histórica.
- **Origem:** remissões herdadas, ainda presentes no documento integrado.
  A correção dos registros/matriz não corrigiu essas duas remissões narrativas.

### P4-01 — Aprovação explícita do contrato não estabelecida

- **Classificação:** PENDÊNCIA DE PROCESSO, não defeito técnico bloqueante,
  não achado de violação de autorização nesta execução.
- **Locators:** plano original `plan.md:537–538` (entregável fase 5) e
  `:808–809` (M4); snapshot `SKILL_REQUIREMENTS.md:3–13,34–35`;
  novo `SKILL.md:8–9,29–34`.
- **Evidência:** plano pede requisitos aprovados antes do conteúdo final;
  proposta declara expressamente que geração não aprova o contrato nem instala
  a skill. Não há aceite explícito do contrato nos inputs auditados.
- **Efeito:** draft e auditoria podem ser avaliados, mas não tratados como
  conclusão/instalação/contrato aprovado.
- **Resolução mínima:** registrar a decisão explícita sobre o contrato ou
  manter status de proposta e pendência. A expressão “próxima etapa” não foi
  convertida em aprovação. Não foi inventada exigência de nova autorização
  para esta auditoria já solicitada.

**Nenhuma correção foi efetuada.** Findings não autorizam aplicação, edição de
snapshot, perfil, política ou código.

## 6. Dez walkthroughs documentais determinísticos

Legenda: `S` = `.agents/skills/mali-kernel-platform/` no snapshot;
`C` = `docs/engineering/mali-kernel-platform/` no snapshot.
Gates descritos nas entradas simuladas **não são resultados físicos desta
auditoria**. Todos partem de leitura de `S/SKILL.md` e discovery.

| # / entrada e situação | Navegação documental | Decisão/gate esperado | Decisão instruída e fonte confrontada | Resultado do walkthrough |
|---|---|---|---|---|
| 1. Identidade: usuário informa Moto G86 MC2/G15; perfil disponível diz Poco MC6 e kernel/permissões próprios | `SKILL:11–25,35–38` → `platform-discovery:27–37` → `architecture:29–34` → `C/E-016,E-017` | Separar G15/PAN_ARCH11 e identidade histórica Moto; não copiar máscara/nó/firmware MC6. Coleta atual incompleta pode ser BLOCKED, sem impedir drafting | Instruído registrar desconhecidos/tupla, confirmar antes de execução e não modificar perfil. Fontes: spec G615 `:3`, perfil original, manifest initializer `:8–12`, investigação Moto `:97–108` | **PASS DOCUMENTAL**; identidade física atual não coletada |
| 2. UAPI/layout: CSF 1.21 relatada; group 32 rejeitado EINVAL; depois 112 aceito; não há kernel source Moto | `kbase-uapi-abi:12–28,32–44` → `uapi-audit:13–40` | Predizer 32→112→40 e heap16→24; cache de aceite; reportar layout observado somente se log real identificado. Kernel handler UNKNOWN | Instruído conferir request completo/guard/errno, não forçar fallback por ENOMEM/EPERM/EACCES nem inferir firmware. Fonte: 110 `:139–283,524–558`, header consumido | **PASS DOCUMENTAL**; simulação não é captura Moto |
| 3. Falha alloc: primeiro MEM_ALLOC_EX retorna ENOMEM, sem caminho previamente aceito | `gpu-memory:5–9` → `memory-sync-audit:14–29,47–54` → `uapi-audit:19–29` → `C:53–67` | Preservar errno e etapa, não tratar recurso como recusa ABI; FAIL do caso hipotético, sem fallback forçado ou flags arbitrárias | Instruído seguir alloc→flags/VA→mmap→cleanup, parar no primeiro erro e propor host/mock antes de fix. Fonte: 110 `:450–505`; overlay alloc `:1594–1707` | **PASS DOCUMENTAL**; causa kernel além do errno continua UNKNOWN |
| 4. DMA-BUF: FD válido; outflag NEED_MMAP sem SAME_VA; mmap CPU bem-sucedido | `gpu-memory:11–29` → `memory-sync-audit:14–22` → `dma-buf-sync:5–13` | FAIL estático da classificação examinada; VA retornado não pode ser substituído por CPU VA só por NEED_MMAP. Fences/cache e cleanup independentes | Instruído não chamar “011” aplicada, não alternar flags, não concluir leak/fault Moto; coletar ownership e propor patch posterior. Fontes README `:12–17`, backend `:1507–1563,1723–1738,1833–1873` | **PASS DOCUMENTAL**; nenhum import físico executado |
| 5. sync_file/lifetime: pressuposto futuro fixture aprovado, glibc/CSF1.21/4KiB, variante identificada; FD inicialmente pending e VK_TIMEOUT previsto, seguido de signal | `dma-buf-sync:19–41` → `memory-sync-audit:23–43,52–54` → fixture original | Conservar waiter no timeout esperado, completar 12 ciclos sem FD growth; 77=BLOCKED, outros não-zero=FAIL; diferenciar variante default/004 e não prometer corner cases | Instruído exige pending após timeout/completion, mas também “stop … timeout” sem exceção. Fonte `tests/README:222–229`, fixture `:250–254`, experimental004 `:26–35,44–89` | **PARTIAL DOCUMENTAL — D4-01**. Aqui hardware é NOT EXECUTED; autorização futura é apenas premissa simulada |
| 6. Falha CSF: submit retorna sucesso, wrapper loga KICK error ou surge group fatal; SetEvent retorna VK_SUCCESS | `csf-jm:23–40` → `csf-audit:18–40` | Primeiro erro preservado, não inferir completion/recovery; parar submissões, não criar segundo reader nem TERM/reset manual | Instruído separar publicação/notificação/completion/cleanup, latch de erro não é recovery. Fontes backend `:604–688,761–821`, queue007 `:706–738`, 085/111 | **PASS DOCUMENTAL**; fault é input hipotético, não ocorrido aqui |
| 7. Android/glibc: Android sync histórico PASS; guest chamado Alpine, libc/JSON/acesso desconhecidos | `android:16–42` → `linux-glibc:5–38` → `device-validation:17–31` | Não herdar PASS Android; guest/loader/ABI/acesso precisam identificação; runtime glibc BLOCKED até prerequisites, não UNSUPPORTED por ausência de evidência | Instruído JSON no guest, ICD glibc próprio, sem mount/root/socket bypass automático. Fontes arquitetura `:17–24`, build-glibc `:86–116`, histórico MC6 `:1–10` | **PASS DOCUMENTAL**; nenhuma qualificação glibc/Moto criada |
| 8. Evidência insuficiente: apenas manifest c453/7d02, relato a273/a06b, série atual3e20 e firmware/kernel ausentes | `validation:7–29,42–51` → `C:183–196,223–248` → `firmware-power:11–18,35–38` | HISTORICAL_REPORT para execuções antigas; fonte estática ≠ execução; atual NOT EXECUTED/BLOCKED por identidade ausente, firmware UNKNOWN. Ausência de kernel/fullCTS não bloqueia homologação documental limitada | Instruído manter quatro identidades e dimensões separadas, sem inventar manifest/teste ou handler. Fontes dois registros históricos originais e scripts de hash/proveniência | **PASS DOCUMENTAL**; limites não viram novos PASS |
| 9. Preparar patch: fix documental/source proposto; usuário não autorizou aplicar e originals têm mudanças | `SKILL:29–34,58–59` → `validation:60–65` → PanVK authority/AGENTS | Preparar diff revisável na cópia, check sem aplicação, rejeitar drift; preservar originals; aplicação/commit/profile/contract não autorizados | Instruído `git diff --binary --full-index`, `git apply --check --whitespace=error -v`, nenhuma aplicação automática. Fonte AGENTS patch-only/approval e plano§8 | **PASS DOCUMENTAL**; check documental executado nesta auditoria não aplicou nada |
| 10. Recusar MC6→MC2: solicitante tenta usar CTS/Poco, `glibc:pass` e coreMask MC6 para certificar Moto | `SKILL:35–38` → `architecture:29–31` → `linux-glibc:31–38` → `C/COMPATIBILITY_MATRIX` | Recusar promoção/generalização, preservar histórico e perfil; exigir evidência do caso/tupla, sem ampliar GPUs | Instruído não chamar Moto suportado por resultado MC6, não certificar CSF via JM/Panthor nem WSI por headless. Fontes perfil original e histórico glibc MC6 | **PASS DOCUMENTAL**; recusa não implica nova investigação |

Total: **9 PASS DOCUMENTAIS, 1 PARTIAL DOCUMENTAL**. Nenhum cenário foi executado
em dispositivo, nenhuma entrada simulada foi convertida em resultado runtime.

## 7. Homologação — critérios do plano

### Critérios obrigatórios da fase 8

| Critério | Avaliação | Justificativa |
|---|---|---|
| Escopo | PASS DOCUMENTAL | G15/Moto MC2/PAN_ARCH11 e Android/glibc chroot explícitos. JM/Panthor/MC6 permanecem fronteiras/histórico; roteadores verificam disponibilidade/escopo. |
| Baseline | PASS DOCUMENTAL | Pin Mesa27, limpeza e série confirmados; pós-imagens documentais não confundidas com Mesa aplicado. |
| Arquitetura | PASS DOCUMENTAL | Kraid como decisão concluída; ligação condicional/static versus configuração/binário separadas. Não exigida reabertura do compilador. |
| Preservação | PASS no escopo auditado | Patch não toca plano/lock/work; histórico, IDs e audit anterior preservados. Verificação ampla de empacotamento/preservação pertence ao executor, não certificada por este parecer. |
| Rastreabilidade | PARTIAL, não crítica | Fontes técnicas centrais corretas e 220 referências verificadas; duas remissões narrativas herdadas precisam anotação D4-02. |
| Precisão | PASS DOCUMENTAL | Classes/tuplas/gates separados; sem promover hipóteses, enums, builds, assertions ou relatos a funcionamento físico atual. |
| Cobertura | PASS DOCUMENTAL limitada | Dez referências e cinco workflows cobrem domínios requeridos; lacunas críticas para runtime classificadas. Não se exige firmware/kernel source/fullCTS para documental. |
| Segurança | PASS DOCUMENTAL | Autorização explícita, originals read-only, sem raw ioctls improvisados, bypass, reset automático, broad kill, mounts/install/cleanup presumidos. Timeout deve alcançar processo real; processo/contexto isolados. |
| Operação | PARTIAL, não crítica | Pré-condições, navegação, passos/fontes, gates, entregas e stops presentes. D4-01 deixa timeout esperado ambíguo em um caso. |
| Integração | PASS DOCUMENTAL | Central mantém coordenação; PanVK mantém contratos Vulkan; compiler/build não duplicados. Handoff limitado e disponibilidade verificada; textos gerais preexistentes não ampliam o escopo novo. |

### Checklist final do plano

| Item | Estado nesta proposta/auditoria |
|---|---|
| Mesa27 limpo identificado | PASS |
| Kraid descrito como concluído arquiteturalmente | PASS |
| Escopo correto refletido | PASS |
| Artefatos anteriores/ausências registrados | PASS documental; não certificação de backup integral |
| MC6/outros claramente separados | PASS |
| Perfil técnico Moto com limites explícitos | PASS documental histórico; inventário físico atual não executado |
| Fases anteriores sem reconstrução fictícia | PASS; índice canônico UNKNOWN preservado |
| Lacunas críticas resolvidas ou classificadas | PASS para drafting; não resolvidas tecnicamente por esta auditoria |
| SKILL.md gerado | PASS no snapshot/patch; não instalado |
| Referências geradas | PASS, dez |
| Workflows gerados | PASS estrutura, cinco; operação PARTIAL por D4-01 |
| Integração definida | PASS, duas skills |
| Verificação estrutural e técnica concluída | Executada; disposition PARTIAL e findings acima |
| Auditoria aprovada ou pendências formalmente aceitas | PENDENTE; este parecer não presume aceite |
| Nenhuma validação física inexistente declarada concluída | PASS |
| Requisitos aprovados antes do conteúdo final — fase5/M4 | PENDENTE P4-01; os arquivos continuam proposta, não conteúdo definitivo aprovado |

## 8. Limites técnicos que NÃO são defeitos bloqueantes documentais

- SAME_VA/NEED_MMAP, default waiter, CLOEXEC, deadline/revents e enqueue parcial
  são discrepâncias/limites de implementação explícitos. Sua correção pertence
  a tarefa separada autorizada; não é pré-condição inventada para esta auditoria.
- Runtime Moto da série3e20, glibc real/acesso/loader/WSI, layout aceito, página
  efetiva/GLB, kernel/DDK/firmware exatos e cancelamento/lifetime internos
  continuam UNKNOWN ou sem qualificação correspondente.
- Falha externa-AHB app UID permanece FAIL histórico adiado; não virou nova
  causa a investigar nem bloqueio de geração/homologação documental limitada.
- 16KiB, full CTS, estabilidade geral, performance comparativa, DVFS,
  suspend/resume e recovery não foram executados/qualificados nesta tarefa.
- Históricos a273/a06b, c453/7d02 e native release 3e79/d30b continuam separados.
  Não foi recuperado manifest bruto ausente nem auditado o arquivo de evidência
  initializer. Não foi extrapolada a pesquisa negativa de glibc a ausência global.
- Não há hipótese de causa nova no kernel. A única interpretação não explícita
  relevante é a intenção de “timeout” em D4-01; falta a exceção documental.
- O plan2.md concurrente não fornece especificação, autorização nem evidência.

## 9. Comandos e resultados efetivamente executados

Todos os programas externos chamados via Bash foram prefixados por `rtk`
ou `rtk bypass`. Comandos abaixo são verificações da auditoria, não exemplos
de hardware executados.

| Comando/operação | Resultado observado |
|---|---|
| `rtk git status --short`; `rtk git branch --show-current`; `rtk git rev-parse HEAD`; `rtk git diff -- .agents/skills/mali-kernel-platform/plan.md` | Branch/HEAD acima; diff preexistente do plano identificado. Status inicial só plano; status posterior também plan2 concurrente, preservado. |
| `rtk sha256sum .agents/skills/mali-kernel-platform/plan.md sources.lock /home/vagners/.copilot/session-state/2faebd54-c930-403f-8595-23919c5700e5/files/etapa3-skill-cumulativa.patch` | Exit0; três hashes acima, confirmados novamente no fechamento. |
| `rtk git -C work/mesa rev-parse HEAD`; `rtk git -C work/mesa status --porcelain=v1 --untracked-files=all` | Exit0; pin correto, status vazio. |
| `rtk bypass python3 scripts/compute-patch-series-id.py --profile g615-v11-csf` | Exit0; série3e20 completa coincide com lock. Script somente leitura, sem atualização de lock. |
| `rtk git apply --stat <patch>` | Exit0; 27 files, 1223 insertions, 26 deletions; caminhos documentais previstos. Não aplicação. |
| `rtk bypass python3 - <<'PY' … PY` — parser em memória de diff/pós-imagens e Markdown | Exit0; 27 pós-imagens exatas, zero errors; 28 docs/220 refs/74 locators/12 anchors; missing/badanchors/badlines/whitespace vazios; entry97/skill16. Nenhum arquivo criado pelo parser. |
| `rtk bypass git apply --check --whitespace=error -v <patch>` | Exit0; 27 “Checking patch”, sem offsets/fuzz, nenhum apply. |
| `rtk git diff --check`; `rtk git -C work/mesa diff --check` | Exit0, sem mensagens; apenas whitespace dos diffs existentes, não aprovação semântica do plano. |
| `rtk bypass sed`, `cat`, `python3` para leituras numeradas; `functions.rg` com glob `*.patch` e `sync_file_test.c` | Fontes/seletores confrontados na seção4; fixture confirma VK_TIMEOUT esperado e return77. Leituras agrupadas grandes foram completadas em partes menores quando o output foi truncado. |
| `functions.view` no plano grande | Recusado por limite do hook; leitura substituída com `rtk bypass sed`, sem alteração de arquivo. |

Gates desta execução:

| Dimensão | Estado |
|---|---|
| Proveniência dos inputs e estrutura/locators | PASS |
| Coerência/rastreabilidade documental operacional | PARTIAL — D4-01/D4-02 |
| Aprovação formal do contrato/conclusão definitiva | PENDENTE, não presumida |
| Auditoria independente documental | Executada — PARTIAL DOCUMENTAL |
| Instalação/aplicação do patch | NOT EXECUTED |
| Replay Mesa/build/assertions ABI/software tests | NOT EXECUTED |
| ADB/transfer/install/mount/hardware/firmware/power/stability/performance | NOT EXECUTED |

Não houve download, commit, alteração de perfil/política, teste físico, aplicação
ou correção. A única entrega escrita intencionalmente por este auditor é este
relatório. Snapshot e patch não foram editados.

## 10. Integridade concorrente e encerramento

Durante a auditoria, o usuário informou novo untracked
`.agents/skills/mali-kernel-platform/plan2.md` no original. O status confirmou
sua presença; **não foi lido, usado como especificação, modificado ou removido**.
Não é atribuído à auditoria nem contabilizado como defeito da skill.
Plano, lock e patch mantiveram os hashes fornecidos; Mesa permaneceu limpo.

A auditoria termina aqui: conjunto integrado e dez cenários examinados uma vez.
Não se recomenda nova investigação kernel, fullCTS, firmware ou causa AHB para
resolver estas pendências documentais. O próximo ato possível é a decisão sobre
os findings/contrato pelo responsável; este parecer não autoriza correções,
aplicação ou homologação física.
