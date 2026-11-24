# Plano de Correção — Skill `mali-kernel-platform`

**Objetivo:** transformar a skill em um instrumento operacional de desenvolvimento especializado em Mali G15, usando o conhecimento técnico já consolidado no projeto.

## 1. Diretrizes obrigatórias

A correção deve respeitar estas decisões:

- Não interromper nem refazer o plano de consolidação técnica em andamento.
- Preservar todos os documentos, evidências, descobertas e decisões existentes.
- Não repetir investigações já concluídas.
- Não transformar a skill em uma coleção de referências ou recomendações genéricas.
- Converter conhecimento técnico em instruções aplicáveis ao código.
- Investigar somente lacunas que impeçam uma orientação tecnicamente segura.
- Não implementar alterações no Mesa durante a construção da skill.
- Alterações na skill e na documentação devem ser propostas por patches revisáveis.
- Não aplicar patches nem criar commits sem autorização explícita.

## 2. Fase 0 — Receber e preservar a consolidação

**Objetivo:** utilizar o resultado do plano atual como entrada para a correção.

Atividades:

1. Receber os documentos técnicos finais.
2. Conferir a rastreabilidade das descobertas.
3. Preservar os registros de evidências e decisões.
4. Separar conhecimento confirmado, limitações conhecidas e lacunas reais.
5. Identificar quais informações podem se transformar diretamente em instruções operacionais.

**Entrega:** inventário do conhecimento disponível para a skill.

Critério de conclusão: nenhum conhecimento técnico relevante é descartado ou substituído sem justificativa.

## 3. Fase 1 — Converter conhecimento em instruções operacionais

**Objetivo:** transformar cada área técnica em orientação direta para o desenvolvedor.

Áreas obrigatórias:

- Kbase, UAPI e ABI.
- CSF e gerenciamento de filas.
- Job Manager, quando aplicável.
- Memória GPU e gerenciamento de VA.
- DMA-BUF e importação de buffers.
- Sincronização, fences e KCPU.
- Firmware, inicialização e recuperação.
- Integração Android.
- Compatibilidade Linux glibc.
- Integração com Mesa e Kraid.

Para cada área, produzir instruções com:

1. Arquivos e componentes envolvidos.
2. Estruturas, funções e interfaces relevantes.
3. Contratos que devem ser preservados.
4. Regras obrigatórias de implementação.
5. Procedimentos concretos para alterações.
6. Tratamento de erros e condições de falha.
7. Dependências e impactos em outros componentes.
8. Testes e critérios de aceitação.

Não basta informar que determinado componente existe ou que um problema pode ocorrer. A skill deve orientar como trabalhar corretamente com ele.

**Entrega:** conjunto de instruções técnicas operacionais por domínio.

## 4. Fase 2 — Construir os fluxos de desenvolvimento

**Objetivo:** permitir que o agente conduza tarefas de engenharia usando a skill.

A skill deve fornecer procedimentos para:

### 4.1 Correção de defeitos

- Identificar o componente responsável a partir do contexto da tarefa.
- Localizar os pontos de alteração conhecidos.
- Aplicar os contratos e regras documentados.
- Preparar um patch isolado.
- Definir e executar validações adequadas.
- Revisar os impactos e possíveis regressões.

### 4.2 Implementação de funcionalidades

- Identificar as interfaces existentes que devem ser utilizadas.
- Definir as alterações necessárias.
- Preservar compatibilidade e contratos.
- Implementar por etapas verificáveis.
- Preparar testes para os comportamentos novos.
- Validar a integração com os componentes relacionados.

### 4.3 Refatoração

- Preservar comportamento e interfaces existentes.
- Evitar alterações desnecessárias.
- Verificar dependências.
- Comparar o comportamento anterior e posterior.
- Validar ausência de regressões.

### 4.4 Otimização

- Preservar correção funcional.
- Identificar o caminho de execução envolvido.
- Utilizar medições reproduzíveis.
- Evitar otimizações baseadas apenas em suposições.
- Comparar resultados antes e depois.

**Entrega:** procedimentos executáveis para as principais tarefas de desenvolvimento.

## 5. Fase 3 — Definir regras de decisão técnica

**Objetivo:** evitar que o agente redescubra decisões já tomadas ou escolha soluções incompatíveis.

A skill deverá separar:

| Classificação               | Comportamento                                |
| --------------------------- | -------------------------------------------- |
| Decisão aprovada            | Seguir obrigatoriamente                      |
| Contrato técnico confirmado | Preservar                                    |
| Limitação conhecida         | Respeitar e aplicar a orientação documentada |
| Alternativa rejeitada       | Não reutilizar sem nova justificativa        |
| Lacuna real                 | Investigar somente o necessário              |
| Hipótese não validada       | Não tratar como fato                         |

