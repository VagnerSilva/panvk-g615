# Plano de Revisão Técnica Complementar — `kraid-compiler`

**Estado:** PROPOSTA — aguardando aprovação  
**Objetivo:** elevar a precisão, rastreabilidade e capacidade de validação da skill `kraid-compiler`, preservando sua estrutura e conteúdo aprovado.

## 1. Escopo da revisão

A revisão será limitada a cinco áreas:

1. Matriz de suporte NIR.
2. Invariantes do Kraid IR.
3. Contratos e dependências dos passes.
4. Compatibilidade entre gerações ISA.
5. Rastreabilidade de testes e validações.

Não faz parte deste trabalho:

- Modificar o código-fonte do Mesa.
- Alterar o comportamento do compilador.
- Reorganizar toda a skill.
- Repetir a auditoria completa do compilador sem necessidade.
- Alterar outras skills ou documentos sem justificativa técnica.

## 2. Fase 0 — Preparação e integridade

### Objetivos

Confirmar o estado real do projeto antes da revisão.

### Atividades

- Confirmar repositório, branch e commit do Mesa.
- Registrar a configuração de compilação utilizada.
- Verificar `git status` e diffs existentes.
- Localizar a versão atual de `kraid-compiler/SKILL.md`.
- Verificar a skill central `mesa3d-mali-expert`.
- Identificar documentos técnicos já existentes que possam servir de referência.

### Critério de conclusão

Inventário registrado, revisão identificada e alterações preexistentes preservadas.

## 3. Fase 1 — Matriz de suporte NIR

### Objetivo

Transformar as orientações atuais em um método reproduzível de verificação de suporte.

### Atividades

Investigar:

- `nir.rs`.
- Opções de compilação NIR.
- Lowering executado antes da tradução.
- Condições por estágio e arquitetura.
- Fallbacks e operações não suportadas.
- Testes existentes.

Definir um formato mínimo para cada entrada:

| Campo       | Informação                                                 |
| ----------- | ---------------------------------------------------------- |
| Operação    | Intrinsic, ALU, texture, jump etc.                         |
| Tipo        | Bit size e formato aplicável                               |
| Estágio     | Vertex, fragment etc.                                      |
| Arquitetura | Modelo ou geração aplicável                                |
| Suporte     | Direct, after lowering, partial, unsupported, not verified |
| Condição    | Pré-requisitos e limitações                                |
| Evidência   | Arquivo, símbolo e revisão                                 |
| Teste       | Teste correspondente ou ausência documentada               |

### Regras

- Não inferir suporte de uma família inteira a partir de um único match arm.
- Diferenciar suporte direto de suporte obtido por lowering.
- Registrar explicitamente operações não verificadas.
- Não classificar fallback ou panic como suporte.

### Critério de conclusão

A skill define como produzir e manter uma matriz NIR baseada em evidências.

## 4. Fase 2 — Matriz de invariantes do Kraid IR

### Objetivo

Garantir que mudanças no IR considerem seus efeitos sobre todo o compilador.

### Atividades

Auditar os invariantes relacionados a:

- SSA e definições/uses.
- Tipos e larguras.
- Phi nodes.
- CFG e blocos.
- Swizzles.
- Efeitos de memória.
- Registradores especiais e estado oculto.
- Metadados e informações derivadas.

Definir um registro mínimo:

| Campo         | Informação                                  |
| ------------- | ------------------------------------------- |
| Invariante    | Propriedade que deve permanecer válida      |
| Representação | Estruturas e símbolos responsáveis          |
| Produtores    | Passes que criam ou modificam a propriedade |
| Consumidores  | Passes que dependem dela                    |
| Validação     | Validator ou teste aplicável                |
| Reparação     | SSA, liveness ou metadados a reconstruir    |
| Risco         | Consequência de violação                    |

### Regras

- Não presumir que `Shader::validate` verifica todas as propriedades.
- Distinguir invariantes garantidos pelo tipo de dados daqueles garantidos por convenção.
- Identificar quais transformações exigem reparação de SSA ou recomputação de liveness.

### Critério de conclusão

A skill exige análise dos invariantes e consumidores afetados antes de mudanças no IR.

## 5. Fase 3 — Contratos e dependências dos passes

### Objetivo

Tornar verificável a ordem de execução e a segurança das transformações.

### Atividades

Para cada passe relevante, registrar:

| Campo          | Informação                       |
| -------------- | -------------------------------- |
| Passe          | Nome e símbolo                   |
| Localização    | Arquivo e chamada                |
| Condição       | Quando é executado               |
| Pré-condições  | Estado exigido na entrada        |
| Transformações | O que pode modificar             |
| Pós-condições  | Estado produzido                 |
| Dependências   | Passes anteriores necessários    |
| Consumidores   | Passes posteriores dependentes   |
| Testes         | Cobertura existente e necessária |

Investigar especialmente:

- Alterações de CFG após RA.
- Reparação de SSA.
- Recomputação de liveness.
- Passes de legalização.
- Efeitos de memória e barreiras.
- Instruções protegidas contra movimentação ou remoção.

### Critério de conclusão

A skill exige contratos verificáveis para mudanças de passes e proíbe reordenação baseada apenas nos nomes das funções.

