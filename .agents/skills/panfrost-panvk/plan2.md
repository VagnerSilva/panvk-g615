# Plano de implementação — Ajustes complementares da skill `panfrost-panvk`

**Escopo:** revisão complementar da skill `panfrost-panvk`  
**Arquivo-alvo:** `.agents/skills/panfrost-panvk/SKILL.md`  
**Estado inicial:** planejamento; nenhuma alteração aplicada  
**Método:** patch revisável, seguido de validação técnica

## 1. Objetivo

Implementar seis ajustes identificados na revisão técnica da skill `panfrost-panvk`, aumentando a precisão técnica, a rastreabilidade e a confiabilidade dos procedimentos de investigação.

A revisão deve preservar a estrutura e o conteúdo aprovado. Não deve reescrever a skill nem ampliar seu escopo arquitetural.

## 2. Restrições e limites

| Item                  | Regra                                    |
| --------------------- | ---------------------------------------- |
| Arquivo permitido     | `.agents/skills/panfrost-panvk/SKILL.md` |
| Código Mesa           | Não alterar                              |
| Código PanVK/Panfrost | Não alterar                              |
| Código Kraid          | Não alterar                              |
| Outras skills         | Não alterar                              |
| Conteúdo aprovado     | Preservar                                |
| Método de alteração   | Patch revisável                          |
| Aplicação do patch    | Exige autorização explícita              |
| Commit                | Exige autorização explícita              |

A skill `kraid-compiler` pode ser consultada como referência. Ela não deve ser modificada.

As skills especializadas ainda não confirmadas como existentes não podem ser tratadas como disponíveis.

## 3. Fases de implementação

### Fase 0 — Preparação e inventário

**Objetivo:** confirmar o estado real do arquivo antes de preparar alterações.

Atividades:

1. Confirmar a existência do arquivo `SKILL.md`.
2. Ler integralmente sua versão atual.
3. Verificar a validade do frontmatter YAML.
4. Verificar a formatação Markdown.
5. Identificar as seções relacionadas aos seis ajustes.
6. Confirmar quais skills especializadas existem no repositório.
7. Registrar o estado inicial do arquivo e do repositório.
8. Verificar se caracteres como `\\---`, `**#`, `\\|` e `\\(` estão literalmente no arquivo ou se são apenas escapes da representação da mensagem.

**Critérios de conclusão:**

- Arquivo integralmente inspecionado.
- Estado inicial documentado.
- Skills existentes verificadas.
- Nenhuma alteração realizada.

### Fase 1 — Corrigir o roteamento entre skills

**Objetivo:** impedir referências operacionais a skills inexistentes ou ainda não implementadas.

Atividades:

1. Manter a referência à `kraid-compiler`, cuja implementação já foi confirmada.
2. Revisar a referência a `panvk-build-validation`.
3. Aplicar a mesma regra às skills de kernel/plataforma e testes.
4. Exigir verificação da existência da skill antes de encaminhar uma tarefa.
5. Exigir leitura da skill especializada antes de utilizar seus procedimentos.
6. Definir o comportamento alternativo quando uma skill não estiver disponível.

Regra operacional:

```text
IF specialized_skill_exists:
    READ specialized_skill
    ROUTE task
ELSE:
    DECLARE skill_unavailable
    USE available_guidance
    DO_NOT_ASSUME_MISSING_PROCEDURES
```

**Critérios de aceitação:**

- Nenhum encaminhamento pressupõe a existência de uma skill não confirmada.
- A ausência de uma especialização não bloqueia automaticamente a investigação.
- A skill central continua responsável pelo roteamento.
- Não há duplicação desnecessária de instruções entre skills.

### Fase 2 — Separar estado de suporte e qualidade da evidência

**Objetivo:** eliminar a ambiguidade entre o estado de suporte de uma funcionalidade e a confiabilidade das informações disponíveis.

A matriz de funcionalidades Vulkan deve apresentar duas dimensões independentes.

