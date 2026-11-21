# Plano de Execução — Consolidação Técnica da Skill `mali-kernel-platform`

## 1. Objetivo

Orientar um agente a produzir a documentação de consolidação técnica das investigações F0–F5.

O resultado será uma base documental verificável para:

- Preservar as evidências já coletadas.
- Consolidar descobertas e riscos.
- Registrar compatibilidade entre Kbase, Panthor, CSF e JM.
- Identificar contradições e lacunas.
- Orientar as investigações F6–F12.
- Definir os requisitos da skill `mali-kernel-platform`.

A documentação será submetida a uma auditoria independente após sua criação.

## 2. Separação das responsabilidades

### Etapa A — Geração documental

Responsável: agente executor.

O agente deve:

- Consultar as evidências disponíveis.
- Inventariar os documentos existentes.
- Analisar as fontes necessárias.
- Produzir os documentos solicitados.
- Verificar a consistência entre eles.
- Registrar dúvidas e limitações.

O agente não deve aprovar o próprio trabalho como tecnicamente correto.

### Etapa B — Auditoria independente

Responsável: agente revisor ou segunda execução independente.

O revisor deve:

- Conferir os documentos produzidos.
- Reexaminar as fontes originais.
- Verificar afirmações técnicas.
- Identificar omissões e contradições.
- Verificar a classificação das evidências.
- Avaliar se os documentos atendem aos requisitos.

A aprovação final depende dessa auditoria.

## 3. Restrições obrigatórias

1. Não modificar arquivos de código-fonte.
2. Não modificar arquivos em `work/`.
3. Não aplicar patches.
4. Não alterar patches existentes.
5. Não criar commits.
6. Não substituir documentos existentes sem autorização.
7. Não descartar conteúdo não rastreado.
8. Não transformar hipóteses em fatos.
9. Não declarar testes executados quando existirem apenas relatos históricos.
10. Não afirmar comportamento interno do kernel ou firmware sem evidência verificável.

Toda alteração documental deve ser isolada e revisável.

## 4. Fase A1 — Inventário documental

Antes de produzir qualquer arquivo:

1. Consultar `AGENTS.md`.
2. Identificar o estado do repositório, branch e revisão.
3. Inspecionar `git status`.
4. Inventariar integralmente `docs/engineering/`.
5. Identificar documentos existentes relacionados à skill.
6. Identificar referências e worklogs utilizados nas fases F0–F5.
7. Registrar documentos ausentes, duplicados ou incompletos.

**Critério de saída:** inventário concluído, sem sobrescrever ou descartar conteúdo existente.

## 5. Fase A2 — Organização das evidências

Classificar cada evidência por:

- Identificador único.
- Área técnica.
- Afirmação sustentada.
- Fonte original.
- Revisão ou commit, quando disponível.
- Arquivo e localização.
- Tipo de evidência.
- Grau de confirmação.
- Limitações.
- Fase de investigação relacionada.

Usar as seguintes classificações:

| Classificação            | Significado                                   |
| ------------------------ | --------------------------------------------- |
| Confirmado estaticamente | Verificado diretamente no código ou documento |
| Reproduzido              | Comportamento reproduzido em experimento      |
| Build validado           | Compilação executada e resultado registrado   |
| Hardware validado        | Teste executado em dispositivo identificado   |
| Relato histórico         | Resultado informado por terceiros ou worklog  |
| Hipótese                 | Explicação ainda não demonstrada              |
| Desconhecido             | Evidência insuficiente                        |

Não elevar o grau de confirmação sem nova evidência.

## 6. Fase A3 — Produção dos documentos

Criar os documentos abaixo, respeitando o conteúdo e os arquivos já existentes.

### 6.1 `TECHNICAL_BASELINE.md`

Registrar:

- Objetivo e escopo da skill.
- Arquitetura técnica investigada.
- Fronteiras userspace, kernel e firmware.
- Diferenças entre Kbase e Panthor.
- Diferenças entre CSF e JM.
- Plataformas e arquiteturas examinadas.
- Proveniência das implementações.
- Limitações da investigação.
- Estado consolidado de F0–F5.

### 6.2 `EVIDENCE_REGISTER.md`

Registrar as evidências técnicas individualmente.

Cada registro deve permitir localizar a fonte e reproduzir a verificação quando possível.

Não utilizar referências vagas como "código analisado" ou "documentação pública".

### 6.3 `FINDINGS_REGISTER.md`

Registrar:

- Problemas confirmados.
- Inconsistências estruturais.
- Regressões.
- Riscos potenciais.
- Limitações arquiteturais.
- Questões sem resposta.

Cada achado deve possuir:

- ID.
- Descrição.
- Evidência.
- Impacto conhecido.
- Escopo.
- Grau de confiança.
- Estado.
- Investigação necessária.

### 6.4 `COMPATIBILITY_MATRIX.md`

Consolidar a compatibilidade por:

- Backend.
- Arquitetura GPU.
- CSF ou JM.
- Versão UAPI.
- Layout de estruturas.
- IOCTLs.
- Recursos disponíveis.
- Evidência de compatibilidade.
- Limitações e exceções.

Não generalizar resultados de um dispositivo para outros.

