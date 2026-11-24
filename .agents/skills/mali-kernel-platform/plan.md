# Plano de geração da skill `mali-kernel-platform`

**Status:** Plano de execução\
**Projeto:** Mesa / Kraid\
**Skill-alvo:** `.agents/skills/mali-kernel-platform/`\
**Referência técnica:** Mesa `27.0.0-devel` limpo\
**Dispositivo-base:** Motorola Moto G86 --- Mali-G615 MC2\
**Plataformas-alvo:** Android e Linux glibc

---

## 1. Objetivo

Gerar uma skill especializada em kernel e plataforma Mali, capaz de
orientar investigação, diagnóstico, manutenção e validação da integração
GPU no projeto Mesa/Kraid.

A skill deve transformar em instruções operacionais o conhecimento
técnico já levantado, preservar as evidências existentes, completar
apenas as lacunas relevantes e definir procedimentos reproduzíveis para
trabalhos futuros.

O trabalho não deve reiniciar as investigações concluídas nem descartar
documentos, patches, worklogs, perfis ou resultados anteriores.

## 2. Decisões e escopo congelado

As decisões abaixo são a referência deste plano:

---

Item Definição

---

Arquitetura do projeto Migração para Kraid considerada
concluída

Mesa de referência `27.0.0-devel` limpo, após o reset
da base

GPU-alvo Mali G15

Dispositivo físico-base Moto G86

GPU do dispositivo Mali-G615 MC2

SoC MediaTek MT6878

Android Android 16, conforme perfil
conhecido; confirmar no inventário
atual

Linux glibc

Validação física Exclusivamente no Moto G86
disponível para testes

Outras GPUs Fora do escopo de suporte e
validação

Fonte do kernel Não disponível no projeto; não
tratar sua ausência como bloqueio

Alterações Preparar patches revisáveis;
aplicar somente com autorização
explícita

Testes físicos Executar somente com autorização
explícita

---

A Mali-G615 MC6 do Poco X6 Pro e outros dispositivos podem permanecer
como fontes históricas de evidência. Esses resultados não comprovam
comportamento, compatibilidade ou funcionamento na G615 MC2 do Moto G86.

A skill não deve declarar suporte universal à família Mali. Seu escopo
deve permanecer limitado à G15, ao Moto G86 como plataforma física de
referência e aos ambientes Android e Linux glibc.

## 3. Princípios obrigatórios

1.  **Preservação:** não apagar, substituir ou reconstruir documentos e
    evidências existentes sem necessidade demonstrada.
2.  **Baseline limpa:** usar o Mesa `27.0.0-devel` limpo como referência
    de construção da skill.
3.  **Separação de camadas:** distinguir o Mesa de referência, a
    integração Kraid e os componentes específicos da plataforma.
4.  **Rastreabilidade:** cada afirmação técnica importante deve apontar
    para fonte, arquivo, patch, worklog, log ou experimento.
5.  **Classificação de evidência:** não confundir análise estática,
    relato histórico, build, teste automatizado e validação física.
6.  **Escopo restrito:** não ampliar a matriz para outras GPUs ou
    plataformas sem decisão explícita.
7.  **Sem suposições sobre kernel:** usar userspace, UAPI, headers,
    documentação pública, logs e experimentos observáveis. Marcar como
    desconhecido o que não puder ser comprovado.
8.  **Não destrutivo:** não executar operações destrutivas sobre a
    árvore de trabalho ou artefatos preservados.
9.  **Patches revisáveis:** mudanças de código ou documentação devem ser
    apresentadas como patches revisáveis.
10. **Autorização:** não aplicar patches, executar testes de hardware ou
    criar commits sem autorização explícita.
11. **Sem alegações não comprovadas:** não declarar estabilidade,
    desempenho ou compatibilidade sem evidência correspondente.
12. **Sem duplicação:** integrar-se às skills centrais e especializadas
    existentes, sem replicar seu conteúdo.

## 4. Estado de conhecimento já levantado

O trabalho anterior produziu investigações e materiais que devem ser
reaproveitados. A lista abaixo é um resumo do conhecimento conhecido,
não substitui a conferência dos arquivos atuais após o reset.

### 4.1 Arquitetura e backend

Já foram investigados:

- Fronteiras entre Mesa userspace, backend Kbase/Panthor e interfaces
  do kernel.