As decisões consolidadas devem ser apresentadas como instruções, não como sugestões opcionais.

**Entrega:** matriz de decisões e regras de execução.

## 6. Fase 4 — Definir validação e segurança das alterações

**Objetivo:** garantir que as instruções resultem em código verificável.

A skill deverá definir:

- Validação estática e compilação.
- Testes unitários e de integração.
- Verificação de ABI e UAPI.
- Testes de memória e sincronização.
- Validação específica de Android e Linux glibc.
- Critérios de regressão.
- Evidências obrigatórias para declarar uma alteração validada.

A validação física deve respeitar a autorização do usuário.

A plataforma de referência permanece:

- GPU: Mali-G615 MC2.
- SoC: MediaTek MT6878.
- Dispositivo: Motorola Moto G86.
- Sistema: Android 16, sujeito à confirmação do estado atual.
- Mesa: baseline limpa 27.0.0-devel.
- Arquitetura: Kraid já integrado.

Resultados de outras GPUs ou dispositivos não podem ser apresentados como validação do Moto G86.

**Entrega:** procedimentos e critérios de validação por domínio.

## 7. Fase 5 — Organizar a arquitetura da skill

**Objetivo:** manter a skill objetiva, utilizável e sem duplicação desnecessária.

A organização deverá separar:

- Instruções centrais de execução.
- Conhecimento técnico por domínio.
- Procedimentos de implementação.
- Regras de compatibilidade.
- Procedimentos de validação.
- Referências técnicas complementares.

A `SKILL.md` deve direcionar o agente para instruções especializadas quando necessário.

Os documentos técnicos existentes devem permanecer preservados. Não devem ser copiados integralmente para a skill quando uma instrução operacional suficiente puder referenciá-los.

**Entrega:** estrutura final da `mali-kernel-platform`.

## 8. Fase 6 — Auditoria operacional independente

**Objetivo:** verificar se a skill realmente orienta o desenvolvimento.

A auditoria deverá avaliar tarefas representativas:

1. Corrigir um problema de importação DMA-BUF.
2. Alterar um fluxo de sincronização.
3. Modificar um componente de gerenciamento CSF.
4. Ajustar uma interface de compatibilidade.
5. Implementar uma funcionalidade de plataforma.

Para cada tarefa, verificar se o agente consegue:

- Identificar os componentes corretos.
- Encontrar os pontos de alteração.
- Respeitar os contratos técnicos.
- Definir uma implementação coerente.
- Preparar um patch revisável.
- Definir validações adequadas.
- Identificar riscos e impactos.

A auditoria não deve exigir alterações reais no Mesa. Pode utilizar exercícios de execução e revisão de patches demonstrativos.

Se uma instrução for insuficiente, a auditoria deverá identificar exatamente o conteúdo que precisa ser corrigido.

**Entrega:** relatório de auditoria operacional com evidências.

## 9. Fase 7 — Correções finais e homologação

**Objetivo:** entregar a skill pronta para uso.

Atividades:

1. Corrigir falhas encontradas na auditoria.
2. Eliminar instruções genéricas ou redundantes.
3. Verificar referências e caminhos dos arquivos.
4. Conferir coerência com as decisões aprovadas.
5. Verificar cobertura dos domínios técnicos.
6. Executar novamente as verificações necessárias.
7. Preparar a versão final para aprovação.

**Entrega:** `mali-kernel-platform` operacional, revisada e pronta para homologação.

## 10. Critérios de aceitação final

A skill somente será considerada concluída quando:

- [ ] Orientar diretamente a implementação e correção de código.
- [ ] Identificar arquivos, componentes e interfaces relevantes.
- [ ] Explicar os contratos técnicos que devem ser preservados.
- [ ] Fornecer procedimentos concretos de desenvolvimento.
- [ ] Definir critérios de validação.
- [ ] Orientar a criação de patches revisáveis.
- [ ] Preservar as decisões arquiteturais aprovadas.
- [ ] Separar fatos, limitações e hipóteses.
- [ ] Evitar investigações repetidas.
- [ ] Ser capaz de orientar tarefas representativas sem depender de uma nova investigação geral.
- [ ] Manter o escopo restrito à Mali G15 e às plataformas aprovadas.
- [ ] Passar pela auditoria operacional independente.

## 11. Resultado esperado

A `mali-kernel-platform` deixa de ser principalmente uma referência técnica e passa a ser uma ferramenta de execução de engenharia.

O fluxo esperado será:

**Tarefa recebida → Orientação técnica → Planejamento da alteração → Implementação → Validação → Revisão.**

A investigação deixa de ser o procedimento padrão. Ela ocorre somente quando existe uma lacuna real que impede a execução segura.

### Regra final

O conhecimento técnico já consolidado deve ser utilizado para resolver problemas, não para mandar o desenvolvedor descobrir novamente como resolvê-los.
