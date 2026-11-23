#!/usr/bin/env python3
"""Capture Mesa's upstream Vulkan extension matrix, separate from runtime data."""
import argparse
import json
import pathlib
import re
import subprocess


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mesa", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    mesa = pathlib.Path(args.mesa)
    text = (mesa / "docs" / "features.txt").read_text()
    version = (mesa / "VERSION").read_text().strip()
    revision = subprocess.check_output(
        ["git", "-C", str(mesa), "rev-parse", "HEAD"], text=True
    ).strip()

    pattern = re.compile(
        r"^\s*(VK_[A-Za-z0-9_]+)\s+(DONE|not started|in progress|started|TODO|N/A)\s*(.*)$"
    )
    rows = []
    for line in text.splitlines():
        match = pattern.match(line)
        if match:
            rows.append(dict(zip(("name", "status", "drivers"), match.groups())))
    if not rows:
        raise SystemExit("No Vulkan extension rows found in Mesa docs/features.txt")
    done = sum(
        row["status"] == "DONE"
        and re.search(r"(?:^|[,(]\s*)panvk(?:/[^,\s)]+)?(?:\s*[,)]|$)", row["drivers"])
        is not None
        for row in rows
    )
    total = len(rows)
    coverage = round(done / total, 4)
    data = {
        "source": "docs/features.txt of exact Mesa checkout",
        "mesaRev": revision,
        "mesaCommit": revision,
        "mesaVersion": version,
        "panvk": {"done": done, "total": total, "coverage": coverage},
        "rows": rows,
        "note": "Upstream implementation matrix, NOT a per-device runtime guarantee.",
    }
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "upstream-feature-matrix.json").write_text(json.dumps(data, indent=2) + "\n")
    md = [
        f"# Upstream PanVK matrix (Mesa {revision})", "",
        f"Implemented: {done}/{total} ({coverage * 100:.1f}%)", "",
        "NOT a runtime guarantee. See runtime-feature-matrix.json from device probe.", "",
    ]
    (out / "upstream-feature-matrix.md").write_text("\n".join(md))
    print(f"OK done={done} total={total} out={out}")


if __name__ == "__main__":
    main()
