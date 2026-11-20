# Plano de Implementação — Skill `panfrost-panvk`

**Versão:** 1.0  
**Status:** Proposto para aprovação  
**Escopo:** Construção de uma nova skill especializada  
**Arquivo de destino:** `.agents/skills/panfrost-panvk/SKILL.md`  
**Escopo de código:** Nenhuma alteração no código-fonte Mesa, Panfrost, PanVK ou Kraid.

---

## 1. Objetivo

Construir uma skill especializada em investigação, análise, desenvolvimento e manutenção do PanVK, utilizando Panfrost como referência para infraestrutura compartilhada e integração com o Mesa.

A skill deverá orientar agentes a compreender o caminho completo entre a API Vulkan, a implementação PanVK, os compiladores, os recursos gráficos, a submissão de comandos e a execução na GPU Mali.

Prioridades:

1. Precisão técnica.
2. Rastreabilidade das conclusões.
3. Compreensão dos contratos entre componentes.
4. Compatibilidade entre gerações Mali.
5. Investigação reproduzível.
6. Segurança e preservação do repositório.
7. Economia de contexto e ausência de duplicação entre skills.

## 2. Princípios de implementação

- PanVK é o domínio principal.
- Panfrost é o domínio de referência e integração.
- A G615 MC6, arquitetura Pan 11 e CSF são a plataforma inicial de referência, não o limite de suporte.
- O suporte Vulkan deve ser verificado por funcionalidade, geração e revisão.
- A implementação real deve prevalecer sobre documentação genérica.
- Nenhuma hipótese deve ser apresentada como comportamento confirmado.
- A skill deve investigar interfaces sem assumir a responsabilidade das skills especializadas.
- Alterações no código devem ser preparadas como patches revisáveis.
- Aplicação de patches e commits exigem autorização explícita.

## 3. Fases de implementação

### Fase 0 — Preparação e levantamento de referências

**Objetivo:** estabelecer a base técnica necessária para escrever a skill.

Atividades:

1. Identificar a estrutura atual de `.agents/skills/`.
2. Consultar a skill central `mesa3d-mali-expert`.
3. Consultar a versão aprovada de `kraid-compiler`.
4. Identificar regras comuns de governança e investigação.
5. Reunir as referências arquiteturais do PanVK e Panfrost.
6. Identificar os diretórios e principais componentes do driver.
7. Identificar os limites de responsabilidade das demais skills.

Referências técnicas prioritárias:

- `src/panfrost/vulkan/`
- `src/panfrost/lib/`
- `src/panfrost/lib/genxml/`
- `src/gallium/drivers/panfrost/`
- `src/compiler/nir/`
- `src/panfrost/compiler/`

Os caminhos e símbolos deverão ser confirmados na revisão efetivamente utilizada pelo projeto. Não presumir que todos os componentes ou arquivos existem em todas as revisões.

**Entregável:** inventário técnico e mapa de responsabilidades.

**Critério de conclusão:** nenhuma seção da futura skill dependerá de caminhos ou componentes presumidos.

### Fase 1 — Arquitetura e inicialização do PanVK

**Objetivo:** documentar como o driver Vulkan é estruturado e inicializado.

Cobertura:

- Instance e Physical Device.
- Device creation.
- Device capabilities.
- Feature negotiation.
- Extensions e properties.
- Queue families.
- Command pools.
- Device limits.
- Identificação da GPU.
- Inicialização de estruturas internas.
- Ciclo de vida dos objetos.
- Tratamento de falhas de inicialização.

Investigação obrigatória:

- Como o dispositivo é descoberto.
- Como a geração Mali é identificada.
- Como recursos são anunciados ao Vulkan.
- Como os objetos Vulkan são representados internamente.
- Como o driver diferencia funcionalidades implementadas, parcialmente implementadas e indisponíveis.

**Entregável:** mapa arquitetural de inicialização e ciclo de vida.

### Fase 2 — Implementação Vulkan

**Objetivo:** construir a cobertura técnica das funcionalidades da API.

Domínios:

**2.1 Objetos e estado**

- VkInstance.
- VkPhysicalDevice.
- VkDevice.
- Queues.
- Command pools.
- Command buffers.
- Pipeline cache.
- Query pools.
- Objetos auxiliares.

