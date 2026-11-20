# Roteiro operacional: PanVK Android

Execute os comandos na raiz de uma cópia descartável do repositório. Não use caminhos pessoais, artefatos de outra sessão ou a árvore Mesa original como inputs implícitos.

## 1. Proveniência e dependências

- Leia [sources.lock](../../../../sources.lock), o [perfil G615](../../../../profiles/g615-v11-csf.json) e o [contrato dos patches](../../../../patches/README.md).
- Rode `git status --short` e `python3 scripts/compute-patch-series-id.py --profile g615-v11-csf`. Compare com `sources.lock`. O cálculo inclui arquivos elegíveis de famílias não aplicadas; registre também a variante efetivamente usada, incluindo qualquer opt-in.
- Verifique Git, Python 3 (incluindo Mako e packaging), Meson, Ninja, `pkg-config`, compilador C/C++ host, LLVM/Clang, Rust e `bindgen`. Consulte o [README](../../../../README.md#building) para os mínimos em vigor.
- Para codegen Mesa, confira também ferramentas e bibliotecas indicadas pelo Meson, como Bison, Flex, `glslangValidator`, LLVM SPIR-V, SPIRV-Tools, libdrm e expat no host. Não trate toda dependência detectada como obrigatória.
- O [fetch-ndk.sh](../../../../scripts/fetch-ndk.sh) provisiona o ZIP oficial r30 `30.0.16248370` para host Linux x86_64. Verifica o checksum publicado. `--depth 1` não se aplica ao ZIP; não use um clone de fontes no lugar do toolchain.
- O build chama [build-android-deps.sh](../../../../scripts/build-android-deps.sh) e [prepare-x11-headers.sh](../../../../scripts/prepare-x11-headers.sh) quando os prefixos faltam. O primeiro prepara libdrm target e zlib do sysroot. O segundo copia headers X11/XCB do host e gera `.pc` sem bibliotecas de link. Confirme os headers antes do build; use `X11_INCLUDE` se os headers estiverem fora de `/usr/include`.

## 2. Build e validação estática

```sh
set -eu
profile=g615-v11-csf
ndk="$PWD/work/ndk/30.0.16248370"
./scripts/fetch-ndk.sh
./scripts/fetch-mesa.sh
./scripts/apply-patches.sh --profile "$profile"
./scripts/build-android.sh --profile "$profile" --ndk "$ndk"
so="dist/android-$profile/libvulkan_panfrost.so"
file "$so"
readelf -h -n "$so"
./scripts/validate-binary.sh --abi android "$so"
sha256sum "$so"
```

O [build Android](../../../../scripts/build-android.sh) usa [o cross file](../../../../meson/android-aarch64.ini) e chama o [bootstrap](../../../../scripts/bootstrap-host-tools.sh) quando necessário. `mesa_clc`, `vtn_bindgen2` e `panfrost_compile` são binários host; o ICD é target AArch64. O WSI `android,x11` não determina a arquitetura do ELF.

**Caso confirmado — bindgen:** no build anterior com NDK r27d, o primeiro erro apareceu em `src/compiler/rust/bindings.rs`, com `mmintrin.h` x86 no cross-build AArch64. O retry com target e sysroot explícitos compilou. Não presuma que r30 precisa desse ajuste. Se o log atual reproduzir a assinatura, verifique o comando `bindgen` e faça um único retry com `BDIR` novo:

```sh
ndk="$PWD/work/ndk/30.0.16248370"
BDIR="$PWD/build/android-bionic-bindgen-check" \
BINDGEN_EXTRA_CLANG_ARGS="--target=aarch64-linux-android29 --sysroot=$ndk/toolchains/llvm/prebuilt/linux-x86_64/sysroot" \
  ./scripts/build-android.sh --profile g615-v11-csf --api 29 --ndk "$ndk"
```

Confira `build/android-bionic.log` ou `$BDIR.log`. Não promova um retry de diagnóstico sem registrar suas opções e o artefato resultante. Use [validate-binary.sh](../../../../scripts/validate-binary.sh) mais `readelf` para confirmar ABI, arquitetura e notas do NDK.

### Verificações paralelas ao ICD

Rode as suítes afetadas em `tests/dxvk/profile`, `tests/runtime-features` e `tests/consumer-compat` via `python3 -m unittest discover`. A última usa o `vk.xml` do Mesa preparado. Use `python3 tests/validate-package-selfcheck.py` para regressões do validador.

PanPlay e PanProbe têm toolchains Gradle independentes. Leia seus `app/build.gradle.kts` e rode `./gradlew :app:lintDebug :app:assembleDebug` nas respectivas pastas. Se o Gradle reportar licença não aceita, marque o gate como bloqueado; não confunda esse erro com o build do ICD. Para glibc, use o [guia de build](../../../../docs/BUILD-POCO-X6-PRO.md); não use o `.so` Bionic como substituto.

## 3. ADPKG de desenvolvimento

Use [package-launcher-zips.sh](../../../../scripts/package-launcher-zips.sh) com uma versão `-dev`. Escolha uma saída nova: o script pode substituir um ZIP de mesmo nome.

```sh
out="$(mktemp -d "$PWD/dist/adpkg-dev.XXXXXXXX")"
./scripts/package-launcher-zips.sh \
  --so dist/android-g615-v11-csf/libvulkan_panfrost.so \
  --version v0.0.0-dev-ndk30 --only adpkg \
  --dev-name PanVK-G615-dev-ndk30 --outdir "$out"
```

Use `unzip -t` no ZIP informado pelo script. Compare o `.so` extraído, byte a byte, com o original. Compare seu SHA-256 com `SHA256SUMS.txt`. Confirme `libraryName` e `minApi` em `meta.json`. A compilação para API 29 não implica que o ADPKG aceite API 29: o empacotador dev declara `minApi: 35`.

O [empacotador de release](../../../../scripts/package-android-adpkg.sh) é outro fluxo. Siga o [guia de release](../../../../docs/RELEASE.md) e o [validador de pacote](../../../../scripts/validate-package.sh). Não trate um ZIP dev íntegro como release universal ou como evidência de execução.

## 4. Baseline em hardware

1. Use `adb devices -l` para identificar o alvo. Confirme GPU, Android, Kbase e compatibilidade com o perfil; não extrapole resultados para outro aparelho.
2. No Poco X6 Pro com Mali-G615, importe o ADPKG no app de teste sem substituir o driver do sistema. Siga o [guia de gates](../../../../tests/README.md).
3. Confirme `driverInfo`, enumeração da GPU e `vkCreateDevice`. Depois execute o compute limitado: **10/10 leituras iguais a `0x12345678`**. Não use a enumeração como prova do dispatch.
4. Registre Build ID, hash do `.so`, perfil, revisão, patch series, variante, dispositivo, logs e resultados. Em seguida compare a migração contra a mesma baseline, com uma mudança por execução.
5. Valide offscreen, Android WSI e AHardwareBuffer em gates separados. Se necessário, amplie para CTS conforme o risco da mudança. Use cargas limitadas e preserve o primeiro erro.