#### Dimensão A — Estado de suporte

| Estado         | Significado                                     |
| -------------- | ----------------------------------------------- |
| `SUPPORTED`    | Implementação confirmada para o escopo avaliado |
| `PARTIAL`      | Implementação incompleta ou limitada            |
| `UNSUPPORTED`  | Ausência de suporte confirmada                  |
| `NOT VERIFIED` | Estado ainda não determinado                    |

#### Dimensão B — Qualidade da evidência

| Estado       | Significado                             |
| ------------ | --------------------------------------- |
| `Confirmed`  | Evidência direta e verificável          |
| `Observed`   | Comportamento observado em uma execução |
| `Hypothesis` | Explicação ainda não comprovada         |
| `Unknown`    | Evidência insuficiente                  |

As duas dimensões devem ser registradas separadamente.

Exemplo ilustrativo:

| Feature   | Support status | Evidence     |
| --------- | -------------- | ------------ |
| Feature A | `SUPPORTED`    | `Confirmed`  |
| Feature B | `PARTIAL`      | `Observed`   |
| Feature C | `NOT VERIFIED` | `Hypothesis` |

Os valores acima são exemplos de preenchimento, não afirmações sobre funcionalidades reais do PanVK.

**Critérios de aceitação:**

- Toda avaliação distingue estado de suporte e qualidade da evidência.
- Uma hipótese não é convertida em estado de suporte.
- Um teste isolado não comprova suporte universal.
- O escopo da avaliação é registrado.

### Fase 3 — Formalizar a separação entre contrato Vulkan e implementação

**Objetivo:** estabelecer a hierarquia correta das evidências técnicas.

A skill deve distinguir quatro fontes:

| Fonte                | O que comprova                                  |
| -------------------- | ----------------------------------------------- |
| Especificação Vulkan | Contrato e comportamento exigidos pela API      |
| Código-fonte         | Comportamento implementado no código analisado  |
| Testes               | Comportamento exercitado nas condições do teste |
| Hardware             | Comportamento observado na plataforma testada   |

Regra fundamental:

> A especificação Vulkan define o comportamento exigido, mas não comprova que a implementação PanVK o atende.

Fluxo de rastreabilidade:

```text
Vulkan specification
        ↓
PanVK implementation
        ↓
Test coverage
        ↓
Hardware execution
```

Cada etapa exige evidência própria. A investigação deve relacionar o requisito da API à implementação, aos testes disponíveis e, quando aplicável, à execução em hardware.

**Critérios de aceitação:**

- A especificação não é usada como prova de implementação.
- Os testes não são tratados como prova de cobertura integral.
- Resultados de hardware identificam plataforma, geração, ambiente e condições de execução.
- Lacunas entre requisito, código, teste e hardware são registradas explicitamente.

### Fase 4 — Aprofundar a reconstrução do modelo de execução Mali

**Objetivo:** tornar a análise de CSF e JM dependente da implementação e da geração efetivamente investigadas.

A skill deve exigir a reconstrução do caminho de execução relevante.

Elementos a investigar, conforme aplicabilidade:

- Modelo de submissão.
- Estruturas de comandos.
- Interface entre userspace e kernel.
- UAPI utilizada.
- Filas e mecanismos de execução.
- Sincronização e dependências.
- Tratamento de erros.
- Relação com firmware.
- Particularidades da geração Mali.

Fluxo de referência:

```text
Vulkan command recording
        ↓
PanVK command construction
        ↓
Submission preparation
        ↓
Userspace/kernel interface
        ↓
CSF or JM execution model
        ↓
GPU execution
        ↓
Completion and synchronization
```

Não presumir que todas as gerações compartilham o mesmo caminho. Confirmar estruturas, interfaces e mecanismos no código e nas fontes correspondentes à plataforma avaliada.

**Critérios de aceitação:**

