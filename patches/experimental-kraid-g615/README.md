# Experimental Kraid G615 overlay

This opt-in overlay is not part of the default patch series or a release. It
contains a narrowly scoped FAU hypothesis and an IDVS prototype. The tests
cover the documented G615 workloads, not every instruction, shader or GPU.

Prepare the pinned Mesa base with the standard G615 patch families and
`jm-v7-wip` through 0178, without the later commit that reverts Android's
Kraid default. The expected prepared tree is
`d5db8cd96dc795016f771145459e5cc5907ec761`. Then run:

```sh
sh scripts/apply-experimental-kraid-g615.sh --mesa /path/to/prepared-mesa
```

The script checks the exact tree and requires `.panvk-patchlevel` to contain
`p0178`, so the resulting driver's identity does not report an older patch
level. It rejects patch drift and does not configure or build Mesa, alter the
standard series, or change global device settings.
Record the hash of each overlay patch alongside the base and build hashes;
the standard patch-series identifier does not identify this overlay.

Before sharing an experimental build, follow the compute, IDVS and app-UID
checks in [the test documentation](../../tests/README.md). A successful
linear-image IDVS test does not fix or validate AHB import. See that document
for results, limitations, and the requirement to preserve the app's original
private driver.

## IDVS review notes

The position variant is compiled first. Its FAU layout is copied to the
varying variant, which can append promoted constants, and the resulting layout
is copied back. This preserves existing word indices but does not prove that
all shared or near-capacity FAU layouts work correctly.

The varying variant's `has_shader_clk_instr` is not merged back into the
position variant's metadata. If a clock instruction survives only in the
varying variant, the combined metadata can therefore report it as absent.
This is a static finding, not a reproduced rendering failure: the inspected
PanVK code has no consumer of that field, while the Gallium Panfrost driver
does. Check the applicable backend contract and add a regression before
promoting the prototype; do not infer that this explains the black screen.