## 6. Fase 4 — Matriz de compatibilidade ISA

### Objetivo

Evitar generalizações incorretas sobre suporte a gerações Mali.

### Atividades

Confrontar:

- `model.rs`.
- `isa.rs`.
- `encode_v9.rs`.
- `decode.rs`.
- `proc/isa/`.
- Arquivos XML.
- Geradores e disassembler.
- Testes de encoding e decoding.
- Caminho completo de compilação.

Definir uma matriz com:

| Campo          | Informação                         |
| -------------- | ---------------------------------- |
| Arquitetura    | Geração e modelo                   |
| Modelo interno | Aceitação em `model_for_arch`      |
| Encoder        | Faixa efetivamente gerada          |
| Decoder        | Faixa efetivamente suportada       |
| Instruções     | Disponibilidade e restrições       |
| Codegen        | Caminho completo verificado        |
| Testes         | Evidência de cobertura             |
| Estado         | Confirmed, partial ou not verified |

### Regras

- XML presente não significa suporte completo.
- Símbolo gerado não significa que o modelo é aceito.
- Encoder e decoder devem ser avaliados separadamente.
- Não transferir pressupostos de Bifrost para Kraid.
- Toda afirmação de compatibilidade deve indicar a revisão auditada.

### Critério de conclusão

A skill contém um método para determinar suporte ISA sem generalizações entre gerações.

## 7. Fase 5 — Rastreabilidade de testes e validações

### Objetivo

Garantir que resultados possam ser reproduzidos e interpretados corretamente.

### Atividades

Definir um registro mínimo de execução:

| Campo     | Informação                           |
| --------- | ------------------------------------ |
| Revisão   | Commit exato                         |
| Ambiente  | Host, dispositivo e configuração     |
| Build     | Comando e resultado                  |
| Teste     | Nome e comando                       |
| Resultado | PASS, FAIL, BLOCKED ou NOT EXECUTED  |
| Evidência | Log ou saída relevante               |
| Limitação | Condições que restringem a conclusão |

Separar explicitamente:

- Testes unitários.
- Testes de integração.
- Testes de compilação.
- Testes de hardware.
- CTS.
- Estabilidade.
- Benchmarks e profiling.

### Regras

- Não declarar teste aprovado quando não foi executado.
- Não confundir compilação bem-sucedida com correção funcional.
- Não confundir teste unitário com execução real na GPU.
- Não declarar melhoria de performance sem baseline controlado e medições comparáveis.

### Critério de conclusão

A skill estabelece um padrão reproduzível de validação e comunicação de resultados.

## 8. Fase 6 — Revisão cruzada

### Objetivo

Verificar consistência entre as novas orientações e o conteúdo existente.

### Atividades

- Verificar se as cinco extensões complementam os sete capítulos atuais.
- Eliminar instruções redundantes.
- Conferir consistência com `mesa3d-mali-expert`.
- Verificar limites entre compilador, Panfrost/PanVK, kernel e build.
- Identificar regras que devem permanecer na skill central.
- Verificar se os procedimentos são aplicáveis ao Kraid globalmente, não apenas à Mali-G615.

### Critério de conclusão

Nenhuma duplicação significativa, conflito de autoridade ou restrição acidental de arquitetura.

## 9. Fase 7 — Preparação do patch

### Objetivo

Preparar uma alteração pequena, isolada e revisável.

### Arquivo principal

`.agents/skills/kraid-compiler/SKILL.md`

### Atividades

- Preservar o conteúdo aprovado.
- Inserir apenas as complementações necessárias.
- Preferir tabelas compactas e regras operacionais.
- Não criar documentos auxiliares sem necessidade.
- Preparar patch revisável.
- Executar `git diff --check`.
- Conferir o diff completo e o escopo dos arquivos alterados.

### Critério de conclusão

Patch isolado, sem alterações não relacionadas e com justificativa para cada complemento.

## 10. Fase 8 — Revisão final e aprovação

### Verificações

- Precisão técnica das afirmações.
- Referências a arquivos e símbolos.
- Correspondência com a revisão auditada.
- Clareza das classificações de suporte.
- Cobertura dos cinco pontos complementares.
- Ausência de duplicação.
- Compatibilidade com as regras de governança existentes.

### Entrega

Apresentar:

1. Resumo das lacunas encontradas.
2. Evidências que justificam cada correção.
3. Diff completo.
4. Resultado das verificações.
5. Pontos que permanecem desconhecidos.

A integração no projeto só ocorrerá após aprovação explícita do patch.

## 11. Critérios gerais de conclusão

A revisão estará concluída quando:

- [ ] Matriz NIR tiver critérios reproduzíveis.
- [ ] Invariantes do IR estiverem associados a produtores e consumidores.
- [ ] Passes tiverem contratos e dependências documentados.
- [ ] Compatibilidade ISA estiver vinculada à evidência da revisão.
- [ ] Testes e validações tiverem rastreabilidade.
- [ ] A skill central e as demais especializações não apresentarem conflitos.
- [ ] O patch estiver revisado e aprovado.

**Regra de execução:** investigar primeiro, documentar evidências, preparar o patch e aguardar aprovação. Nenhuma alteração no código-fonte do Mesa está autorizada por este plano.
