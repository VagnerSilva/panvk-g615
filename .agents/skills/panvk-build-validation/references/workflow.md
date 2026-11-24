# Roteiro operacional: PanVK Mesa 27 Android/Bionic e Linux/glibc

Execute comandos de preparação/build somente na raiz de uma cópia descartável do repositório, com autorização para aplicar a série nessa cópia. Não use caminhos pessoais, artefatos de outra sessão ou a árvore Mesa original como inputs implícitos. Para manutenção documental, use scripts e evidências existentes: os blocos de build e runtime abaixo são instruções, não verificações obrigatórias da documentação.

Use Bash nos blocos shell e `set -euo pipefail` para propagar falhas, inclusive nas inspeções por pipeline. Defina as variáveis de cada procedimento antes de executá-lo.

O alvo documental é Moto G86 / Mali-G615 MC2, `PAN_ARCH=11`, Kbase CSF. Android 16 e CSF 1.21 constam no manifesto histórico Moto; a configuração atual deve ser confirmada antes de testes físicos. G15 é o rótulo do plano, não outro valor de `PAN_ARCH`.

## 1. Proveniência e dependências

Leia [sources.lock](../../../../sources.lock), o [perfil G615](../../../../profiles/g615-v11-csf.json) e o [contrato dos patches](../../../../patches/README.md). O único perfil aceito pelos scripts é `g615-v11-csf`; seus metadados ainda descrevem Poco X6 Pro MC6/MT6897, não Moto MC2/MT6878. Não altere perfil, pin ou lock para esconder essa diferença; registre separadamente o dispositivo real.

Antes de preparar a cópia, registre:

```sh
git status --short --untracked-files=all
git branch --show-current
git rev-parse HEAD
git diff --stat
git diff --cached --stat
git -C work/mesa rev-parse HEAD
git -C work/mesa status --short --untracked-files=all
python3 -B scripts/compute-patch-series-id.py --profile g615-v11-csf
```

Compare Mesa e o hash calculado com o lock. Se a árvore Mesa não existir, registre isso como input ausente antes do fetch. Preserve mudanças locais e arquivos não rastreados necessários; exportar apenas `HEAD` não os inclui.

O `patchSeriesId` inclui arquivos elegíveis de famílias não aplicadas. Não comprova aplicação. Registre a variante efetiva e obtenha `series-manifest.json` com `--series-manifest` do [aplicador](../../../../scripts/apply-patches.sh); esse manifesto lista os inputs ordenados aplicados. Seu SHA-256 é uma identidade adicional, não substitui o hash do ICD.

