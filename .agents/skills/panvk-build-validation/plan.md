# Plano de Correção e Atualização — `panvk-build-validation`

## 1. Objetivo

Atualizar a skill existente para refletir a arquitetura atual do projeto Mesa 27 com Kraid integrado e orientar diretamente o agente na preparação, compilação, inspeção, validação e diagnóstico do PanVK.

O trabalho deve preservar os procedimentos válidos e corrigir apenas conteúdo desatualizado, incompleto ou incompatível com o estado atual do projeto.

## 2. Escopo congelado

### Plataforma principal

- GPU: Mali-G615 MC2.
- Dispositivo físico: Motorola Moto G86.
- SoC: MediaTek MT6878.
- Sistema: Android 16, sujeito à confirmação do ambiente atual.
- Mesa: 27.0.0-devel.
- Backend: Kraid integrado e padrão.
- Ambiente Android: Bionic.
- Ambiente complementar: Linux glibc.

### Restrições

- Não ampliar a matriz para outras GPUs ou dispositivos.
- Não tratar resultados históricos de outras GPUs como validação do Moto G86.
- Não reconstruir scripts existentes.
- Não modificar diretamente a fonte original em `work/`.
- Não aplicar patches sem autorização.
- Não executar testes físicos sem autorização.
- Não criar commits sem autorização.

## 3. Fase 0 — Inventário direcionado

**Objetivo:** conhecer a implementação atual e identificar exatamente o que precisa mudar.

### Arquivos a examinar

1. `.agents/skills/panvk-build-validation/SKILL.md`
2. `.agents/skills/panvk-build-validation/references/workflow.md`
3. Scripts de build e validação referenciados.
4. Perfis de plataforma e configuração.
5. `sources.lock` e metadados de patch.
6. Testes automatizados e logs existentes.
7. Documentação de baseline e validação.

### Atividades

- Verificar se cada referência existe.
- Identificar comandos realmente utilizados.
- Conferir parâmetros e dependências dos scripts.
- Identificar requisitos históricos.
- Separar procedimentos válidos de procedimentos desatualizados.
- Identificar funcionalidades que ainda não possuem instruções operacionais.

### Entrega

Inventário com três classificações:

| Classificação | Tratamento                             |
| ------------- | -------------------------------------- |
| Válido        | Preservar                              |
| Desatualizado | Corrigir                               |
| Ausente       | Complementar somente quando necessário |

Não repetir testes que já possuem evidências válidas.

## 4. Fase 1 — Atualização da SKILL.md

**Objetivo:** atualizar as instruções centrais sem perder sua objetividade.

### 4.1 Metadados

Atualizar a descrição para representar:

- Mesa 27.
- Kraid integrado.
- PanVK.
- Build Android/Bionic.
- Build Linux glibc.
- Mali G15.
- Moto G86 MC2.
- Diagnóstico e validação de artefatos e runtime.

Remover referências a uma migração futura ou baseline anterior à migração.

### 4.2 Método operacional

Preservar e aprimorar os cinco princípios existentes:

1. Delimitar a falha.
2. Preservar o contexto.
3. Isolar uma causa por vez.
4. Utilizar os scripts do projeto.
5. Validar o resultado exato.

Adicionar instruções concretas para:

- Selecionar o ambiente correto.
- Selecionar o perfil correto.
- Preparar o build.
- Executar a compilação.
- Inspecionar artefatos.
- Executar os testes disponíveis.
- Interpretar resultados.
- Registrar evidências.

### 4.3 Roteamento

Definir responsabilidades:

- `mesa3d-mali-expert`: orientação geral e encaminhamento especializado.
- `panfrost-panvk`: implementação e arquitetura PanVK/Panfrost.
- `mali-kernel-platform`: Kbase, UAPI, ABI, CSF e plataforma.
- `panvk-build-validation`: compilação, empacotamento, testes e validação.

Evitar duplicação de conteúdo entre as skills.

## 5. Fase 2 — Atualização do workflow

**Objetivo:** transformar `references/workflow.md` em um procedimento executável.

### 5.1 Preparação

Documentar:

- Verificação do estado Git.
- Identificação da revisão Mesa.
- Verificação da árvore de origem.
- Verificação do perfil.
- Verificação do `patchSeriesId`.
- Verificação das ferramentas disponíveis.
- Preservação de alterações locais.

### 5.2 Build Android/Bionic

Documentar o fluxo efetivo:

1. Preparar os inputs.
2. Verificar o NDK selecionado.
3. Configurar Meson e cross-file.
4. Verificar dependências host e target.
5. Compilar.
6. Inspecionar os artefatos.
7. Registrar os resultados.

O NDK r30 somente será mantido como requisito obrigatório se os scripts e a configuração atual confirmarem essa exigência.

### 5.3 Build Linux glibc

Adicionar ou atualizar o fluxo correspondente:

1. Identificar o ambiente Linux.
2. Verificar compilador e dependências.
3. Preparar configuração Meson.
4. Compilar o PanVK.
5. Inspecionar bibliotecas e dependências.
6. Executar os testes disponíveis.
7. Registrar os resultados.

Não presumir que os mesmos parâmetros Android funcionam em glibc.

### 5.4 Inspeção dos artefatos

Manter e complementar os procedimentos para:

- ELF.
- Arquitetura AArch64.
- Notas e dependências.
- Símbolos.
- Bibliotecas.
- Integridade de pacotes.
- SHA-256.
- Correspondência entre o binário validado e o pacote distribuído.

