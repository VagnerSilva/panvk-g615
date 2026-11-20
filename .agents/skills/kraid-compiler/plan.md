# Plano de Implementação — kraid-compiler

**Projeto:** Mesa 3D / Kraid  
**Componente:** `.agents/skills/kraid-compiler/SKILL.md`  
**Estado:** PROPOSTA — aguardando aprovação  
**Escopo:** documentação técnica e instruções operacionais da especialização  
**Referência inicial:** Mesa `13baeb70c066a9f82d2bcfb29f06e4865212affa`, branch `feat-migration`  
**Baseline de hardware:** Mali-G615 MC2, CSF v11  
**Objetivo arquitetural:** Kraid como backend global do Mesa, sem limitar a especialização à G615.

---

## 1. Objetivo

Criar uma skill especializada para investigar, desenvolver, revisar e validar o compilador Kraid integrado ao Mesa.

A skill deverá permitir que um agente:

1. Compreenda a arquitetura real do compilador.
2. Rastreie o fluxo NIR → Kraid IR → ISA.
3. Identifique corretamente as responsabilidades de cada subsistema.
4. Investigue erros de compilação e execução.
5. Analise otimizações e transformações.
6. Diagnostique register pressure, alocação e spilling.
7. Avalie scheduling e dependências.
8. Investigue geração e codificação de instruções.
9. Desenvolva mudanças com testes direcionados.
10. Valide correção e desempenho sem conclusões não comprovadas.

A skill não deverá substituir a documentação técnica do código nem duplicar as regras de governança do `AGENTS.md`.

## 2. Escopo técnico

### 2.1 Arquitetura e pipeline

Auditar:

- `compile.rs`
- `lib.rs`
- `builder.rs`
- `meson.build`
- Interfaces C/Rust.
- Entrada e saída do compilador.
- Ordem real dos passes.
- Dependências entre passes.
- Condições de execução dos passes.
- Etapas de validação e geração final.

Entregável: mapa do pipeline real, com entradas, saídas, transformações e invariantes.

### 2.2 NIR frontend

Auditar:

- `nir.rs`
- Conversão de instruções NIR.
- Tipos e formatos.
- Intrinsics.
- Operações ALU.
- Texturas e operações de memória.
- Controle de fluxo.
- Valores constantes.
- Operações não suportadas.
- Lowering executado antes e durante a tradução.

Entregável: matriz de suporte NIR → Kraid IR.

A matriz deverá diferenciar:

- Suporte direto.
- Suporte após lowering.
- Suporte parcial.
- Não suportado.
- Não verificado.

Não presumir que toda operação NIR possui tradução direta.

### 2.3 Kraid IR

Auditar:

- `ir.rs`
- `ops.rs`
- `data_type.rs`
- `model.rs`
- `ssa_value.rs`
- `phi.rs`
- `flow.rs`
- `swizzle.rs`
- `validate.rs`

Investigar:

- Representação SSA.
- Definições e usos.
- Basic blocks.
- CFG.
- Tipos e tamanhos.
- Operandos e modificadores.
- Semântica das operações.
- Valores especiais.
- Reconstrução e validação do IR.

Entregável: documentação das estruturas, invariantes e regras de transformação.

### 2.4 Legalização

Auditar:

- `legalize.rs`
- `legalize_src_swizzles.rs`
- `lower_copy.rs`
- `lower_mkvec_swz.rs`
- `lower_blend_call.rs`
- `small_constants.rs`
- `widen_alu_ops.rs`
- `remat_constants.rs`

Investigar:

- Restrições de operandos.
- Swizzles.
- Tipos e larguras.
- Constantes.
- Operações especiais.
- Requisitos da ISA.
- Ordem e dependências entre transformações.

Entregável: mapa das restrições e das etapas de legalização.

### 2.5 Otimizações

Auditar todos os passes existentes, incluindo:

- `opt_copy_prop.rs`
- `opt_dce.rs`
- `opt_exec_units.rs`
- `opt_flow.rs`
- `opt_fuse.rs`
- `opt_normalize_consts.rs`
- `opt_promote_consts.rs`
- `opt_var.rs`
- `jump_thread.rs`
- `reconvergence.rs`
- `repair_ssa.rs`