- Organização do backend em `work/mesa/src/panfrost/lib/kmod/`.
- Fluxos de descoberta e inicialização de dispositivo.
- Diferenças entre Kbase e Panthor.
- Consultas de propriedades e capacidades.
- Gestão de FDs e recursos.
- Diferenças entre CSF e JM.
- Relação entre frontend Vulkan, backend de dispositivo e UAPI.

A skill deve preservar a distinção entre o código userspace do Mesa e a
implementação do kernel. A existência de código em `lib/kmod` não
significa que o código-fonte do kernel esteja presente.

### 4.2 Kbase e UAPI/ABI

Já foram analisados:

- Inventário de IOCTLs utilizados.
- Declarações de UAPI e estruturas.
- Layouts históricos e seleção por versão.
- Handshake e descoberta do dispositivo.
- Direção, tamanho e número de IOCTLs.
- Tratamento de erros e fallbacks.
- Ciclo de vida dos FDs.
- Permissões e identidade do dispositivo.
- Diferenças entre versões de UAPI.
- Compatibilidade estrutural em compiladores AArch64 e ARMv7.

Foram registrados layouts de estruturas Kbase, incluindo variantes de
criação de queue group, inicialização de tiler heap e alocação de
memória. Os resultados de compilação/assertions demonstram propriedades
estruturais dos headers testados; não provam, por si só, compatibilidade
com handlers de kernel.

A skill deve exigir confirmação da UAPI efetiva do Moto G86 antes de
transportar conclusões de outro dispositivo.

### 4.3 CSF e JM

Já foram levantados:

- Consulta de interface CSF.
- Capacidades e propriedades de CSF.
- Ciclo de vida de queue groups e filas.
- Ring buffers, bind, mmap, kick e terminate.
- Notificações e leitura de eventos.
- Operações KCPU e CQS64.
- Diferenças entre ring buffer gerenciado por userspace e por kernel.
- Estruturas de atom JM e extensões específicas de fornecedor.
- Regras de fallback e rejeição por versão.

A skill deve determinar a aplicabilidade real de CSF/JM ao Moto G86. Não
deve assumir que ambos são caminhos ativos no dispositivo.

### 4.4 Memória GPU

Já foram investigados:

- BOs e gerenciamento de VA.
- Alocação e importação de memória.
- `MEM_ALIAS`, extents e `SAME_VA`.
- `NEED_MMAP` e mapeamentos CPU/GPU.
- Importação DMA-BUF.
- MEM_ALLOC e MEM_ALLOC_EX.
- JIT e inicialização de memória.
- Cache operations e sincronização.
- Diferenças de comportamento entre Kbase e Panthor.

Um achado anterior identificou possível conflation entre
`BASE_MEM_SAME_VA` e `BASE_MEM_NEED_MMAP` na interpretação de flags e
GPU VA. A correção correspondente não deve ser presumida como aplicada:
verificar o estado atual do baseline e dos patches antes de qualquer
ação.

### 4.5 DMA-BUF e sincronização

Já foram analisados:

- Importação e exportação de DMA-BUF.
- Coerência de cache.
- `DMA_BUF_IOCTL_SYNC`.
- Reconciliação de sync_file.
- Fences e sincronização externa.
- Waiters e ciclo de vida de FDs.
- KCPU CQS64.
- Timeouts, EINTR e eventos de poll.
- Falhas parciais de enfileiramento.
- Compartilhamento entre processos.

Foram identificados riscos potenciais em lifetime de waiters, duplicação
de FDs sem `CLOEXEC`, conversão de timeout, tratamento de eventos de
`poll` e falha parcial de operações KCPU. Patches experimentais
existentes devem ser tratados como evidência e material de revisão, não
como correções automaticamente homologadas.

DMA-BUF coherency e espera de fences `sync_file` são assuntos distintos
e devem permanecer separados na documentação e nos testes.

### 4.6 Android e WSI

Já foram investigados:

- Android Hardware Buffer.
- Importação de AHardwareBuffer.
- Caminhos de swapchain.
- `ANativeWindow_lock`.
- `AHardwareBuffer_lock` e unlock.
- Mapper e dependências de namespace/SELinux.
- Sincronização de memória em caminhos de WSI.
- Limitações de validações anteriores em dispositivos diferentes.

