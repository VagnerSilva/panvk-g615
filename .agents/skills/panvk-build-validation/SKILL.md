---
name: panvk-build-validation
description: "Use para diagnosticar issues de build limpo Android do PanVK, NDK r30, bindgen, headers X11/XCB, patchSeriesId, ELF AArch64, ZIP ADPKG, smoke tests Mali-G615 e baseline antes da migração. Separa evidência de build, pacote e hardware."
---

# Diagnóstico e validação do build PanVK

Use esta skill para reproduzir, corrigir ou validar o fluxo Android/Bionic do perfil `g615-v11-csf`. Para questões internas de Mesa, Kraid ou CSF, consulte a [skill especialista](../mesa3d-mali-expert/SKILL.md).

## Método

1. **Delimite a falha.** Identifique o alvo (ICD, aplicativo ou glibc), a fase e o critério de aceite. Consulte primeiro os scripts e os logs locais. Não presuma versões, flags, GPU, UAPI ou sucesso.
2. **Preserve o contexto.** Confira mudanças locais, perfil, pin Mesa e patch series. Prepare uma cópia descartável que inclua os inputs pretendidos. Uma exportação de `HEAD` não inclui mudanças locais. Não edite a fonte original em `work/` nem execute nela scripts que limpam ou redefinem a árvore.
3. **Isole uma causa por vez.** Cite o primeiro erro causal, o arquivo ou comando e a evidência. Altere uma variável e repita apenas o gate afetado, em um diretório de build novo quando a configuração cross mudar. Se o teste não reduzir o domínio da falha, pare de alternar flags e reduza o caso.
4. **Use os scripts do projeto.** Não instale pacotes avulsos nem reutilize um NDK do host sem registrar sua origem. Não edite o Mesa extraído. Para mudanças no driver, use a família de patches correta, valide a aplicação sem offset/fuzz e revise o diff resultante.
5. **Valide o resultado exato.** Separe `PASS`, `FAIL`, `BLOQUEADO` e `NÃO EXECUTADO` por gate. Não infira runtime a partir de compilação, exportação de símbolos, enumeração ou integridade ZIP.

## Gates

| Gate | Aprovação | Em caso de falha |
|---|---|---|
| Proveniência | Mesa no pin; perfil e `patchSeriesId` coerentes; série esperada aplicada sem drift | Compare inputs antes de atualizar o lock; não reescreva evidências históricas. |
| Toolchain | NDK selecionado explicitamente; ferramentas host e dependências target separadas | Leia o erro do Meson; verifique target, sysroot e `pkg-config`. |
| ICD | ELF64 `AArch64`, notas Android, NDK esperado e validação estática aprovada | Inspecione `file`, `readelf` e o primeiro erro de build/link. |
| ADPKG dev | ZIP íntegro; biblioteca e SHA-256 iguais aos do ICD validado | Confira `meta.json`, `SHA256SUMS.txt` e os bytes do `.so`. |
| Runtime | ICD correto carregado em Mali compatível; compute retorna `0x12345678` em 10/10 | Pare no primeiro gate que falhar. Preserve logs, resultado e identidade do binário. |

Abra o [roteiro operacional](./references/workflow.md) para comandos, dependências, casos confirmados e recursos do repositório.

## Entrega

Reporte o diagnóstico, a ação executada, os resultados por gate e um próximo passo verificável. Inclua perfil, revisão Mesa, `patchSeriesId`, NDK/API e SHA-256 quando pertinentes. Declare o que não foi executado. Use a baseline de hardware aprovada para comparar a migração, não para substituir os gates de release.