Investigar:

- Pré-condições.
- Pós-condições.
- Invariantes preservadas.
- Dependências entre passes.
- Impactos sobre SSA e CFG.
- Impactos sobre register pressure.
- Correção semântica.

Entregável: catálogo dos passes e suas condições de validade.

### 2.6 Scheduling e dependências

Auditar:

- `schedule.rs`
- `required_waits.rs`
- `message_slots.rs`
- `reconvergence.rs`
- `ops.rs`

Investigar:

- Dependências SSA.
- Dependências de memória.
- Read-after-write.
- Write-after-read.
- Write-after-write.
- Barriers.
- Side effects.
- Recursos especiais.
- Hidden registers.
- Reconvergência.
- Message slots.
- Scheduling orientado à pressão de registradores.

Entregável: mapa de dependências e regras de ordenação.

### 2.7 Liveness e register allocation

Auditar:

- `liveness.rs`
- `ra.rs`
- `parallel_copy.rs`
- `repair_ssa.rs`
- `ssa_value.rs`

Investigar:

- Live-in e live-out.
- Live ranges.
- Interferência.
- Restrições de registradores.
- Classes e tamanhos.
- Alocação.
- Coalescing, quando existente.
- Cópias paralelas.
- Spill candidates.
- Custos e limitações.

Entregável: documentação do fluxo real de liveness e alocação.

### 2.8 Spilling

Auditar:

- `spill.rs`
- Interfaces com register allocation.
- Representação de spill slots.
- Loads e stores gerados.
- Reescrita do IR.
- Novos live ranges.
- Reexecução de passes.
- Casos de falha.

Entregável: fluxo completo de spilling e suas invariantes.

### 2.9 ISA e codegen

Auditar:

- `isa.rs`
- `encode_v9.rs`
- `decode.rs`
- `proc/isa/`
- `isa-v9-v14.xml`
- `isa-v15.xml`
- `tools/isa-gen.rs`
- `tools/disassembler.rs`

Investigar:

- Modelo de instruções.
- Campos e operandos.
- Encoding e decoding.
- Modificadores.
- Restrições por geração.
- Instruções especiais.
- Compatibilidade entre versões da ISA.
- Geração de código.
- Validação do código gerado.

Entregável: mapa do subsistema ISA e matriz de compatibilidade por geração.

### 2.10 Hardware runner e testes

Auditar:

- `hw_tests.rs`
- `hw_runner/`
- `validate.rs`
- Testes unitários.
- Testes de integração.
- Testes de execução.
- Mecanismos de comparação de resultados.

Investigar:

- Como os shaders são preparados.
- Como os testes são enviados ao hardware.
- Como resultados são coletados.
- Como falhas são classificadas.
- Como reproduzir regressões.
- Quais testes dependem de hardware real.

Entregável: mapa de validação e cobertura conhecida.

### 2.11 Integração com Mesa

Auditar:

- `kraid.h`
- `bindings.h`
- `compile.rs`
- `lib.rs`
- `meson.build`
- Consumidores do compilador.
- Interfaces compartilhadas.
- Seleção do backend.
- Fluxo de erros e diagnósticos.

Investigar a integração com Panfrost e PanVK sem duplicar a especialização `panfrost-panvk`.

Entregável: documentação dos contratos de integração e das fronteiras entre subsistemas.

---

## 3. Fases de execução

### Fase 0 — Preparação e integridade

Atividades:

1. Confirmar o repositório e a revisão de referência.
2. Confirmar a branch de trabalho.
3. Inspecionar o estado do Git.
4. Identificar alterações preexistentes.
5. Confirmar a localização das skills existentes.
6. Ler `AGENTS.md` e a skill central aprovada.
7. Confirmar os procedimentos de patch-only.

Entregáveis:

- Registro da revisão auditada.
- Inventário inicial.
- Lista de arquivos modificados previamente.
- Escopo congelado da implementação.

