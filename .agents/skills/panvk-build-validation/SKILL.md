---
name: panvk-build-validation
description: "Use para preparar, compilar, inspecionar e diagnosticar PanVK Mesa 27 com Kraid integrado, em Android/Bionic e Linux/glibc. Escopo G15 do plano: Moto G86 Mali-G615 MC2, PAN_ARCH 11 e Kbase CSF. Separa proveniência, build, pacote e validação funcional."
---

# Diagnóstico e validação do build PanVK

Use esta skill para o PanVK da revisão fixada em [sources.lock](../../../sources.lock), atualmente Mesa `27.0.0-devel`, em Android/Bionic e Linux/glibc. Kraid está integrado, mas sua seleção padrão é Android; glibc permanece opt-in.

O alvo documental é Moto G86 / Mali-G615 MC2. O rótulo G15 do plano não substitui `PAN_ARCH=11`. O único perfil aceito pelos scripts, [g615-v11-csf](../../../profiles/g615-v11-csf.json), ainda identifica o Poco X6 Pro MC6: não copie sua máscara de cores, kernel, permissões ou resultados para o Moto. Confirme a identidade atual antes de execução física; dados desconhecidos ficam `BLOQUEADO`, sem impedir a preparação documental.

## Roteamento

- [mesa3d-mali-expert](../mesa3d-mali-expert/SKILL.md): orientação geral e encaminhamento.
- [kraid-compiler](../kraid-compiler/SKILL.md): tradução NIR, IR, legalização, scheduling, alocação e codegen.
- [panfrost-panvk](../panfrost-panvk/SKILL.md): implementação e arquitetura PanVK/Panfrost.
- [mali-kernel-platform](../mali-kernel-platform/SKILL.md): Kbase, UAPI/ABI, CSF, memória e plataforma.
- Esta skill: preparação, compilação, empacotamento, inspeção, seleção dos testes e classificação das evidências.

## Método

1. **Delimite a falha.** Identifique ICD Bionic, ICD glibc ou aplicativo, host, fase e critério de aceite. Consulte scripts e logs locais antes de escolher o procedimento do [workflow](./references/workflow.md). Não presuma versões, flags, GPU, UAPI ou sucesso.
2. **Preserve o contexto.** Confira mudanças locais, perfil, pin Mesa, `patchSeriesId` e variante aplicada. Prepare uma cópia descartável com os inputs pretendidos; exportar `HEAD` omite mudanças locais. Não edite a fonte original em `work/` nem execute nela scripts que limpam ou redefinem a árvore.
3. **Isole uma causa por vez.** Cite o primeiro erro causal, arquivo ou comando e evidência. Altere uma variável e repita somente o gate afetado, com `BDIR` novo quando a configuração cross mudar. Se o teste não reduzir o domínio da falha, pare de alternar flags e reduza o caso.
4. **Use os scripts do projeto.** Selecione perfil, NDK/toolchain e dependências do alvo explicitamente. Não instale pacotes avulsos nem edite o Mesa extraído. Prepare patches na família correta; aplicação exige autorização, árvore descartável e verificação sem offset/fuzz. `--with-kbase-sync` permanece opt-in, somente G615.
5. **Valide o resultado exato.** Inspecione ELF, dependências, símbolos e identidade antes de empacotar. Selecione somente os testes afetados e registre evidências por gate. Não execute builds ou testes físicos apenas para atualizar documentação; reutilize registros com sua identidade e limitações originais. Testes físicos exigem autorização.

## Gates

Use `PASS`, `FAIL`, `BLOQUEADO` e `NÃO EXECUTADO` separadamente. Um gate aprovado não aprova o seguinte; compilação, símbolos, enumeração e ZIP íntegro não provam runtime.

| Gate | Critério |
|---|---|
| Proveniência | Pin, perfil e hash de inputs coerentes; aplicação comprovada separadamente pelo manifesto da variante e log sem drift. |
| Toolchain | Compiladores, sysroot, ferramentas host e dependências target identificados e separados. |
| Build | Compilação/link concluídos e artefatos esperados produzidos no destino registrado. |
| ELF | ELF64 AArch64, ABI, dependências, exports e notas pertinentes verificados; o script sozinho não cobre todos esses critérios. |
| Pacote | Conteúdo e metadados corretos, ZIP íntegro e bytes/SHA-256 iguais aos do ICD inspecionado. |
| Runtime | ICD exato carregado; resultados funcionais completos para o teste, ambiente e dispositivo declarados. |
| Estabilidade | Sem crash, hang, device-lost ou corrupção nos ciclos e limites executados, sem extrapolar a cobertura. |
| Desempenho | Comparação reproduzível da mesma carga/dispositivo/configuração; sem alegar ganho por build ou enumeração. |

O [roteiro operacional](./references/workflow.md) define pré-condições, comandos, evidências e ações por gate. O compute `0x12345678` em 10/10 continua disponível como smoke test; não é uma baseline Moto homologada pela evidência MC6.

## Entrega

Reporte diagnóstico, ação, resultados por gate e próximo passo verificável. Registre perfil, revisão Mesa, `patchSeriesId`, variante/manifesto, host, toolchain, API, Build ID e SHA-256, além de dispositivo e ambiente quando houver runtime. Separe fatos atuais, relatos históricos, hipóteses e desconhecidos; declare o que não foi executado. Patches e aprovação antes da aplicação são exigidos para alterações no driver Mesa; nos demais arquivos, edite diretamente e revise o diff. Não crie commits ou publique sem autorização.
