# Plano de Geração — Skill `gpu-testing-profiling`

## 1. Objetivo

Criar uma skill especializada em testes e profiling de GPU para o projeto Mesa/Kraid.

A skill deverá orientar diretamente o agente a:

- Executar testes funcionais de GPU.
- Detectar regressões.
- Preparar e executar benchmarks.
- Coletar métricas de desempenho.
- Analisar gargalos.
- Avaliar otimizações.
- Comparar resultados entre versões.
- Produzir relatórios técnicos reproduzíveis.

O objetivo não é ensinar genericamente como investigar desempenho. É fornecer procedimentos concretos para executar e avaliar o trabalho.

## 2. Escopo congelado

### Plataforma principal

- GPU: Mali-G615 MC2.
- Dispositivo: Motorola Moto G86.
- SoC: MediaTek MT6878.
- Sistema: Android 16, sujeito à confirmação do ambiente.
- Mesa: 27.0.0-devel.
- Backend: Kraid integrado.
- Ambiente complementar: Linux glibc.

Outras GPUs e dispositivos ficam fora da matriz ativa de validação.

Resultados históricos de outras plataformas podem ser utilizados como referência, mas não como comprovação de desempenho do Moto G86.

### Restrições

- Não modificar código do Mesa durante a geração da skill.
- Não executar testes físicos sem autorização.
- Não criar benchmarks ou scripts duplicados.
- Não inventar métricas ou disponibilidade de contadores.
- Não apresentar estimativas como medições.
- Não declarar otimização sem comparação reproduzível.
- Não criar commits sem autorização explícita.

## 3. Fase 0 — Inventário técnico

**Objetivo:** identificar os recursos de testes e profiling já existentes.

### Fontes a examinar

- `.agents/skills/gpu-testing-profiling/`, caso já exista.
- Scripts de benchmark e testes.
- Ferramentas de profiling.
- Testes Vulkan e PanVK.
- Logs e resultados históricos.
- Perfis de hardware.
- Documentos de baseline.
- Procedimentos de coleta de métricas.
- Ferramentas disponíveis no Moto G86.

### Atividades

1. Identificar ferramentas existentes.
2. Identificar testes automatizados.
3. Identificar benchmarks disponíveis.
4. Identificar métricas que podem ser coletadas.
5. Identificar procedimentos reproduzíveis.
6. Separar resultados confirmados de hipóteses.
7. Identificar lacunas que impedem instruções operacionais.

**Entrega:** inventário de recursos reutilizáveis.

Não repetir testes ou investigações que já possuem evidências suficientes.

## 4. Fase 1 — Testes funcionais e regressões

**Objetivo:** orientar a validação do comportamento da GPU.

A skill deverá fornecer procedimentos para:

### 4.1 Inicialização e funcionamento

- Inicialização Vulkan.
- Descoberta da GPU.
- Carregamento do driver.
- Criação de dispositivos e filas.
- Execução de comandos.
- Submissão e conclusão de trabalhos.

### 4.2 Testes funcionais

- Compute.
- Renderização.
- Transferência de buffers.
- Gerenciamento de memória.
- DMA-BUF.
- Sincronização.
- CSF.
- WSI Android.
- AHardwareBuffer.

### 4.3 Regressões

Orientar o agente a:

1. Selecionar o teste correspondente à funcionalidade alterada.
2. Preparar uma execução reproduzível.
3. Registrar a identidade do binário.
4. Executar o teste.
5. Comparar com a baseline.
6. Classificar o resultado.
7. Registrar evidências.

**Entrega:** procedimentos operacionais de testes funcionais e regressão.

## 5. Fase 2 — Benchmarking

**Objetivo:** medir o desempenho de forma reproduzível.

A skill deverá orientar:

### 5.1 Preparação

- Identificação do hardware.
- Identificação do driver e versão Mesa.
- Identificação do workload.
- Preparação do ambiente.
- Controle das condições de execução.
- Definição da baseline.

### 5.2 Execução

- Benchmarks Vulkan.
- Workloads de compute.
- Workloads gráficos.
- Testes de transferência de memória.
- Testes de submissão de comandos.
- Testes de carga prolongada.

### 5.3 Métricas

Quando disponíveis, coletar:

- Tempo de execução.
- FPS e frame time.
- Latência.
- Throughput.
- Utilização da GPU.
- Frequência.
- Temperatura.
- Consumo energético.
- Uso de memória.
- Bandwidth.
- Variabilidade entre execuções.

A disponibilidade de cada métrica deverá ser confirmada para a plataforma.

**Entrega:** procedimentos de benchmark e coleta de resultados.

## 6. Fase 3 — Profiling e análise de gargalos

**Objetivo:** orientar a identificação de limitações de desempenho.

Domínios:

### 6.1 GPU

- Utilização dos mecanismos de execução.
- Ocupação.
- Latência de execução.
- Throughput.
- Limitações de processamento.

### 6.2 CPU e submissão

- Overhead de submissão.
- Preparação de comandos.
- Sincronização CPU/GPU.
- Esperas e bloqueios.
- Custo de gerenciamento de filas.

### 6.3 Memória

- Alocações.
- Mapeamentos.
- DMA-BUF.
- Transferências.
- Bandwidth.
- Pressão de memória.

### 6.4 CSF

- Submissão de trabalhos.
- Filas.
- Queue groups.
- Sincronização.
- Esperas.
- Latência entre submissão e execução.

### 6.5 Diagnóstico

Para cada domínio, a skill deverá orientar:

1. Qual métrica observar.
2. Qual ferramenta utilizar.
3. Como coletar os dados.
4. Como interpretar os resultados.
5. Como diferenciar gargalos.
6. Quais componentes podem estar envolvidos.
7. Como confirmar a hipótese com uma medição adicional.

**Entrega:** procedimentos de profiling e diagnóstico de gargalos.

## 7. Fase 4 — Avaliação de otimizações

**Objetivo:** verificar se uma alteração realmente melhora o desempenho.

A skill deverá estabelecer o seguinte fluxo:

1. Registrar a baseline.
2. Identificar o comportamento que será otimizado.
3. Selecionar o benchmark correspondente.
4. Registrar as condições de execução.
5. Medir o comportamento anterior.
6. Executar a versão modificada.
7. Repetir as medições.
8. Comparar os resultados.
9. Verificar regressões funcionais.
10. Classificar o resultado.

### Critérios

- Melhoria reproduzível.
- Ausência de regressão funcional.
- Ausência de degradação relevante em outros workloads.
- Variação estatística documentada.
- Evidências suficientes para justificar a conclusão.

Uma otimização não será considerada aprovada apenas porque uma execução apresentou resultado melhor.

**Entrega:** procedimento de avaliação comparativa de otimizações.

## 8. Fase 5 — Baseline e histórico de desempenho

**Objetivo:** estabelecer rastreabilidade entre versões.

Cada execução deverá registrar:

- Identificação do dispositivo.
- GPU e SoC.
- Sistema operacional.
- Revisão Mesa.
- Identificação do Kraid.
- Identidade do binário.
- Configuração do benchmark.
- Condições de execução.
- Métricas coletadas.
- Resultado.
- Logs e evidências.

Os resultados deverão ser organizados para permitir comparações futuras.

A baseline do Moto G86 deverá ser independente dos resultados históricos do Poco X6 Pro e de outras plataformas.

**Entrega:** formato de registro e comparação de desempenho.

## 9. Fase 6 — Construção da skill

**Objetivo:** transformar os procedimentos em instruções operacionais.

### Organização proposta

```text
.agents/skills/gpu-testing-profiling/
├── SKILL.md
└── references/
    ├── functional-testing.md
    ├── benchmarking.md
    ├── profiling.md
    ├── bottleneck-analysis.md
    ├── optimization-validation.md
    └── performance-baseline.md
```

### Responsabilidades da SKILL.md

A entrada principal deverá:

- Definir quando utilizar a skill.
- Identificar os tipos de tarefa.
- Direcionar para os procedimentos adequados.
- Definir regras de coleta de evidências.
- Estabelecer critérios de aprovação.
- Definir o formato dos relatórios.

Os documentos especializados deverão conter procedimentos concretos.

Não duplicar informações já mantidas nas outras skills.

## 10. Fase 7 — Auditoria operacional

**Objetivo:** verificar se o agente consegue utilizar a skill sem redescobrir os procedimentos.

Exercícios controlados:

1. Planejar e executar um teste funcional usando evidências disponíveis.
2. Preparar um benchmark reproduzível.
3. Interpretar resultados de frame time.
4. Identificar um possível gargalo de memória.
5. Analisar um problema de sincronização.
6. Comparar duas versões do driver.
7. Avaliar uma otimização com dados de referência.

A auditoria deverá verificar:

- Seleção correta dos testes.
- Escolha adequada das métricas.
- Uso correto das ferramentas.
- Interpretação dos resultados.
- Separação entre fatos e hipóteses.
- Identificação de regressões.
- Qualidade dos relatórios.

Os exercícios podem utilizar logs, dados e resultados existentes. Testes físicos dependem de autorização.

**Entrega:** relatório de auditoria operacional.

## 11. Fase 8 — Correção e homologação

**Objetivo:** finalizar a skill.

Atividades:

1. Corrigir instruções insuficientes.
2. Eliminar duplicações.
3. Conferir ferramentas e comandos.
4. Conferir referências.
5. Verificar os critérios de aceitação.
6. Revisar a cobertura técnica.
7. Apresentar o diff completo.
8. Solicitar aprovação final.

**Entrega:** `gpu-testing-profiling` pronta para homologação.

## 12. Critérios de aceitação

- [ ] Escopo restrito à Mali-G615 MC2.
- [ ] Moto G86 definido como plataforma física de referência.
- [ ] Testes funcionais documentados.
- [ ] Procedimentos de regressão definidos.
- [ ] Benchmarks reproduzíveis.
- [ ] Métricas identificadas e classificadas.
- [ ] Profiling documentado por domínio.
- [ ] Diagnóstico de gargalos operacional.
- [ ] Avaliação de otimizações definida.
- [ ] Baseline e histórico rastreáveis.
- [ ] Resultados históricos corretamente classificados.
- [ ] Nenhuma métrica presumida como disponível.
- [ ] Auditoria operacional aprovada.

## 13. Resultado esperado

A skill deverá permitir que o agente conduza diretamente:

**Testar → Medir → Coletar → Analisar → Identificar gargalos → Otimizar → Comparar → Validar.**

O agente deverá receber uma tarefa de desempenho e saber quais testes executar, quais métricas coletar, como interpretar os resultados e como comprovar uma melhoria.

A investigação será necessária somente quando os dados disponíveis não permitirem uma conclusão técnica segura.

### Regra final

A skill deve transformar conhecimento de testes e desempenho em procedimentos executáveis, não em uma lista de ferramentas ou assuntos que o desenvolvedor precisa pesquisar.