Critério de aprovação:

Nenhuma alteração preexistente poderá ser sobrescrita ou descartada.

### Fase 1 — Auditoria do pipeline

Atividades:

1. Examinar `compile.rs`.
2. Reconstruir a ordem dos passes.
3. Identificar dependências.
4. Identificar fronteiras de entrada e saída.
5. Examinar a integração com o frontend.
6. Identificar os pontos de validação.
7. Registrar lacunas documentais.

Entregáveis:

- Diagrama do pipeline.
- Tabela dos passes.
- Mapa de dependências.
- Lista de questões ainda não resolvidas.

Critério de aprovação:

O fluxo documentado deverá corresponder às chamadas reais encontradas no código.

### Fase 2 — Auditoria de IR e frontend

Atividades:

1. Examinar o frontend NIR.
2. Examinar as estruturas do IR.
3. Mapear tipos e operações.
4. Documentar SSA e CFG.
5. Identificar operações suportadas e não suportadas.
6. Verificar invariantes.
7. Mapear validações.

Entregáveis:

- Matriz NIR → Kraid IR.
- Modelo estrutural do IR.
- Catálogo de operações.
- Lista de invariantes.

Critério de aprovação:

Nenhuma capacidade poderá ser declarada sem evidência na implementação.

### Fase 3 — Auditoria de legalização e otimizações

Atividades:

1. Catalogar passes de legalização.
2. Catalogar passes de otimização.
3. Identificar pré-condições e pós-condições.
4. Reconstruir dependências entre passes.
5. Identificar transformações que alteram SSA ou CFG.
6. Identificar restrições específicas da ISA.
7. Registrar riscos de regressão.

Entregáveis:

- Catálogo de passes.
- Grafo de dependências.
- Matriz de invariantes.
- Matriz de riscos.

Critério de aprovação:

Cada transformação documentada deverá ter sua finalidade e seus limites identificados.

### Fase 4 — Auditoria de scheduling e alocação

Atividades:

1. Examinar o modelo de dependências.
2. Examinar o cálculo de liveness.
3. Examinar o scheduling.
4. Examinar register allocation.
5. Examinar spilling.
6. Verificar como os passes interagem.
7. Identificar pontos de instrumentação.

Entregáveis:

- Fluxo de scheduling.
- Modelo de liveness.
- Fluxo de alocação.
- Fluxo de spilling.
- Lista de invariantes e riscos.

Critério de aprovação:

O relacionamento entre scheduling, liveness, alocação e spilling deverá estar documentado sem simplificações incorretas.

### Fase 5 — Auditoria de ISA e geração

Atividades:

1. Examinar os modelos de ISA.
2. Examinar encoding e decoding.
3. Comparar as definições por geração.
4. Examinar a geração final.
5. Identificar restrições de instruções.
6. Examinar ferramentas de disassembly.
7. Identificar validações existentes.

Entregáveis:

- Mapa de codegen.
- Matriz ISA por geração.
- Catálogo de instruções e restrições relevantes.
- Lista de validações.

Critério de aprovação:

Não misturar características de diferentes gerações nem extrapolar a cobertura dos XMLs sem verificar o código.

### Fase 6 — Auditoria de testes e hardware runner

Atividades:

1. Identificar testes unitários.
2. Identificar testes de integração.
3. Identificar testes de hardware.
4. Examinar o hardware runner.
5. Verificar a coleta de resultados.
6. Identificar limitações de execução.
7. Definir critérios de reprodução.

Entregáveis:

- Matriz de testes.
- Mapa do hardware runner.
- Classificação de validação.
- Lacunas de cobertura.

Critério de aprovação:

Distinguir claramente testes de software, simulação e execução real em GPU.

### Fase 7 — Especificação da skill

Atividades:

1. Consolidar os resultados das auditorias.
2. Definir o conteúdo obrigatório.
3. Definir o roteamento de tarefas.
4. Definir procedimentos de investigação.
5. Definir padrões de evidência.
6. Definir regras para mudanças.
7. Definir critérios de validação.
8. Eliminar duplicação com a skill central e `AGENTS.md`.