Resultados de WSI obtidos em outros dispositivos devem permanecer
identificados como evidência histórica e não podem ser atribuídos ao
Moto G86.

### 4.7 Sparse e recursos avançados

A pesquisa de sparse Kbase identificou lacunas entre os requisitos
Vulkan/PanVK e a UAPI Kbase analisada. A decisão documentada
anteriormente foi não habilitar sparse no caminho Kbase sem
implementação e validação suficientes.

A skill deve preservar essa decisão como referência histórica,
reavaliando-a somente se houver mudança técnica ou autorização
explícita. Não deve apresentar protótipos ou estudos de viabilidade como
suporte implementado.

### 4.8 Evidências e limitações históricas

Há worklogs, perfis, probes, patches e relatórios que registram builds e
testes em dispositivos diferentes. Alguns resultados incluem testes JM
em G57 e evidências da G615 MC6.

Esses materiais devem ser preservados com identificação de dispositivo,
versão, commit, patch set e condições do teste. Não devem ser promovidos
a validação do Moto G86.

Não foram comprovados, de forma geral, os seguintes itens:

- Compatibilidade integral de todos os caminhos CSF no Moto G86.
- Validação de hardware em página de 16 KiB.
- Cobertura completa de WSI Android no Moto G86.
- Todos os cenários de sincronização interprocessos.
- Comportamento interno do firmware.
- Implementação interna do kernel do dispositivo.
- Validação física de Linux glibc no Moto G86.

## 5. Artefatos existentes a preservar

A consolidação documental já criada deve ser mantida:

```text
docs/engineering/mali-kernel-platform/
├── TECHNICAL_BASELINE.md
├── EVIDENCE_REGISTER.md
├── FINDINGS_REGISTER.md
├── COMPATIBILITY_MATRIX.md
├── RISK_REGISTER.md
├── INVESTIGATION_BACKLOG.md
├── SKILL_REQUIREMENTS.md
├── CONSOLIDATION_AUTOCHECK.md
└── audit/
    └── CONSOLIDATION_AUDIT.md
```

Também devem ser preservados, quando presentes:

- `AGENTS.md`.
- `.agents/skills/mesa3d-mali-expert/`.
- `.agents/skills/kraid-compiler/`.
- `.agents/skills/panfrost-panvk/`.
- `.agents/skills/panvk-build-validation/`.
- `docs/KBASE-PROFILES.md`.
- `docs/KBASE-SPARSE-FEASIBILITY.md`.
- `worklogs/`.
- `patches/`.
- `validation/`.
- Perfis e probes do dispositivo.
- Registros de proveniência e `sources.lock`.

O inventário após o reset deve confirmar quais arquivos permanecem
presentes e se seus conteúdos correspondem ao material anteriormente
analisado. Não assumir que todo arquivo listado anteriormente ainda
existe ou está inalterado.

## 6. Plano de execução

### Fase 0 --- Baseline limpa e preservação

**Objetivo:** identificar a referência correta e proteger o trabalho
anterior.

Atividades:

1.  Registrar o commit exato do Mesa `27.0.0-devel` limpo após o reset.
2.  Registrar branch, versão, origem e proveniência.
3.  Confirmar a presença da integração Kraid na referência usada pelo
    projeto, sem confundir baseline original com árvore de migração.
4.  Inventariar os documentos e diretórios de evidência existentes.
5.  Verificar o estado Git sem modificar arquivos.
6.  Identificar diferenças entre o inventário atual e o inventário
    histórico.
7.  Registrar artefatos ausentes ou não recuperáveis, sem reconstruir
    conteúdo por suposição.

**Entregáveis:**

- Registro do baseline.
- Inventário dos artefatos preservados.
- Mapa de proveniência e estado Git.
- Lista de divergências após o reset.

**Critério de saída:** referência limpa identificada e material anterior
preservado ou suas ausências explicitamente registradas.

### Fase 1 --- Reconciliar a consolidação existente

**Objetivo:** tornar os documentos atuais coerentes com o escopo
aprovado.

Atividades:

1.  Ler os documentos de consolidação existentes.
2.  Preservar IDs, referências e histórico.
3.  Corrigir o dispositivo-base para Moto G86 / Mali-G615 MC2.
4.  Separar evidências da MC6 e de outros dispositivos.
5.  Atualizar o escopo para Kraid, G15, Android e Linux glibc.
6.  Distinguir Mesa limpo, integração Kraid e particularidades do
    dispositivo.