- CSF e JM são tratados como modelos de execução, não apenas como atributos de uma geração.
- A análise identifica a geração e o caminho efetivamente utilizados.
- Interfaces, estruturas e mecanismos são confirmados em fontes verificáveis.
- Diferenças entre gerações são registradas quando relevantes.

### Fase 5 — Ampliar a cobertura do inventário de recursos Vulkan

**Objetivo:** evitar lacunas no inventário de recursos Vulkan que podem ser relevantes para investigações específicas.

Adicionar ao inventário, quando aplicável:

| Área             | Recursos                                            |
| ---------------- | --------------------------------------------------- |
| Memória          | Sparse resources, external memory, protected memory |
| Sincronização    | External semaphore, external fence                  |
| Imagem e sampler | Sampler YCbCr conversion                            |
| Renderização     | Multiview, feedback loops                           |
| Robustez         | Robustness e recursos relacionados                  |

A inclusão desses itens não significa exigir sua implementação nem presumir que estejam disponíveis no PanVK.

Para cada recurso relevante, investigar:

1. Se o recurso pertence ao escopo da API e da versão avaliadas.
2. Se existe implementação no PanVK.
3. Se depende de extensões ou propriedades específicas.
4. Se depende de infraestrutura compartilhada.
5. Se existe cobertura de testes.
6. Se foi validado em hardware.
7. Quais limitações ou condições de uso foram identificadas.

**Critérios de aceitação:**

- Os recursos estão contemplados no inventário.
- Nenhum suporte é presumido pela simples inclusão na matriz.
- Recursos irrelevantes para uma tarefa podem ser marcados como não aplicáveis.
- Estado de suporte e evidência seguem a classificação definida na Fase 2.

### Fase 6 — Estruturar a classificação de falhas

**Objetivo:** evitar diagnósticos genéricos que misturam etapas diferentes do pipeline Vulkan.

A skill deve distinguir explicitamente:

| Categoria                    | Etapa                  |
| ---------------------------- | ---------------------- |
| Vulkan validation error      | Validação da API       |
| Shader compilation failure   | Compilação de shaders  |
| Command construction failure | Construção de comandos |
| Submission failure           | Submissão              |
| GPU execution error          | Execução na GPU        |
| Synchronization failure      | Sincronização          |
| Presentation failure         | WSI e apresentação     |

Para cada falha, registrar:

- Etapa em que ocorreu.
- Mensagem ou código de erro.
- Evidência reproduzível.
- Componentes envolvidos.
- Última etapa confirmada como bem-sucedida.
- Próxima etapa que falhou ou permaneceu desconhecida.
- Condições de reprodução e ambiente.
- Hipótese de causa raiz, separada dos fatos observados.

**Critérios de aceitação:**

- Cada diagnóstico possui uma categoria identificável.
- Falhas em etapas diferentes não são agrupadas sem justificativa.
- A causa raiz permanece hipótese até ser comprovada.
- A investigação identifica a última etapa bem-sucedida e a primeira etapa com falha observável.

### Fase 7 — Preparar patch revisável

**Objetivo:** consolidar os seis ajustes sem reescrever a skill.

Procedimento:

1. Preparar patch exclusivamente para `SKILL.md`.
2. Manter a organização atual do documento.
3. Inserir alterações nas seções correspondentes.
4. Evitar duplicação de regras existentes.
5. Preservar exemplos e decisões já aprovados.
6. Identificar o motivo de cada alteração.
7. Relacionar cada alteração ao ID correspondente da matriz de rastreabilidade.

**Critérios de aceitação:**

- Patch limitado ao arquivo autorizado.
- Todas as mudanças possuem justificativa rastreável.
- Nenhum conteúdo aprovado é removido sem necessidade.
- O diff é pequeno e focado nos seis ajustes.
- Nenhum arquivo de código ou outra skill aparece no patch.

### Fase 8 — Revisão técnica independente

**Objetivo:** verificar se o patch resolve os problemas identificados sem introduzir regressões.

A revisão deve avaliar:

1. Correção do roteamento entre skills.
2. Separação entre suporte e evidência.
3. Hierarquia das fontes de informação.
4. Precisão do modelo CSF/JM.
5. Cobertura do inventário Vulkan.
6. Classificação das falhas.
7. Consistência com a skill central `mesa3d-mali-expert`.
8. Compatibilidade com `kraid-compiler`.
9. Ausência de instruções contraditórias.
10. Ausência de expansão desnecessária do escopo.

**Critérios de aceitação:**

- Nenhum dos seis ajustes permanece incompleto.
- Nenhuma regressão documental é identificada.
- Afirmações técnicas novas possuem formulação verificável.
- Referências a outras skills refletem sua existência real.
- Problemas encontrados são registrados antes de qualquer aplicação.

### Fase 9 — Validação final e aprovação

**Objetivo:** entregar uma versão pronta para inclusão no projeto.

Validações:

- Frontmatter YAML válido.
- Markdown válido.
- Links relativos e referências corretos.
- Skills mencionadas verificadas.
- Matrizes consistentes.
- Terminologia uniforme.
- Nenhuma funcionalidade declarada como suportada sem evidência.
- Diff limitado ao arquivo autorizado.
- Conteúdo aprovado preservado.

Relatório final:

| Verificação               | Resultado esperado |
| ------------------------- | ------------------ |
| Integridade documental    | Aprovada           |
| Roteamento                | Aprovado           |
| Precisão técnica          | Aprovada           |
| Rastreabilidade           | Aprovada           |
| Consistência arquitetural | Aprovada           |
| Controle de escopo        | Aprovado           |

A inclusão no projeto ocorrerá somente após aprovação explícita do usuário.

## 4. Matriz de rastreabilidade

| ID  | Ajuste                               | Fase | Resultado esperado        |
| --- | ------------------------------------ | ---: | ------------------------- |
| A01 | Roteamento seguro entre skills       |    1 | Referências verificáveis  |
| A02 | Separação de suporte e evidência     |    2 | Matriz com duas dimensões |
| A03 | Contrato Vulkan versus implementação |    3 | Hierarquia de evidências  |
| A04 | Modelo de execução Mali              |    4 | Reconstrução CSF/JM       |
| A05 | Cobertura de recursos Vulkan         |    5 | Inventário ampliado       |
| A06 | Classificação de falhas              |    6 | Diagnóstico por etapa     |

## 5. Entregáveis

1. `SKILL.md` revisado, com os seis ajustes integrados.
2. Patch revisável.
3. Relatório de revisão técnica independente.
4. Relatório de validação final.
5. Matriz de rastreabilidade dos ajustes.

## 6. Critérios gerais de conclusão

A implementação estará concluída quando:

- Os seis ajustes estiverem incorporados.
- A estrutura original da skill estiver preservada.
- O conteúdo passar pela revisão técnica independente.
- A validação documental estiver aprovada.
- O patch estiver pronto para aplicação.
- O usuário tiver aprovado explicitamente a aplicação.

Não fazem parte desta execução:

- Alterações no código Mesa.
- Implementação de funcionalidades Vulkan.
- Mudanças no compilador Kraid.
- Criação ou modificação de outras skills.
- Alterações em kernel, firmware ou drivers.
- Commits ou integração sem autorização.

## 7. Ordem de execução

1. Preparação e inventário.
2. Roteamento entre skills.
3. Separação de suporte e evidência.
4. Contrato Vulkan e implementação.
5. Modelo de execução Mali.
6. Inventário de recursos Vulkan.
7. Classificação de falhas.
8. Preparação do patch.
9. Revisão técnica independente.
10. Validação final e aprovação.

## 8. Estado do plano

**Plano pronto para execução.**

Nenhum arquivo foi alterado. Nenhum patch foi aplicado. Nenhum commit foi realizado.

A próxima etapa é executar a Fase 0, confirmar o estado real do repositório e preparar as alterações como patch revisável. A aplicação continuará bloqueada até autorização explícita.