Entregável:

Proposta completa de `kraid-compiler/SKILL.md`.

Critério de aprovação:

A skill deverá ser tecnicamente fiel ao código auditado, objetiva e utilizável por um agente independente.

### Fase 8 — Revisão técnica

Revisar:

- Precisão técnica.
- Cobertura do escopo.
- Referências aos arquivos.
- Consistência dos nomes.
- Ausência de afirmações não verificadas.
- Ausência de duplicação.
- Clareza das instruções.
- Compatibilidade com a skill central.
- Compatibilidade com a arquitetura modular.

Entregável:

Relatório de revisão com problemas, correções e pendências.

Critério de aprovação:

Nenhum bloqueador técnico ou de governança poderá permanecer.

### Fase 9 — Preparação do patch

Atividades:

1. Preparar o novo diretório da especialização.
2. Criar o arquivo por patch revisável.
3. Preservar arquivos existentes.
4. Validar o formato Markdown.
5. Verificar frontmatter e identificação da skill.
6. Verificar referências e caminhos.
7. Executar `git diff --check`.
8. Revisar o diff completo.

Entregáveis:

- Patch da nova skill.
- Relatório de validação.
- Diff para aprovação.

Critério de aprovação:

O patch deverá estar pronto para aplicação, sem modificar arquivos fora do escopo autorizado.

### Fase 10 — Aprovação e integração

Atividades:

1. Apresentar o patch completo.
2. Apresentar o relatório técnico.
3. Receber aprovação explícita.
4. Aplicar o patch somente após autorização.
5. Verificar o estado final do Git.
6. Confirmar a presença da skill no projeto.

Entregáveis:

- Skill integrada.
- Diff final.
- Estado de integração documentado.

Critério de aprovação:

A skill só será considerada concluída após confirmação da integração e validação final.

---

## 4. Regras obrigatórias de qualidade

### Evidência

Toda afirmação técnica específica deverá estar vinculada a:

- Arquivo e símbolo.
- Revisão auditada.
- Implementação observada.
- Teste ou especificação, quando aplicável.

### Compatibilidade

Não assumir equivalência entre:

- Mali de gerações diferentes.
- ISA v9–v14 e v15.
- JM e CSF.
- Implementações antigas e novas do Mesa.
- Caminhos Bifrost e Kraid.

### Correção

Toda proposta de mudança no compilador deverá identificar:

- Invariante afetada.
- Subsistemas consumidores.
- Risco semântico.
- Teste de regressão.
- Validação necessária.

### Performance

Não declarar ganho sem comparação controlada.

Separar:

- Correção funcional.
- Estabilidade.
- Consumo de registradores.
- Spilling.
- Latência.
- Throughput.
- Tempo de compilação.

### Segurança do repositório

- Não sobrescrever alterações preexistentes.
- Não executar operações destrutivas.
- Não aplicar mudanças sem autorização.
- Não criar commits sem autorização.
- Não modificar código-fonte durante a elaboração da skill.

---

## 5. Estrutura final esperada

`.agents/skills/kraid-compiler/`

- `SKILL.md`

A primeira versão deverá permanecer concentrada em um único arquivo, salvo se o volume e a necessidade de referência técnica justificarem arquivos auxiliares.

Não criar documentação duplicada de runbooks já existentes.

---

## 6. Critérios de conclusão

A implementação será considerada concluída quando:

1. Todos os domínios previstos tiverem sido auditados.
2. O pipeline real estiver documentado.
3. As principais estruturas e invariantes estiverem identificadas.
4. Os limites de suporte estiverem explícitos.
5. Os procedimentos de investigação estiverem definidos.
6. Os procedimentos de validação estiverem definidos.
7. A skill estiver revisada tecnicamente.
8. O patch tiver sido aprovado.
9. A integração estiver confirmada.

**Resultado esperado:** uma especialização técnica confiável, capaz de orientar engenharia do Kraid em diferentes gerações Mali e plataformas, sem presumir capacidades não implementadas e sem restringir a arquitetura à G615.