7.  Classificar cada evidência por força e ambiente.
8.  Resolver contradições documentais sem apagar o histórico.
9.  Atualizar o autocheck e registrar as decisões.

**Entregáveis:**

- Documentos de consolidação reconciliados.
- Registro de decisões e divergências.
- Matriz de evidências por dispositivo e plataforma.

**Critério de saída:** documentos coerentes entre si e sem atribuição
indevida de evidências de outros dispositivos ao Moto G86.

### Fase 2 --- Recuperar o mapa de fases e auditar a cobertura

**Objetivo:** determinar o que foi investigado, o que foi concluído e o
que ainda falta, sem inventar o histórico F0--F5.

Atividades:

1.  Procurar definições originais, critérios de entrada/saída e
    entregáveis de F0--F5.
2.  Se os artefatos originais não forem encontrados, registrar a
    limitação.
3.  Criar uma matriz de cobertura baseada nos domínios técnicos
    comprovadamente investigados.
4.  Separar fases históricas de etapas propostas neste plano.
5.  Reaproveitar análises anteriores quando sua fonte e escopo forem
    rastreáveis.
6.  Identificar lacunas técnicas relevantes ao Moto G86.
7.  Classificar cada lacuna por impacto, dependência e possibilidade de
    validação.

**Entregáveis:**

- Mapa de cobertura técnico.
- Registro de fases históricas recuperadas ou não recuperadas.
- Backlog priorizado de lacunas.
- Critérios de conclusão por domínio.

**Critério de saída:** nenhuma fase ou resultado é apresentado como
histórico sem evidência; as lacunas restantes estão identificadas.

### Fase 3 --- Perfil técnico do Moto G86

**Objetivo:** construir uma referência verificável do dispositivo-base.

Atividades:

1.  Confirmar modelo, SoC, GPU, revisão/identificação reportada e
    sistema.
2.  Registrar propriedades observáveis da GPU.
3.  Identificar node, permissões e condições de acesso.
4.  Obter a versão UAPI efetivamente reportada pelo userspace/kernel
    interface, quando disponível.
5.  Identificar CSF ou JM a partir de evidência observável.
6.  Registrar propriedades de memória, coerência, filas e sincronização
    quando consultáveis.
7.  Registrar versão de driver/firmware somente quando a fonte for
    confiável.
8.  Separar informações reportadas pelo sistema de inferências.
9.  Registrar comandos, ferramentas, data e resultados usados para
    produzir o perfil.

**Entregáveis:**

- Perfil técnico do Moto G86.
- Inventário de capacidades observadas.
- Lista de propriedades desconhecidas.
- Procedimento reproduzível de coleta.

**Critério de saída:** o perfil diferencia dados observados, dados
inferidos e dados desconhecidos.

**Restrição:** não executar testes físicos sem autorização explícita.

### Fase 4 --- Completar as lacunas técnicas prioritárias

**Objetivo:** concluir somente as investigações ainda necessárias ao
escopo aprovado.

#### 4.1 Kbase, UAPI e ABI

- Confirmar as interfaces usadas no Moto G86.
- Verificar versões, estruturas e IOCTLs relevantes.
- Revisar layouts e fallbacks com base na UAPI efetiva.
- Documentar limites de compatibilidade.
- Distinguir validação estrutural de compatibilidade real com kernel.

#### 4.2 CSF e execução

- Confirmar recursos CSF observáveis.
- Revisar queue groups, filas e ring buffers.
- Revisar notificações e ciclo de vida.
- Identificar tratamento de falhas e encerramento.
- Investigar JM somente se houver evidência de aplicabilidade.

#### 4.3 Memória GPU

- Revisar alocação, importação e liberação.
- Confirmar semântica de GPU VA e CPU mapping.
- Revisar `SAME_VA`, `NEED_MMAP`, alias e JIT.
- Investigar coerência e cache operations.
- Avaliar compartilhamento DMA-BUF.

#### 4.4 Sincronização

