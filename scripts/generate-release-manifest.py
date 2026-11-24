#!/usr/bin/env python3
"""generate-release-manifest.py — MANIFEST.json + SOURCE.json.

Usage: generate-release-manifest.py --profile g615-v11-csf --abi android-aarch64-bionic --stage <dir>
VALIDATION.json comes from scripts/collect-validation.py (real logs). No skeleton.
"""
import argparse, json, hashlib, pathlib, subprocess, datetime, sys, os

ap = argparse.ArgumentParser()
ap.add_argument('--profile', required=True)
ap.add_argument('--abi', required=True, choices=('android-aarch64-bionic', 'linux-aarch64-glibc'))
ap.add_argument('--stage', required=True)
ap.add_argument('--published', action='store_true')
a = ap.parse_args()
if a.profile != 'g615-v11-csf':
    ap.error(f"unsupported profile: {a.profile}; only g615-v11-csf is supported")
from build_provenance import checked_series, binary_build_id
stage = pathlib.Path(a.stage)
root = pathlib.Path(__file__).resolve().parent.parent

def sh(*cmd):
    return subprocess.check_output(cmd, text=True).strip()

# Releases are built from the sources.lock pin + patch series; work/mesa may be a dev tree.
lock = json.loads((root / 'sources.lock').read_text())
mesa_sha = lock['mesaCommit']
patch_series_id = sh('python3', str(root / 'scripts' / 'compute-patch-series-id.py'), '--profile', a.profile)
if patch_series_id != lock['patchSeriesId']:
    ap.error("sources.lock patchSeriesId does not match the current inventory")
so = stage / 'libvulkan_panfrost.so'
binary = so.read_bytes()
sha = hashlib.sha256(binary).hexdigest()
build_id = binary_build_id(binary)
series, series_digest = checked_series(root, (stage / 'series-manifest.json').read_bytes())
if series['profile'] != a.profile:
    ap.error("staged series profile does not match the package profile")

matrix_name = None
if (stage / 'runtime-feature-matrix.json').exists():
    matrix_name = 'runtime-feature-matrix.json'

manifest = {
    'profile': a.profile, 'abi': a.abi,
    'mesaCommit': mesa_sha, 'mesaVersion': lock.get('mesaVersion'),
    'patchSeriesId': patch_series_id,
    'buildHost': sh('uname', '-a'), 'date': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'ndkRoot': os.environ.get('ANDROID_NDK_ROOT'),
    'binarySha256': sha, 'buildId': build_id,
    'variant': series['variant'], 'seriesManifestSha256': series_digest,
}
if matrix_name:
    manifest['runtimeFeatureMatrix'] = matrix_name
(stage / 'MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n')

source = {
    'profile': a.profile, 'abi': a.abi,
    'binarySha256': sha, 'buildId': build_id,
    'variant': series['variant'], 'seriesManifestSha256': series_digest,
    'mesaRepo': lock.get('mesaRepo'),
    'mesaCommit': mesa_sha,
    'sourceCommit': mesa_sha,
    'patchSeriesId': patch_series_id,
    'referenceRepos': lock.get('referenceRepos'),
    'releaseStatus': {'prerelease': True, 'published': a.published},
    'bcCompatibilityIncluded': False,
}
if matrix_name:
    source['runtimeFeatureMatrix'] = matrix_name
(stage / 'SOURCE.json').write_text(json.dumps(source, indent=2) + '\n')

collector = root / 'scripts' / 'collect-validation.py'
validation_path = stage / 'VALIDATION.json'
collected = False
if collector.is_file():
    cmd = [
        sys.executable, str(collector),
        '--profile', a.profile,
        '--abi', a.abi,
        '--stage', str(stage),
        '--out', str(validation_path),
        '--require-beta-gates',
    ]
    subprocess.check_call(cmd)
    collected = validation_path.is_file()

if not collected:
    print(
        "FAIL: VALIDATION.json must come from scripts/collect-validation.py; "
        "refusing all-untested skeleton",
        file=sys.stderr,
    )
    sys.exit(1)

print(f"OK stage={stage} sha={sha[:16]} collected={collected}")