**2.2 Graphics pipeline**

- Pipeline layout.
- Shader stages.
- Vertex input.
- Input assembly.
- Tessellation.
- Geometry.
- Rasterization.
- Multisampling.
- Depth/stencil.
- Color blending.
- Dynamic state.
- Render passes.
- Subpasses.
- Framebuffers.
- Dynamic rendering.

A skill deverá verificar a disponibilidade de cada estágio e funcionalidade na implementação real.

**2.3 Compute pipeline**

- Compute shader.
- Pipeline layout.
- Descriptor binding.
- Push constants.
- Workgroup configuration.
- Dispatch.
- Dependências de memória.
- Sincronização entre operações.

**2.4 Descriptors e binding**

- Descriptor set layouts.
- Descriptor pools.
- Descriptor sets.
- Descriptor updates.
- Descriptor binding.
- Dynamic offsets.
- Push descriptors, quando aplicável.
- Descriptor indexing, conforme suporte.
- Buffer views.
- Image views.
- Samplers.

**2.5 Outros recursos Vulkan**

- Queries.
- Occlusion.
- Timestamps.
- Events.
- Conditional rendering, quando aplicável.
- Extensões específicas.
- Recursos de compatibilidade.

**Entregável:** matriz de funcionalidades Vulkan e mapa de implementação.

### Fase 3 — Shaders e integração com compiladores

**Objetivo:** documentar o caminho de shaders até a geração e utilização do código de GPU.

Cobertura:

1. Recepção de SPIR-V.
2. Validação e processamento.
3. Conversão para NIR.
4. Transformações NIR realizadas pelo driver.
5. Seleção do backend.
6. Preparação dos parâmetros de compilação.
7. Integração com Kraid.
8. Recepção dos artefatos compilados.
9. Integração com metadados e recursos.
10. Utilização do resultado nos pipelines.

Rastreabilidade obrigatória:

- Ponto de entrada.
- Função responsável.
- Estruturas de dados.
- Opções de compilação.
- Informações de arquitetura.
- Contrato de entrada e saída.
- Tratamento de erros.
- Metadados esperados pelo driver.

**Fronteira de responsabilidade:**

A `panfrost-panvk` investiga preparação, seleção, integração e consumo dos resultados.

A `kraid-compiler` investiga tradução interna, otimizações, scheduling, liveness, RA, spilling e geração ISA.

**Entregável:** mapa completo de integração entre Vulkan, NIR, Kraid e PanVK.

### Fase 4 — Recursos e gerenciamento de memória

**Objetivo:** estabelecer metodologia para investigar recursos e memória.

Cobertura:

- Buffers.
- Images.
- Image views.
- Samplers.
- Memory objects.
- Memory types e heaps.
- Allocation e binding.
- GPU virtual addressing.
- CPU mapping.
- Cache coherency.
- Resource aliasing.
- Image layouts.
- Tiling.
- Modifiers.
- Metadata.
- Compressão.
- Importação e exportação de recursos.
- Compartilhamento de memória.

Rastreabilidade obrigatória:

- Criação.
- Alocação.
- Binding.
- Utilização.
- Sincronização.
- Mapeamento.
- Destruição.

A skill deverá distinguir memória Vulkan, gerenciamento de memória no userspace e mecanismos disponibilizados pelo kernel.

**Entregável:** matriz de recursos, memória e ciclo de vida.

### Fase 5 — Sincronização e submissão de comandos

**Objetivo:** compreender como as garantias Vulkan são implementadas pelo driver e pelo hardware.

Cobertura:

**5.1 Sincronização Vulkan**

- Pipeline barriers.
- Memory barriers.
- Buffer barriers.
- Image barriers.
- Events.
- Binary semaphores.
- Timeline semaphores.
- Fences.
- Synchronization2.
- Queue family ownership transfer.
- Host synchronization.

**5.2 Execução**

- Command buffer recording.
- Command buffer state.
- Queue submission.
- Job construction.
- Job dependencies.
- Hardware command stream.
- Completion tracking.
- Fence signaling.
- Error recovery.
- Timeout e GPU hang.

