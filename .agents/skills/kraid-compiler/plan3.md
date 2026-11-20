# Plano de Ajustes Finais — `kraid-compiler`

**Estado:** PROPOSTA — aguardando aprovação  
**Objetivo:** concluir a revisão complementar da skill, reforçando a rastreabilidade das afirmações técnicas, a reprodução dos ambientes de validação e a análise de dependências de scheduling e register allocation.

## 1. Escopo

Três ajustes serão realizados:

1. Rastreabilidade das afirmações técnicas por commit.
2. Identificação completa dos ambientes de validação.
3. Rastreabilidade das dependências de scheduling, liveness e register allocation.

### Fora do escopo

- Reescrever capítulos existentes.
- Alterar a arquitetura da skill.
- Modificar código-fonte do Mesa.
- Alterar contratos internos do compilador.
- Criar novas especializações.
- Modificar outras skills.

## 2. Fase 0 — Preparação e integridade

### Atividades

- Confirmar repositório e branch.
- Registrar o commit atual do Mesa.
- Verificar `sources.lock`.
- Conferir a versão atual de `kraid-compiler/SKILL.md`.
- Verificar o estado de `git status`.
- Preservar todos os diffs preexistentes.
- Identificar as afirmações técnicas que precisam de rastreabilidade.

### Critério de conclusão

Estado do projeto identificado e arquivo da skill localizado sem interferir em alterações existentes.

## 3. Fase 1 — Rastreabilidade das afirmações técnicas

### Objetivo

Impedir que observações de uma revisão sejam reutilizadas como fatos permanentes.

### Afirmações abrangidas

- Ordem do pipeline de compilação.
- Suporte NIR.
- Invariantes do Kraid IR.
- Condições de execução dos passes.
- Compatibilidade ISA.
- Limitações de register allocation e spilling.
- Configuração dos testes de hardware.

### Ajuste proposto

Adicionar à seção `Authority and source boundaries`:

Toda afirmação técnica específica de uma revisão deve registrar:

- Commit exato do Mesa.
- Arquivo e símbolo que sustentam a afirmação.
- Condições de compilação ou execução relevantes.
- Teste ou evidência complementar, quando aplicável.

Distinguir:

- **Revision-bound:** confirmado somente na revisão examinada.
- **Cross-revision verified:** confirmado em múltiplas revisões identificadas.
- **Unknown:** não confirmado na revisão atual.

### Regras

- Não apresentar observações antigas como estado atual.
- Não usar documentação isolada para comprovar comportamento do código.
- Não generalizar resultados de uma arquitetura para outras.
- Revalidar afirmações quando o código ou a configuração mudar.

### Critério de conclusão

Toda afirmação técnica variável possui origem identificável e escopo de validade.

## 4. Fase 2 — Identificação do ambiente de validação

### Objetivo

Permitir reprodução e comparação confiável dos resultados.

### Informações a registrar

| Categoria | Dados                                                      |
| --------- | ---------------------------------------------------------- |
| Código    | Commit do Mesa e estado do worktree                        |
| Host      | Sistema operacional e arquitetura                          |
| Toolchain | Versões de Rust, compilador C/C++ e ferramentas relevantes |
| Build     | Meson, opções, configuração e target                       |
| GPU       | Fabricante, modelo e arquitetura                           |
| Kernel    | Versão e configuração relevante                            |
| Firmware  | Versão identificável, quando disponível                    |
| Runner    | Tipo, configuração e condições de execução                 |
| Testes    | Comandos, resultados e logs                                |

### Ajuste proposto

Expandir a tabela de validação existente para incorporar os dados ambientais relevantes.

Não exigir campos que não se aplicam a uma execução. Registrar explicitamente quando uma informação estiver indisponível.

### Regras

- Não assumir que dois builds são equivalentes por usarem o mesmo commit.
- Não comparar benchmarks sem verificar a equivalência do ambiente.
- Separar limitações ambientais de falhas do compilador.
- Preservar os comandos e resultados originais.

### Critério de conclusão

A skill define um registro ambiental suficiente para reproduzir e interpretar cada validação.