- Separar fences, sync_file e coerência DMA-BUF.
- Revisar lifetime de waiters e FDs.
- Revisar timeout, EINTR e eventos de poll.
- Investigar falhas parciais de KCPU.
- Investigar sincronização interprocessos.
- Distinguir análise estática de teste reproduzido.

#### 4.5 Firmware, energia e recuperação

- Documentar interfaces observáveis.
- Identificar sequência de inicialização e encerramento.
- Registrar sinais observáveis de falha e recuperação.
- Identificar limites de investigação sem fonte do kernel.
- Não afirmar detalhes internos sem documentação ou evidência.

#### 4.6 Segurança

- Revisar permissões e acesso ao dispositivo.
- Registrar restrições SELinux e namespaces relevantes.
- Avaliar isolamento e fronteiras de confiança visíveis no userspace.
- Documentar riscos sem presumir implementação interna do kernel.

#### 4.7 Android e Linux glibc

- Identificar dependências e diferenças de integração.
- Documentar acesso ao dispositivo e permissões.
- Revisar DMA-BUF, sincronização e WSI conforme aplicável.
- Separar builds e testes de cada ambiente.
- Não inferir que sucesso em Android comprova funcionamento em Linux
  glibc, ou vice-versa.

**Entregáveis:**

- Achados técnicos atualizados.
- Evidências adicionais.
- Riscos e limitações.
- Backlog residual.

**Critério de saída:** todas as lacunas críticas estão resolvidas ou
explicitamente classificadas como não verificáveis, fora do escopo ou
pendentes de autorização.

### Fase 5 --- Definir o contrato operacional da skill

**Objetivo:** converter o conhecimento técnico em regras claras para
agentes.

A skill deverá instruir o agente a:

1.  Identificar plataforma, dispositivo e GPU antes de analisar um
    problema.
2.  Confirmar se a evidência se aplica ao Moto G86.
3.  Separar Android e Linux glibc.
4.  Distinguir Mesa limpo, Kraid e componentes específicos da
    plataforma.
5.  Localizar as fontes de verdade antes de concluir.
6.  Analisar Kbase, UAPI, ABI e IOCTLs.
7.  Analisar CSF/JM apenas conforme aplicabilidade comprovada.
8.  Analisar memória GPU, DMA-BUF, cache e sincronização.
9.  Analisar firmware, power, recuperação e segurança dentro dos limites
    observáveis.
10. Classificar evidências por nível de validação.
11. Produzir diagnósticos com referências rastreáveis.
12. Preparar patches pequenos e revisáveis quando necessário.
13. Preservar mudanças existentes.
14. Solicitar autorização antes de aplicar patches ou executar testes
    físicos.
15. Encerrar com diagnóstico, evidências, riscos e próximos passos.

A skill deverá proibir:

- Tratar a G615 MC6 como validação da MC2.
- Ampliar suporte para outras GPUs sem decisão.
- Afirmar compatibilidade com base apenas em layouts compilados.
- Afirmar funcionamento de kernel/firmware sem evidência.
- Executar operações destrutivas para limpar a árvore.
- Aplicar patches ou criar commits sem autorização.
- Executar testes de hardware sem autorização.
- Declarar desempenho sem benchmark reproduzível.

**Entregável:** `SKILL_REQUIREMENTS.md` atualizado e aprovado antes da
geração do conteúdo final.

### Fase 6 --- Construir a skill

**Objetivo:** gerar a skill modular, concisa e operacional.

Estrutura proposta:

```text
.agents/skills/mali-kernel-platform/
├── SKILL.md
├── references/
│   ├── architecture.md
│   ├── kbase-uapi-abi.md
│   ├── csf-jm.md
│   ├── gpu-memory.md
│   ├── dma-buf-sync.md
│   ├── firmware-power.md
│   ├── security.md
│   ├── android.md
│   ├── linux-glibc.md
│   └── validation.md
└── workflows/
    ├── platform-discovery.md
    ├── uapi-audit.md
    ├── memory-sync-audit.md
    ├── csf-audit.md
    └── device-validation.md
```

#### 6.1 `SKILL.md`

Deve conter:

- Nome e descrição da skill.
- Escopo e condições de acionamento.
- Dispositivo e plataformas-alvo.
- Invariantes e regras de segurança.
- Procedimento de investigação.
- Critérios de evidência.
- Política de patches e autorização.
- Roteamento para referências e workflows.
- Limitações conhecidas.