**5.3 Coerência**

- Cache flush.
- Cache invalidate.
- Memory visibility.
- Execution dependency.
- Memory dependency.
- Dependências entre estágios.
- Dependências entre filas.

A skill deverá diferenciar:

1. Garantia especificada pela API.
2. Tratamento realizado pelo PanVK.
3. Mecanismo de sincronização utilizado pelo hardware.
4. Interface disponibilizada pelo kernel.

**Entregável:** mapa de sincronização e submissão.

### Fase 6 — WSI e apresentação

**Objetivo:** documentar o caminho entre a aplicação Vulkan e a apresentação de imagens.

Cobertura:

- VkSurfaceKHR.
- Swapchain.
- Image acquisition.
- Present modes.
- Presentation.
- Presentation synchronization.
- Buffer import/export.
- DRM/KMS.
- Integração Android.
- Integração Linux.
- Interfaces de janela.
- Restrições específicas da plataforma.

A investigação deverá separar os caminhos Android e Linux.

**Entregável:** mapa WSI e matriz de compatibilidade por plataforma.

### Fase 7 — Panfrost como referência de integração

**Objetivo:** documentar somente os componentes Panfrost necessários para compreender o PanVK.

Cobertura:

- Infraestrutura compartilhada.
- Bibliotecas comuns.
- Estruturas de dispositivo.
- Informações de GPU.
- GenXML.
- Geração de comandos.
- Integração com NIR.
- Recursos e memória compartilhados.
- Interfaces com o kernel.
- Diferenças entre Gallium e Vulkan.

Não deverá transformar a skill em uma documentação completa do driver Gallium.

**Entregável:** mapa das dependências PanVK/Panfrost.

### Fase 8 — Compatibilidade entre gerações Mali

**Objetivo:** impedir generalizações incorretas entre diferentes gerações.

Dimensões:

- Modelo de GPU.
- Arquitetura Pan.
- ISA.
- Execution model.
- CSF/JM.
- Recursos de hardware.
- Formatos.
- Memory layout.
- Sincronização.
- Kernel/UAPI.
- Firmware.
- Vulkan features.
- WSI.

Cada afirmação específica deverá identificar sua revisão, geração e condições relevantes.

A G615 MC6 será utilizada como referência inicial de validação, sem limitar a cobertura arquitetural da skill.

**Entregável:** metodologia de compatibilidade por geração.

### Fase 9 — Metodologia de testes e diagnóstico

**Objetivo:** definir como investigar e validar problemas no PanVK.

Cobertura:

- Vulkan CTS.
- Testes unitários Mesa.
- Piglit, quando aplicável.
- Testes de compilação de shaders.
- Testes graphics.
- Testes compute.
- Testes de descriptors.
- Testes de memória.
- Testes de sincronização.
- Testes de formatos.
- Testes WSI.
- Testes em hardware real.
- Regressões.
- Análise de GPU hangs.

Separar obrigatoriamente:

1. Auditoria estática.
2. Build.
3. Testes automatizados em software.
4. Testes funcionais em hardware.
5. Profiling e benchmarks.

Nenhum resultado deverá ser declarado como validado sem evidência correspondente.

**Entregável:** metodologia de testes e diagnóstico.

### Fase 10 — Governança e integração com outras skills

**Objetivo:** garantir consistência com a arquitetura modular do projeto.

Responsabilidades:

| Skill                    | Domínio                        |
| ------------------------ | ------------------------------ |
| `mesa3d-mali-expert`     | Governança geral e roteamento  |
| `kraid-compiler`         | Compilador Kraid               |
| `panfrost-panvk`         | PanVK e integração Panfrost    |
| `mali-kernel-platform`   | Kernel, UAPI e firmware        |
| `mesa-kraid-migration`   | Migração e integração global   |
| `panvk-build-validation` | Build e distribuição           |
| `gpu-testing-profiling`  | Testes, profiling e benchmarks |

A skill deverá encaminhar tarefas para a especialização correta, mantendo contexto suficiente para investigar as interfaces compartilhadas.

**Entregável:** matriz de roteamento e fronteiras.

### Fase 11 — Construção do SKILL.md

**Objetivo:** transformar as fases anteriores em um documento operacional.