Verifique Git, Python 3/Mako/packaging, Meson, Ninja, `pkg-config`, C/C++ host, LLVM, Rust e bindgen. O [README](../../../../README.md#building) registra Meson 1.7+, Rust 1.85+, target Rust Android e restrições de bindgen. Consulte o Meson para Bison, Flex, `glslangValidator`, LLVM SPIR-V, SPIRV-Tools, libdrm e expat host; nem toda dependência detectada é obrigatória. Registre versões e origem; instale dependências apenas após uma falta confirmada.

**Efeitos dos scripts:** [fetch-mesa.sh](../../../../scripts/fetch-mesa.sh) recebe um diretório de trabalho posicional e faz checkout/reset/clean. [prepare-x11-headers.sh](../../../../scripts/prepare-x11-headers.sh) substitui seu prefixo. O [build Android](../../../../scripts/build-android.sh) pode limpar `BDIR` ao mudar a release string e sobrescreve o ICD de destino. Nunca os execute sobre dados originais ou destinos que precisam ser preservados.

## 2. Android/Bionic

O [fetch-ndk.sh](../../../../scripts/fetch-ndk.sh) provisiona NDK r30 `30.0.16248370`, verifica SHA-1 e aceita `--work DIRECTORY`. Seu arquivo oficial exige host Linux x86_64. O build aceita `--ndk` explicitamente; r30 não é uma checagem rígida do script. Em host ARM64, selecione um toolchain compatível e confira também a descoberta de NDK pelo script de dependências; não execute o fetch oficial x86_64.

O build chama [build-android-deps.sh](../../../../scripts/build-android-deps.sh) e o preparador X11 quando os prefixos faltam. Libdrm target e zlib do sysroot ficam separados do host. X11/XCB usam headers e `.pc` sem bibliotecas de link; `X11_INCLUDE` seleciona headers fora de `/usr/include`. Não reaproveite prefixos de outro NDK/API sem comprovar sua origem.

Fluxo Linux x86_64, em cópia descartável autorizada com destinos novos:

```sh
set -euo pipefail
profile=g615-v11-csf
ndk="$PWD/work/ndk/30.0.16248370"
run="$(mktemp -d "$PWD/build-android-review.XXXXXXXX")"
./scripts/fetch-ndk.sh
./scripts/fetch-mesa.sh
./scripts/apply-patches.sh --profile "$profile" \
  --series-manifest "$run/series-manifest.json"
env -u PANVK_HOST_TOOLS_CACHE \
  ./scripts/bootstrap-host-tools.sh --mesa "$PWD/work/mesa" --out "$run/host-tools"
BDIR="$run/bionic" DDIR="$run/dist" HOST_TOOLS="$run/host-tools/bin" \
  ./scripts/build-android.sh --profile "$profile" --api 29 --ndk "$ndk"
sha256sum "$run/series-manifest.json" "$run/dist/libvulkan_panfrost.so"
```

API 29 é o default do script, não comprovação de suporte runtime nessa API. O [cross file Android](../../../../meson/android-aarch64.ini) usa API 35 no template; o script gera a cópia correspondente a `--api`. Confira a cópia gerada, target/sysroot e `pkg_config_libdir` target antes de interpretar erros de configuração. O log acima fica em `$run/bionic.log`.

[bootstrap-host-tools.sh](../../../../scripts/bootstrap-host-tools.sh) produz `mesa_clc`, `vtn_bindgen2` e `panfrost_compile` host. Reconstrua-os após mudanças da série: o cache opt-in usa somente o commit Mesa e pode conservar codegen antigo. O ICD é target AArch64; WSI `android,x11` não determina sua arquitetura.

O build habilita `-Dpanfrost-rust=true`. [Android 017](../../../../patches/android/017-default-to-kraid-on-android.patch) seleciona Kraid por padrão no Android e preserva `PAN_USE_KRAID=0`, `1`/`all` e seletores de estágio. Registre a seleção do processo de teste; não transforme o controle legado em aprovação de Kraid.

## 3. Linux/glibc

Use [build-glibc.sh](../../../../scripts/build-glibc.sh), não o ICD Bionic. O [guia glibc](../../../../docs/BUILD-POCO-X6-PRO.md#glibc-cross-build-on-wsl-or-linux) descreve dependências e seleção de host.

Em Linux/WSL x86_64, sem ADB:

```sh
./scripts/build-glibc.sh --profile g615-v11-csf --jobs 2 \
  --cross-file "$PWD/meson/linux-aarch64-debian-cross.ini"
```

O [cross file Debian](../../../../meson/linux-aarch64-debian-cross.ini) requer GCC/G++/binutils AArch64, Rust `aarch64-unknown-linux-gnu`, bindgen, ferramentas host e dependências de desenvolvimento AArch64. Adapte uma cópia para outra distro/sysroot. `pkg_config_libdir` deve resolver dependências target, não bibliotecas host.

O default inclui X11 e Wayland; adicione `--headless` somente para compute/offscreen sem WSI. `--headless` exige `--cross-file`. Cross local não combina com `--serial`, `--device-root` ou `--chroot-wrapper`; `--jobs` aceita 1 ou 2 e também limita o bootstrap host.

Sem cross file, host AArch64 usa [linux-aarch64-native.ini](../../../../meson/linux-aarch64-native.ini). Em outro host, o modo dispositivo exige `--serial` e confirmação do chroot; faz transferência e build remoto, portanto não é um exercício documental sem efeitos físicos.

Cada execução reconstrói o pin e aplica a série em `build/glibc-replay-<profile>-<pid>`. O destino default é `dist/glibc-g615-v11-csf`, com ICD, JSON e manifesto. O script recusa destino existente e retém workspace de falha. Não remova ou mova dados sem autorização. O manifesto identifica fontes; registre separadamente toolchain, Build ID e hash do ICD.

Kraid não é selecionado por padrão em glibc. Confira sua inclusão na configuração Meson e use `PAN_USE_KRAID=all` no processo alvo quando a validação exigir Kraid; não presuma equivalência com Android.

Nos dois ambientes, `--with-kbase-sync` é opt-in do aplicador; glibc também o aceita no build. Aplica somente 002-004 após a série principal. Leia as [limitações](../../../../patches/experimental-kbase-sync/README.md); não promova a variante a default ou release. No Android, registre a opção na aplicação e mantenha build/pacote separados; o build Android não aceita essa flag.

## 4. Inspeção ELF e pacote

Selecione `so` do destino produzido e `abi=android` ou `abi=glibc`, sem usar um artefato implícito:

```sh
file "$so"
readelf -h -n "$so"
readelf -d "$so"
readelf --version-info "$so"
./scripts/validate-binary.sh --abi "$abi" "$so"
sha256sum "$so"
```

Exija ELF64, little-endian e Machine AArch64. Registre GNU Build ID; no Android, inspecione `.note.android.ident` para API/NDK quando presente e confronte com toolchain/log, sem inferir a versão apenas pelo nome do pacote. Glibc deve apresentar `libc.so.6` e requisitos `GLIBC_*` compatíveis com o ambiente alvo; Bionic não pode depender de glibc ou bibliotecas host X11. Inspecione todos os `DT_NEEDED` para disponibilidade no alvo.

[validate-binary.sh](../../../../scripts/validate-binary.sh) verifica alguns exports/dependências, mas não impõe ELF64/AArch64 ou notas. Confirme esses campos explicitamente. Exija os exports dinâmicos definidos `vk_icdGetInstanceProcAddr` e `vk_icdNegotiateLoaderICDInterfaceVersion` com `llvm-nm -D --defined-only "$so"` (ou `nm`); símbolo indefinido não satisfaz o gate.

Use [package-launcher-zips.sh](../../../../scripts/package-launcher-zips.sh) somente para ICD Bionic/ADPKG dev, com versão `-dev` e saída nova. Pré-condição: `dist/` existente na cópia, `abi=android` e ICD inspecionado; esse empacotador não verifica a ABI.

```sh
out="$(mktemp -d "$PWD/dist/adpkg-dev.XXXXXXXX")"
./scripts/package-launcher-zips.sh \
  --so "$so" --version v27.0.0-dev --only adpkg \
  --dev-name PanVK-G615-dev --outdir "$out"
```

Defina `zip` como o caminho exato informado pelo script e valide sem extrair sobre arquivos existentes:

```sh
unzip -t "$zip"
unzip -p "$zip" meta.json
unzip -p "$zip" VALIDATION.json
unzip -p "$zip" SHA256SUMS.txt
unzip -p "$zip" libvulkan_panfrost.so | sha256sum
cmp "$so" <(unzip -p "$zip" libvulkan_panfrost.so)
```

O último comando exige Bash. Compare também o hash com `SHA256SUMS.txt`, `libraryName`, perfil, `driverVersion` e `minApi: 35`. API 29 do build não prova API 29 do pacote. `VALIDATION.json` dev não contém aprovação física.

Os [empacotadores Android](../../../../scripts/package-android-adpkg.sh) e [glibc](../../../../scripts/package-glibc.sh) seguem outro contrato. Use [RELEASE.md](../../../../docs/RELEASE.md) e [validate-package.sh](../../../../scripts/validate-package.sh) no pacote canônico, com fontes/manifestos/evidências coerentes. O checkout atual é G615-only; o fluxo universal foi retirado.

## 5. Diagnóstico dirigido

| Sintoma / responsável | Evidência e ação | Verificação após correção |
|---|---|---|
| Bindgen inclui `mmintrin.h` x86 no cross AArch64 | Confira primeiro comando bindgen, target e sysroot no log Meson/Ninja. A assinatura foi relatada no fluxo antigo r27d; não aplique workaround preventivamente ao r30. | Um retry com `BDIR` novo, target/sysroot explícitos, seguido de inspeção ELF. |
| Headers X11/XCB ausentes | Confira `xcb/xcb.h`, `X11/Xlib-xcb.h`, `X11/xshmfence.h` em `X11_INCLUDE` antes de chamar o preparador em prefixo descartável. | Meson resolve `.pc` header-only, sem link host X11 no Bionic. |
| Codegen antigo após mudar patches | Compare árvore usada pelos três geradores host; cache só por pin não prova atualização. Reconstrua geradores da série aplicada, sem cache compartilhado. | Regeneração/build do alvo afetado; registre novo artefato. |
| Glibc cross falha no Meson | Confira ferramentas AArch64, target Rust e `.pc` target; `--headless` só resolve dependências WSI se WSI não fizer parte do aceite. | Nova execução isolada; nenhum artefato publicado após falha. |
| Patch drift ou hash divergente | Confira pin, ordem, perfil e inputs; prepare correção reviewable, nunca ignore offset/fuzz ou atualize lock para mascarar drift. | Check estrito e log da aplicação autorizada na cópia. |
| Importador rejeita ADPKG | Confira identidade extraída do ICD, `meta.json`, nome dev distinto, hash e API mínima. | Integridade e comparação de bytes; importação física é outro gate. |
| Gradle exige licença ou SDK ausente | Use erro do aplicativo, não log do ICD; não aceite licenças ou instale SDK implicitamente. | Gate app `BLOQUEADO` até pré-condição resolvida. |
| Enumera, mas compute/render falha | Preserve primeiro resultado incorreto/crash, hash, modo e seletor Kraid; encaminhe ao especialista responsável. | Mesmo caso limitado, mesma identidade e controle relevante; enumeração não é sucesso. |

Se o bindgen reproduzir exatamente a assinatura, o retry Android usa, junto das mesmas opções explícitas de host/destino/NDK:

```sh
BDIR="$run/bionic-bindgen-check" DDIR="$run/dist-bindgen-check" \
HOST_TOOLS="$run/host-tools/bin" \
BINDGEN_EXTRA_CLANG_ARGS="--target=aarch64-linux-android29 --sysroot=$ndk/toolchains/llvm/prebuilt/linux-x86_64/sysroot" \
  ./scripts/build-android.sh --profile g615-v11-csf --api 29 --ndk "$ndk"
```

## 6. Testes e evidências

### Host e aplicativos

Não rode suítes para aprovar somente texto. Quando o comportamento correspondente mudar, selecione a suíte existente:

```sh
python3 -m unittest discover -s tests -p 'test_build_glibc_cross.py'
python3 -m unittest discover -s tests -p 'test_g615_build_series.py'
python3 -m unittest discover -s tests -p 'test_package_launcher_zips.py'
python3 tests/validate-package-selfcheck.py
```

As suítes [DXVK/profile](../../../../tests/dxvk/profile), [runtime-features](../../../../tests/runtime-features) e [consumer-compat](../../../../tests/consumer-compat) usam `python3 -m unittest discover -s <diretório> -p 'test_*.py'`; consumer-compat exige o `vk.xml` do Mesa preparado. Não equivalem a execução Vulkan no Moto.

PanPlay e PanProbe têm toolchains próprios: consulte [Gradle PanPlay](../../../../apps/panvk-launcher/app/build.gradle.kts) e [Gradle PanProbe](../../../../apps/panvk-test/app/build.gradle.kts). Para alterações pertinentes, rode `./gradlew :app:lintDebug :app:assembleDebug` na pasta do app. Não execute Gradle apenas para atualizar esta skill.

### Funcionamento e identidade física

Antes de qualquer teste físico autorizado: selecione o serial via `adb devices -l`; registre modelo/SoC, GPU/cores, Android/ROM, kernel, Kbase/UAPI, acesso `/dev/mali0`, ABI e identidade do ICD realmente carregado. Não substitua driver do sistema. Use pacote/caminho isolado, timeout, cargas pequenas e uma mudança por execução.

Os procedimentos e resultados esperados estão no [guia de testes](../../../../tests/README.md); esta tabela seleciona o gate, não reimplementa seus harnesses:

| Componente | Teste / aprovação | Limite da evidência |
|---|---|---|
| Inicialização, dispositivo e memória GPU | Gates D/E do guia: ICD correto, `vkCreateInstance`, `vkCreateDevice`, fila, buffer mapeado, bind e destruição. | Identifique PanVK, não lavapipe/vendor incidental; alocação não prova dispatch. |
| Compute | [compute](../../../../tests/compute): modo magic exige `0x12345678` em 10/10; diagnósticos `compute_N` usam critérios próprios. | O [10/10 histórico](../../../../validation/g615-v11-csf/gateDE-compute-2026-09-19.txt) identifica MC6; não homologa Moto/série atual. |
| Renderização | [offscreen](../../../../tests/offscreen), Gate F: readback da triangulação, sem falso positivo de clear/blit. | Separe controles de estágio Kraid e apresentação. |
| DMA-BUF / AHardwareBuffer | [ahb](../../../../tests/ahb), Gate G: alocar, propriedades, importar/bind, escrever GPU, verificar CPU e liberar. | External AHB app-UID, buffer próprio WSI e shell privilegiado são caminhos distintos. |
| Sincronização / CSF | [sync](../../../../tests/sync): fences, semáforos, idle, cadeias cross-queue e importação `sync_file`. | Acesso Kbase/CSF confirmado; teste de lifetime glibc exige opt-in, CSF 1.21 e páginas 4 KiB conforme guia. Não valida toda UAPI. |
| WSI Android | [loader app](../../../../tests/android-loader-app), Gate H e modos `wsi_draw`/`wsi_recreate`: acquire/draw/present/readback conforme guia. | ANB release privado não prova loader do sistema; clear-only não prova draw. |
| Linux/glibc | ICD e JSON isolados, dependências compatíveis, acesso Kbase, compute/sync e WSI selecionado. | Bionic e Poco MC6 não certificam Moto glibc; headless não oferece X11/Wayland. |

Timeout, crash, ausência de resultado, device-lost e corrupção nunca são `PASS`. Estabilidade exige número de ciclos, duração e limites registrados. Desempenho exige baseline da mesma carga/dispositivo/configuração, hashes dos dois ICDs e metodologia; não extrapole um smoke test.

### Registros reutilizáveis

- [Manifesto Moto initializer](../../../../validation/mesa27-large-draw-initializer-fix.json): Mesa no pin, Android 16, G615 MC2, CSF 1.21, binário `c4532ef9…`, série `7d02a194…`; testes direcionados Large_Draw/tessellation/XFB. Exclui CTS completo, apresentação Android e AHB. Não corresponde à série atual só por compartilhar o pin.
- [Matriz da plataforma](../../../../docs/engineering/mali-kernel-platform/COMPATIBILITY_MATRIX.md): relatos Moto separados por WSI próprio, AHB externo app-UID, sync e glibc. Preserve falhas e desconhecidos; não transforme relato histórico em execução atual.
- [Série sync experimental](../../../../patches/experimental-kbase-sync/README.md): evidências por candidato e limitações de shutdown; disponibilidade opt-in não significa homologação.

Registre cada gate com estado, comando, resultado, log e identidade: revisão do projeto/Mesa, perfil, `patchSeriesId`, variante, SHA do manifesto, host/toolchain/API, Build ID e SHA-256 do ICD, dispositivo e seletor Kraid. Evidência sem vínculo suficiente ao binário permanece histórica ou `BLOQUEADO`, nunca atribuída ao pacote atual.

## 7. Gates e auditoria documental

| Gate / pré-condição | Procedimento e evidência | Aprovação / ação em falha |
|---|---|---|
| Proveniência / inputs disponíveis | Seção 1, lock/perfil, hash calculado; manifesto e log de aplicação quando executada. | Identidades coincidem, aplicação sem drift comprovada separadamente; investigar inputs, não reescrever histórico. |
| Toolchain / alvo selecionado | Seções 2/3, versões, cross gerado, sysroot e resolução `.pc`. | Host/target separados e dependências corretas; falta confirmada bloqueia o build. |
| Build / preparação concluída | Script escolhido, exit status e log Meson/Ninja; ICD e JSON glibc. | Exit 0 e todos os artefatos presentes; preservar primeiro erro causal. |
| ELF / artefato disponível | Seção 4, headers/notas, `DT_NEEDED`, exports definidos, Build ID/hash. | ELF64 AArch64 e ABI correta; não aceitar somente o PASS do script. |
| Pacote / ICD inspecionado | Seção 4, teste ZIP, metadados e comparação bytes/hashes; validador canônico se aplicável. | Conteúdo/identidade coerentes; mismatch é FAIL, não execução comprovada. |
| Runtime / dispositivo autorizado e identificado | Seção 6 e guia, logs do ICD exato e saída completa do modo. | Critério funcional do teste cumprido; falha ou ausência de pré-condição não aprova o próximo gate. |
| Estabilidade / carga e limites definidos | Logs dos ciclos, duração, erros, conclusão e identidade. | Sem falhas nos limites executados; nunca certificação geral. |
| Desempenho / baseline comparável | Mesma carga/ambiente, dois hashes e método reproduzível. | Resultados comparáveis; sem medição permanece NÃO EXECUTADO. |

Para auditar a skill sem builds/hardware, percorra sete exercícios: preparar Android; preparar glibc; diagnosticar compilação; inspecionar ELF; validar pacote; planejar teste funcional; analisar regressão. Use scripts, logs e artefatos já identificados. Confira flags/caminhos, pré-condições, primeiro erro, identidade e limitações. Sem artefato, valide somente as instruções e deixe o gate de execução `NÃO EXECUTADO` ou `BLOQUEADO`.

Na homologação documental, confira links locais, sintaxe dos blocos Bash, `git diff --check` e diff completo limitado aos dois documentos. Edite documentação diretamente; patches e check estrito de aplicação são exigidos somente para alterações no driver Mesa. Solicite aprovação final; essa auditoria não homologa o driver ou o hardware.