O arquivo principal deve ser curto o suficiente para funcionar como
ponto de entrada. Detalhes técnicos extensos devem ficar nas
referências.

#### 6.2 Referências

Cada referência deve conter:

- Escopo.
- Interfaces e conceitos relevantes.
- Comportamento confirmado.
- Limites e diferenças por plataforma.
- Evidências e fontes.
- Riscos conhecidos.
- Itens desconhecidos.
- Links relativos para documentos do projeto.

#### 6.3 Workflows

Cada workflow deve definir:

- Quando executar.
- Pré-condições.
- Fontes a consultar.
- Passos de investigação.
- Evidências a coletar.
- Critérios de sucesso e falha.
- Condições de interrupção.
- Entregáveis.
- Ações que exigem autorização.

#### 6.4 Integração com outras skills

A skill central `mesa3d-mali-expert` deve continuar responsável pelo
roteamento geral.

`kraid-compiler` deve cobrir o compilador Kraid. `panfrost-panvk` deve
cobrir frontend e infraestrutura Panfrost/PanVK. `mali-kernel-platform`
deve cobrir interfaces de kernel e plataforma.

Não duplicar conteúdo dessas skills. Definir claramente as fronteiras e
os pontos de encaminhamento.

**Critério de saída:** todos os arquivos estão gerados, os links
relativos funcionam e não há instruções contraditórias.

### Fase 7 --- Verificação estrutural e técnica

**Objetivo:** verificar a qualidade da skill sem executar testes
físicos.

Verificações:

- Estrutura de diretórios.
- Formatação Markdown.
- Links relativos.
- Referências a arquivos existentes.
- Consistência de nomes e termos.
- Ausência de instruções contraditórias.
- Conformidade com o escopo aprovado.
- Rastreabilidade das afirmações técnicas.
- Separação entre fatos, inferências e hipóteses.
- Ausência de alegações de validação não comprovadas.
- Ausência de duplicação desnecessária com outras skills.

Casos de revisão obrigatórios:

1.  Identificação do Moto G86 e da G615 MC2.
2.  Análise de versão e layout UAPI.
3.  Diagnóstico de falha de alocação.
4.  Análise de importação DMA-BUF.
5.  Análise de sync_file e lifetime de waiter.
6.  Diagnóstico de falha CSF.
7.  Separação entre Android e Linux glibc.
8.  Identificação de evidência insuficiente.
9.  Preparação de patch sem aplicá-lo.
10. Recusa em generalizar resultado da MC6 para a MC2.

**Entregáveis:**

- Relatório de verificação.
- Lista de defeitos.
- Patches de correção, se necessários.

### Fase 8 --- Auditoria independente e homologação

**Objetivo:** avaliar se a skill está correta, completa e utilizável.

A auditoria deve verificar:

Critério Condição de aprovação

---

Escopo Somente G15, Moto G86, Android e Linux glibc
Baseline Mesa 27 limpo identificado
Arquitetura Kraid tratado como migração concluída
Preservação Evidências anteriores mantidas
Rastreabilidade Afirmações técnicas importantes têm fontes
Precisão Fatos e hipóteses não são misturados
Cobertura Domínios necessários estão cobertos
Segurança Restrições de autorização são explícitas
Operação Workflows conduzem investigações reproduzíveis
Integração Sem conflito ou duplicação com outras skills

O auditor deve trabalhar com os requisitos e as evidências, não apenas
revisar a redação do `SKILL.md`.

**Status possível:**

- `APPROVED`: todos os critérios obrigatórios atendidos.
- `PARTIAL`: há lacunas não críticas ou itens pendentes claramente
  delimitados.
- `NOT APPROVED`: há contradições críticas, falta de rastreabilidade
  ou violações de escopo/segurança.

A homologação documental não equivale a validação física do driver.

## 7. Classificação obrigatória das evidências

Usar uma classificação consistente:

---

Classe Significado

---

`STATIC_CONFIRMED` Confirmado por inspeção de código,
headers, UAPI ou documentação

`REPRODUCED` Comportamento reproduzido por
experimento documentado

`BUILD_VALIDATED` Build concluído e identificado por
ambiente e versão

`AUTOMATED_TEST_VALIDATED` Teste automatizado executado e com
resultado registrado