## 5. Fase 3 — Rastreabilidade de scheduling e register allocation

### Objetivo

Documentar como as dependências e restrições são preservadas durante scheduling, liveness, alocação e spilling.

### Escopo técnico

Investigar os componentes:

- `schedule.rs`
- `required_waits.rs`
- `message_slots.rs`
- `reconvergence.rs`
- `liveness.rs`
- `ra.rs`
- `spill.rs`
- `parallel_copy.rs`
- `repair_ssa.rs`

### Dependências abrangidas

- SSA RaW, WaW e WaR.
- Dependências de memória.
- Barriers.
- Registradores ocultos.
- Discard.
- Message slots.
- Reconvergência e fluxo.
- Restrições de alocação.
- Live-in e live-out.
- Instruções geradas por spilling.

### Ajuste proposto

Acrescentar à seção 5 uma tabela de rastreabilidade:

| Dependência ou restrição | Origem                                    | Mecanismo de proteção               | Passes envolvidos         | Estado antes/depois    | Teste/evidência    |
| ------------------------ | ----------------------------------------- | ----------------------------------- | ------------------------- | ---------------------- | ------------------ |
| Dependência ou hazard    | SSA, memória, barreira ou estado especial | Scheduler, waits ou outro mecanismo | Produtores e consumidores | Propriedade preservada | Teste ou evidência |

### Regras

- Não presumir que todas as dependências são representadas por SSA.
- Identificar qual componente realmente garante cada restrição.
- Distinguir dependências de ordenação de restrições de alocação.
- Verificar efeitos de cada transformação sobre liveness.
- Identificar quando SSA ou metadados precisam ser reconstruídos.
- Não declarar segurança de reordenação sem evidência.

### Critério de conclusão

A skill exige rastreamento explícito das dependências e restrições afetadas por mudanças no scheduling e na alocação.

## 6. Fase 4 — Revisão cruzada

### Objetivo

Garantir que os ajustes não criem duplicação ou conflito.

### Atividades

- Conferir as três alterações contra os capítulos existentes.
- Verificar compatibilidade com `mesa3d-mali-expert`.
- Manter regras de governança em `AGENTS.md` e na skill central.
- Evitar repetição de instruções já existentes.
- Preservar o foco global do Kraid, sem restringi-lo à Mali-G615.

### Critério de conclusão

Os ajustes complementam a skill sem alterar sua divisão de responsabilidades.

## 7. Fase 5 — Preparação do patch

### Arquivo permitido

`.agents/skills/kraid-compiler/SKILL.md`

### Atividades

- Preparar patch isolado.
- Preservar o conteúdo já aprovado.
- Alterar somente as seções necessárias.
- Não editar diretamente o código-fonte do Mesa.
- Executar `git diff --check`.
- Conferir o diff completo.
- Verificar se nenhum arquivo não relacionado foi incluído.

### Critério de conclusão

Patch pequeno, revisável e tecnicamente justificado.

## 8. Fase 6 — Revisão e aprovação final

### Verificações

- Rastreabilidade por revisão.
- Identificação suficiente do ambiente.
- Cobertura de dependências de scheduling e RA.
- Ausência de contradições com as orientações existentes.
- Ausência de alterações não autorizadas.
- Integridade do diff.

### Entrega

Apresentar:

1. Resumo das alterações.
2. Evidências técnicas.
3. Diff completo.
4. Resultado das verificações.
5. Limitações remanescentes.

A integração dependerá de aprovação explícita.

## 9. Critérios finais de conclusão

- [ ] Afirmações técnicas vinculadas à revisão de origem.
- [ ] Estados revision-bound, cross-revision verified e unknown definidos.
- [ ] Ambiente de validação reproduzível.
- [ ] Dependências de scheduling rastreáveis.
- [ ] Restrições de RA e spilling rastreáveis.
- [ ] Consistência com as skills centrais e especializadas.
- [ ] Patch isolado e revisado.
- [ ] Aprovação explícita antes da integração.

**Regra de execução:** nenhuma alteração será aplicada sem autorização. O plano não autoriza modificações no código-fonte do Mesa nem commits.
