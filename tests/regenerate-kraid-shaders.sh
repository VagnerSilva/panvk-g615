#!/bin/bash
set -eu

ROOT="$(cd "$(dirname "$0")" && pwd)"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/panvk-shaders.XXXXXXXX")"
trap 'rm -f "$TMP/guarded.comp.spv" "$TMP/guarded_bda.comp.spv" "$TMP/guarded_texture.comp.spv" "$TMP/fau_shift.comp.spv" "$TMP/idvs_varying.vert.spv" "$TMP/idvs_varying.frag.spv" "$TMP/idvs_multi.vert.spv" "$TMP/idvs_multi.frag.spv" "$TMP/idvs_point.vert.spv"; rmdir "$TMP"' EXIT

for shader in compute/guarded.comp compute/guarded_texture.comp compute/fau_shift.comp ahb/idvs_varying.vert ahb/idvs_varying.frag ahb/idvs_multi.vert ahb/idvs_multi.frag ahb/idvs_point.vert; do
  glslangValidator -V --target-env vulkan1.1 -o "$TMP/$(basename "$shader").spv" "$ROOT/$shader"
  spirv-val --target-env vulkan1.1 "$TMP/$(basename "$shader").spv"
done

glslangValidator -V --target-env vulkan1.2 -o "$TMP/guarded_bda.comp.spv" "$ROOT/compute/guarded_bda.comp"
spirv-val --target-env vulkan1.2 "$TMP/guarded_bda.comp.spv"

python3 - "$ROOT" "$TMP" <<'PY'
import struct
import sys
from pathlib import Path

root, tmp = map(Path, sys.argv[1:])
for shader, symbol in (
    ("compute/guarded.comp", None),
    ("compute/guarded_bda.comp", None),
    ("compute/guarded_texture.comp", None),
    ("compute/fau_shift.comp", None),
    ("ahb/idvs_varying.vert", "idvs_varying_vert_spv"),
    ("ahb/idvs_varying.frag", "idvs_varying_frag_spv"),
    ("ahb/idvs_multi.vert", "idvs_multi_vert_spv"),
    ("ahb/idvs_multi.frag", "idvs_multi_frag_spv"),
    ("ahb/idvs_point.vert", "idvs_point_vert_spv"),
):
    source = Path(shader)
    binary = (tmp / (source.name + ".spv")).read_bytes()
    words = struct.unpack(f"<{len(binary) // 4}I", binary)
    if symbol:
        text = f"/* Generated from {source.name} by glslangValidator. */\n"
        text += f"static const uint32_t {symbol}[] = {{\n"
        suffix = "u"
    else:
        text = ""
        suffix = ""
    for i in range(0, len(words), 8):
        text += "   " + ", ".join(f"0x{v:08x}{suffix}" for v in words[i:i + 8]) + ",\n"
    if symbol:
        text += "};\n"
    if symbol:
        output = root / source.with_suffix(source.suffix + ".spv.h")
    else:
        output = root / "compute" / (source.stem + ".spv.h")
    output.write_text(text)
PY