### 6.5 `RISK_REGISTER.md`

Registrar riscos com:

- ID.
- Descrição.
- Impacto.
- Probabilidade, quando estimável.
- Abrangência.
- Evidência.
- Prioridade.
- Mitigação recomendada.
- Estado.

Separar gravidade técnica de grau de confiança.

### 6.6 `INVESTIGATION_BACKLOG.md`

Registrar as investigações restantes de F6–F12.

Para cada item:

- Objetivo.
- Justificativa.
- Dependências.
- Evidências necessárias.
- Procedimento de investigação.
- Critério de conclusão.

### 6.7 `SKILL_REQUIREMENTS.md`

Transformar as conclusões em requisitos operacionais da skill.

Incluir:

- Regras de análise.
- Procedimentos de investigação.
- Separação de responsabilidades.
- Tratamento de UAPI e ABI.
- Análise de memória e sincronização.
- Compatibilidade entre arquiteturas.
- Classificação de evidências.
- Validação.
- Segurança e integridade do repositório.
- Critérios para preparar patches.

Não escrever ainda o `SKILL.md` definitivo nesta etapa.

## 7. Fase A4 — Verificação de consistência

Após produzir os documentos, o agente executor deve verificar:

1. Todos os IDs citados existem.
2. Todas as afirmações técnicas relevantes possuem referências.
3. As referências apontam para fontes reais.
4. As matrizes não contradizem os registros de evidências.
5. Os riscos não apresentam hipóteses como fatos.
6. Os resultados de hardware não são confundidos com testes de build.
7. Os worklogs históricos mantêm sua proveniência.
8. As limitações estão explícitas.
9. Não há duplicação desnecessária.
10. Nenhum documento existente foi perdido.

Produzir um relatório de autocheck separado da documentação técnica.

## 8. Fase B — Auditoria independente

O revisor deverá executar as seguintes verificações:

### B1. Integridade documental

- Verificar os sete documentos.
- Verificar estrutura, completude e consistência.
- Identificar conteúdo duplicado ou ausente.

### B2. Rastreabilidade

- Selecionar afirmações técnicas e localizar suas fontes.
- Conferir arquivos, revisões e trechos.
- Verificar se a fonte realmente sustenta a afirmação.

### B3. Correção técnica

- Reexaminar os achados prioritários.
- Verificar a separação Kbase/Panthor.
- Verificar a separação CSF/JM.
- Conferir compatibilidade UAPI e layouts.
- Revisar os achados de DMA-BUF e sync_file.
- Revisar os resultados Android e WSI.

### B4. Classificação das evidências

- Identificar afirmações sem comprovação.
- Reclassificar relatos históricos.
- Verificar hipóteses apresentadas como conclusões.
- Identificar conclusões que extrapolam os dispositivos examinados.

### B5. Cobertura

- Verificar se F0–F5 estão representadas.
- Verificar se F6–F12 estão corretamente identificadas como pendentes.
- Verificar se os requisitos da skill cobrem os problemas encontrados.

### B6. Relatório de auditoria

Produzir um relatório independente com:

| Resultado | Significado                |
| --------- | -------------------------- |
| PASS      | Requisito atendido         |
| PARTIAL   | Atendido parcialmente      |
| FAIL      | Requisito não atendido     |
| BLOCKED   | Não foi possível verificar |

Cada falha deve conter:

- Documento afetado.
- Localização.
- Problema encontrado.
- Evidência.
- Correção recomendada.

## 9. Critérios de aprovação

A consolidação só será aprovada quando:

- Os sete documentos estiverem completos.
- As afirmações técnicas relevantes forem rastreáveis.
- Não existirem contradições críticas sem registro.
- As classificações de evidência estiverem corretas.
- As limitações estiverem explícitas.
- A matriz de compatibilidade estiver fundamentada.
- O backlog representar corretamente as fases pendentes.
- Os requisitos da skill forem coerentes com a governança global.
- A auditoria independente não apresentar falhas críticas.

Falhas não críticas devem ser registradas e corrigidas antes do encerramento.

## 10. Entregáveis

```text
docs/engineering/mali-kernel-platform/
├── TECHNICAL_BASELINE.md
├── EVIDENCE_REGISTER.md
├── FINDINGS_REGISTER.md
├── COMPATIBILITY_MATRIX.md
├── RISK_REGISTER.md
├── INVESTIGATION_BACKLOG.md
├── SKILL_REQUIREMENTS.md
└── audit/
    └── CONSOLIDATION_AUDIT.md
```

O relatório de autocheck do executor deve ser separado do relatório de auditoria independente.

## 11. Estado final esperado

Ao concluir:

- F0–F5 estarão consolidadas documentalmente.
- As evidências terão rastreabilidade.
- Os problemas conhecidos estarão registrados.
- Os riscos estarão classificados.
- F6–F12 terão um backlog técnico organizado.
- A skill terá requisitos documentais definidos.
- A qualidade da documentação terá sido verificada independentemente.

A criação dos documentos não significa que a skill esteja concluída ou que os problemas registrados tenham sido corrigidos.

**Aprovação final:** somente após revisão do usuário e encerramento das falhas identificadas na auditoria.