Estrutura prevista:

1. Purpose and scope.
2. Authority and source boundaries.
3. PanVK architecture.
4. Vulkan implementation domains.
5. Graphics and compute pipelines.
6. Shader and Kraid integration.
7. Resource and memory management.
8. Synchronization and submission.
9. WSI and presentation.
10. Panfrost integration reference.
11. Mali generation compatibility.
12. Investigation methodology.
13. Testing and validation.
14. Evidence and traceability.
15. Cross-skill routing.
16. Safety and change control.
17. Completion criteria.

Requisitos de escrita:

- Instruções operacionais, não apenas explicações.
- Linguagem técnica precisa.
- Evitar duplicação da skill central.
- Evitar runbooks extensos sem necessidade.
- Não afirmar suporte sem evidência.
- Manter o conteúdo adequado ao carregamento como skill.

**Entregável:** primeira versão completa do `SKILL.md`.

### Fase 12 — Revisão técnica independente

**Objetivo:** identificar lacunas, contradições e responsabilidades duplicadas.

Revisões obrigatórias:

1. Arquitetura PanVK.
2. Cobertura Vulkan.
3. Pipeline graphics/compute.
4. Integração NIR/Kraid.
5. Memória e recursos.
6. Sincronização e submissão.
7. WSI.
8. Compatibilidade Mali.
9. Fronteiras entre skills.
10. Segurança e governança.

Cada problema identificado deverá ser classificado por severidade e impacto.

**Entregável:** relatório de revisão técnica.

### Fase 13 — Ajustes e validação final

**Objetivo:** concluir a skill sem expandir seu escopo desnecessariamente.

Atividades:

- Corrigir inconsistências.
- Completar instruções ausentes.
- Remover duplicações.
- Verificar roteamento.
- Revisar referências a arquivos e símbolos.
- Conferir critérios de evidência.
- Revisar extensão e legibilidade.
- Executar validação estrutural do documento.

Critérios:

- Estrutura Markdown válida.
- Metadados e identificador da skill válidos para o formato adotado pelo projeto.
- Ausência de referências inventadas.
- Ausência de contradições.
- Fronteiras explícitas.
- Instruções executáveis pelo agente.
- Cobertura alinhada à especificação aprovada.

**Entregável:** versão final candidata à aprovação.

### Fase 14 — Validação prática da skill

**Objetivo:** verificar se a skill funciona em uma investigação real.

Executar uma auditoria estática de um fluxo PanVK escolhido, sem modificar código.

A auditoria deverá demonstrar que a skill consegue:

1. Identificar proveniência e estado do repositório.
2. Encontrar os pontos de entrada relevantes.
3. Reconstruir o fluxo de execução.
4. Identificar contratos entre componentes.
5. Rastrear uma funcionalidade Vulkan até a implementação.
6. Separar fatos de hipóteses.
7. Identificar lacunas de cobertura.
8. Produzir conclusões com evidências.
9. Encaminhar corretamente questões de outras especializações.

A validação não exigirá corrigir os problemas encontrados.

**Entregável:** relatório de validação prática.

### Fase 15 — Aprovação e inclusão no projeto

**Objetivo:** encerrar a construção da skill.

Atividades:

1. Apresentar a versão final.
2. Apresentar o relatório de revisão.
3. Apresentar o resultado da validação prática.
4. Obter aprovação explícita.
5. Preparar patch exclusivo para `.agents/skills/panfrost-panvk/SKILL.md`.
6. Apresentar o diff para revisão.
7. Aplicar somente após autorização.

Não realizar commits sem autorização explícita.

**Entregável:** skill aprovada e integrada ao projeto.

---

## 4. Matriz de rastreabilidade obrigatória

A skill deverá incorporar quatro matrizes operacionais.

### 4.1 Feature traceability

| Campo               | Finalidade                 |
| ------------------- | -------------------------- |
| Vulkan feature      | Funcionalidade investigada |
| API entry point     | Entrada na API             |
| Implementation      | Arquivo e símbolo          |
| Conditions          | Condições de execução      |
| Hardware dependency | Dependência de hardware    |
| Generation          | Geração aplicável          |
| Tests               | Testes correspondentes     |
| Evidence            | Evidência                  |
| Status              | Estado confirmado          |