### 5.5 Diagnóstico

Para cada falha, fornecer:

- Sintoma.
- Componente responsável.
- Evidência necessária.
- Procedimento de diagnóstico.
- Correção aplicável quando conhecida.
- Validação após a correção.

Não transformar problemas conhecidos em roteiros genéricos de investigação.

## 6. Fase 3 — Atualização dos gates

**Objetivo:** alinhar os critérios de aprovação à arquitetura atual.

| Gate         | Critério                                                       |
| ------------ | -------------------------------------------------------------- |
| Proveniência | Revisão Mesa, perfil, fontes e patch series coerentes          |
| Toolchain    | Compiladores, NDK, sysroot e dependências corretos para o alvo |
| Build        | Compilação concluída e artefatos esperados produzidos          |
| ELF          | Arquitetura, formato, dependências e símbolos corretos         |
| Pacote       | Integridade, conteúdo e hashes correspondentes                 |
| Runtime      | Driver correto carregado e testes funcionais aprovados         |
| Estabilidade | Ausência de falhas nas verificações executadas                 |
| Desempenho   | Resultados reproduzíveis e comparáveis                         |

Cada gate deverá possuir:

- Pré-condições.
- Comando ou procedimento.
- Critério objetivo de aprovação.
- Evidência esperada.
- Ação em caso de falha.

Manter os estados:

- `PASS`
- `FAIL`
- `BLOQUEADO`
- `NÃO EXECUTADO`

Um gate aprovado não implica aprovação dos gates seguintes.

## 7. Fase 4 — Atualização da validação funcional

**Objetivo:** orientar os testes de funcionamento do PanVK.

Cobertura prevista:

- Inicialização Vulkan.
- Descoberta do dispositivo.
- Compute.
- Renderização.
- Memória GPU.
- DMA-BUF.
- Sincronização.
- CSF.
- WSI Android.
- AHardwareBuffer.
- Compatibilidade Linux glibc.

Para cada teste, registrar:

1. Componente validado.
2. Pré-condições.
3. Procedimento.
4. Resultado esperado.
5. Evidência.
6. Limitações conhecidas.

O teste `compute = 0x12345678 em 10/10` somente permanecerá como critério obrigatório se sua aplicabilidade e seus resultados forem confirmados para o Moto G86 MC2.

## 8. Fase 5 — Atualização da baseline e dos perfis

**Objetivo:** eliminar referências incorretas à plataforma anterior.

Atividades:

- Verificar a origem do perfil `g615-v11-csf`.
- Confirmar se ele representa a Mali-G615 MC2 do Moto G86.
- Identificar configurações específicas da plataforma.
- Separar dados históricos de dados atuais.
- Atualizar a identificação da baseline.
- Preservar evidências anteriores sem reclassificá-las como testes do Moto G86.

Não substituir ou reescrever registros históricos.

## 9. Fase 6 — Auditoria operacional

**Objetivo:** comprovar que a skill orienta o agente corretamente.

Realizar exercícios controlados:

1. Preparar um build Android.
2. Preparar um build Linux glibc.
3. Diagnosticar uma falha de compilação.
4. Inspecionar um ELF.
5. Validar um pacote.
6. Planejar um teste funcional.
7. Analisar uma regressão.

Verificar se o agente consegue:

- Identificar os scripts corretos.
- Selecionar o ambiente correto.
- Executar os procedimentos documentados.
- Interpretar os resultados.
- Identificar evidências ausentes.
- Relatar limitações corretamente.

Os exercícios podem usar logs e artefatos existentes. Não exigem execução física nem alterações no driver.

## 10. Fase 7 — Homologação

**Objetivo:** finalizar a atualização.

Atividades:

1. Corrigir as falhas encontradas.
2. Eliminar instruções duplicadas.
3. Verificar todos os caminhos.
4. Conferir comandos e parâmetros.
5. Conferir coerência entre `SKILL.md` e `workflow.md`.
6. Revisar critérios de aprovação.
7. Apresentar o diff completo.
8. Solicitar aprovação final.

## 11. Critérios de aceitação

- [ ] Skill original preservada.
- [ ] Referências à migração futura removidas.
- [ ] Mesa 27 e Kraid integrado corretamente representados.
- [ ] Perfil de hardware corretamente identificado.
- [ ] Android/Bionic documentado.
- [ ] Linux glibc documentado.
- [ ] Scripts existentes aproveitados.
- [ ] Procedimentos de build executáveis.
- [ ] Inspeção de artefatos documentada.
- [ ] Gates objetivos e independentes.
- [ ] Testes funcionais corretamente classificados.
- [ ] Evidências históricas preservadas.
- [ ] Nenhuma validação de outra GPU atribuída ao Moto G86.
- [ ] Auditoria operacional aprovada.

## 12. Resultado esperado

Uma skill capaz de conduzir o agente diretamente pelo processo:

**Preparação → Build → Inspeção → Empacotamento → Testes → Diagnóstico → Validação → Relatório.**

A skill deverá utilizar o conhecimento e as ferramentas existentes, sem repetir investigações ou reconstruir infraestrutura.

A conclusão da atualização não significa que todos os testes físicos foram executados. Cada capacidade deverá manter seu estado real de validação.

### Regra de execução

Primeiro inventariar. Depois produzir somente os patches necessários. Revisar o diff. Validar as alterações documentais e operacionais. Solicitar aprovação antes de aplicar os patches.