`DEVICE_VALIDATED` Teste real executado no Moto G86,
com evidência

`HISTORICAL_REPORT` Resultado histórico relatado, ainda
não reproduzido nesta referência

`INFERRED` Interpretação sustentada por
evidências indiretas

`HYPOTHESIS` Hipótese ainda não confirmada

`UNKNOWN` Informação não disponível ou não
verificável

---

Toda evidência deve registrar, quando aplicável:

- Identificador.
- Afirmação sustentada.
- Fonte ou caminho.
- Commit ou patch set.
- Dispositivo.
- GPU.
- Sistema e versão.
- Data.
- Procedimento.
- Resultado.
- Limitações.
- Classe de evidência.

## 8. Gestão de patches e alterações

- Não editar diretamente arquivos-fonte para contornar o fluxo de
  revisão.
- Preparar mudanças como patches pequenos e revisáveis.
- Não aplicar patches sem autorização explícita.
- Não sobrescrever documentos existentes sem comparar o conteúdo e
  preservar informações.
- Não executar `git reset --hard`, `git clean`, `git checkout`
  destrutivo ou equivalentes.
- Não modificar `work/mesa` ou outros artefatos de migração como parte
  da geração documental, salvo autorização específica.
- Não criar commits sem autorização explícita.
- Registrar arquivos alterados e verificações executadas.

A geração da skill pode produzir novos arquivos e patches documentais. A
aplicação desses patches permanece sujeita à autorização do usuário.

## 9. Critérios finais de conclusão

A skill estará concluída quando:

- [ ] O baseline Mesa 27 limpo estiver identificado.
- [ ] A integração Kraid estiver corretamente descrita como concluída.
- [ ] O escopo G15 / Moto G86 / Android / Linux glibc estiver
      refletido em todos os documentos.
- [ ] Os artefatos anteriores estiverem preservados ou suas ausências
      registradas.
- [ ] Evidências da MC6 e de outros dispositivos estiverem claramente
      separadas.
- [ ] O perfil técnico do Moto G86 estiver documentado com limites
      explícitos.
- [ ] Fases e investigações anteriores estiverem rastreadas sem
      reconstrução fictícia.
- [ ] Lacunas técnicas críticas estiverem resolvidas ou classificadas.
- [ ] `SKILL.md` estiver gerado.
- [ ] Referências técnicas estiverem geradas.
- [ ] Workflows estiverem gerados.
- [ ] Integração com as demais skills estiver definida.
- [ ] Verificação estrutural e técnica estiver concluída.
- [ ] Auditoria independente estiver aprovada ou as pendências
      estiverem formalmente aceitas.
- [ ] Nenhuma validação física não executada estiver declarada como
      concluída.

## 10. Ordem prática de execução

A sequência recomendada é:

1.  **M1 --- Baseline e preservação:** registrar o Mesa 27 limpo e
    inventariar o material existente.
2.  **M2 --- Consolidação e cobertura:** reconciliar documentos,
    recuperar o mapa de fases e classificar as lacunas.
3.  **M3 --- Investigação direcionada:** completar apenas o que falta
    para o Moto G86 e os ambientes Android/glibc.
4.  **M4 --- Requisitos e geração:** aprovar o contrato operacional e
    gerar `SKILL.md`, referências e workflows.
5.  **M5 --- Verificação e homologação:** executar revisão estrutural,
    técnica e auditoria independente.

Não começar pela escrita do `SKILL.md`. Primeiro consolidar as fontes
existentes e definir com precisão o que ainda falta. Isso evita repetir
trabalho e impede que a skill transforme hipóteses ou resultados de
outro dispositivo em regras operacionais.

---

## 11. Primeiro passo autorizado pelo plano

A primeira atividade é exclusivamente de inventário e leitura:

- Identificar o commit e o estado da referência Mesa 27 limpa.
- Listar os documentos de consolidação existentes.
- Confirmar os arquivos de perfil, worklogs, patches e validação
  preservados.
- Comparar o inventário atual com os registros anteriores.
- Produzir um relatório de divergências.

Nenhum patch deve ser aplicado. Nenhum teste físico deve ser executado.
Nenhum commit deve ser criado.

**Resultado esperado:** uma fotografia confiável do estado atual,
suficiente para iniciar M1 sem perder o trabalho já realizado.