### 4.2 API-to-hardware traceability

| Campo              | Finalidade          |
| ------------------ | ------------------- |
| API operation      | Operação Vulkan     |
| Driver path        | Caminho no PanVK    |
| Internal state     | Estado interno      |
| Command generation | Geração de comandos |
| Kernel interface   | Interface do kernel |
| Hardware mechanism | Mecanismo utilizado |
| Evidence           | Evidência           |

### 4.3 Resource lifecycle

| Campo           | Finalidade    |
| --------------- | ------------- |
| Resource        | Recurso       |
| Creation        | Criação       |
| Allocation      | Alocação      |
| Binding         | Associação    |
| Usage           | Utilização    |
| Synchronization | Sincronização |
| Destruction     | Destruição    |
| Tests           | Validação     |

### 4.4 Environment and provenance

| Campo        | Finalidade           |
| ------------ | -------------------- |
| Repository   | Repositório          |
| Commit       | Revisão              |
| Worktree     | Estado local         |
| Sources lock | Dependências fixadas |
| Host         | Ambiente             |
| Toolchain    | Ferramentas          |
| GPU          | Modelo               |
| Architecture | Arquitetura          |
| Kernel       | Versão e driver      |
| Firmware     | Versão               |
| Tests        | Comandos executados  |
| Limitations  | Limitações           |

---

## 5. Critérios globais de aceitação

A implementação somente será considerada concluída quando:

- [ ] O PanVK estiver definido como domínio principal.
- [ ] O Panfrost estiver limitado à referência de integração.
- [ ] Todos os domínios Vulkan previstos estiverem cobertos.
- [ ] Graphics e compute estiverem separados.
- [ ] A integração com Kraid estiver delimitada.
- [ ] Memória e recursos tiverem rastreabilidade.
- [ ] Sincronização e submissão estiverem documentadas.
- [ ] WSI contemplar Android e Linux.
- [ ] Compatibilidade entre gerações estiver contemplada.
- [ ] A metodologia de testes estiver definida.
- [ ] A governança estiver alinhada à skill central.
- [ ] A revisão independente estiver concluída.
- [ ] A validação prática demonstrar capacidade de investigação.
- [ ] O usuário aprovar a versão final.

## 6. Controle de escopo

Esta implementação contempla exclusivamente a construção da skill.

Não contempla:

- Alterações no código PanVK.
- Alterações no código Panfrost.
- Alterações no compilador Kraid.
- Correções de bugs identificados durante a investigação.
- Alterações de build ou configuração.
- Execução de benchmarks como parte obrigatória da construção documental.
- Commits automáticos.

Problemas identificados durante a validação serão registrados, não corrigidos.

## 7. Ordem de execução

| Ordem | Fase              | Resultado                   |
| ----: | ----------------- | --------------------------- |
|     1 | Preparação        | Inventário técnico          |
|     2 | Arquitetura       | Modelo PanVK                |
|     3 | Vulkan            | Matriz de funcionalidades   |
|     4 | Shaders           | Integração Kraid            |
|     5 | Memória           | Ciclo de vida               |
|     6 | Sincronização     | Fluxo de execução           |
|     7 | WSI               | Apresentação                |
|     8 | Panfrost          | Dependências compartilhadas |
|     9 | Compatibilidade   | Matriz Mali                 |
|    10 | Testes            | Metodologia de validação    |
|    11 | Governança        | Roteamento                  |
|    12 | Construção        | SKILL.md                    |
|    13 | Revisão           | Relatório técnico           |
|    14 | Validação prática | Auditoria estática          |
|    15 | Aprovação         | Inclusão no projeto         |

## 8. Estado esperado ao final

A skill `panfrost-panvk` deverá funcionar como referência operacional para investigações do driver Vulkan do Mesa em plataformas Mali.

Deverá permitir que um agente compreenda o caminho completo da API até a execução, identifique a camada responsável por um problema e encaminhe investigações especializadas sem perder a rastreabilidade técnica.

**Resultado final:** uma skill independente, especializada, revisada e validada, integrada à arquitetura modular de skills do projeto.
