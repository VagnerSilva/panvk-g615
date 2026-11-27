from pathlib import Path
import os
import shlex
import subprocess
import tempfile
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]


class WorkflowTests(unittest.TestCase):
    def workflow(self, name):
        return yaml.load(
            (ROOT / ".github/workflows" / name).read_text(), Loader=yaml.BaseLoader
        )

    def test_build_compiles_and_validates_both_abis_before_upload(self):
        workflow = self.workflow("build.yml")
        job = workflow["jobs"]["build"]
        self.assertEqual(job["strategy"]["matrix"]["abi"], ["android", "glibc"])
        steps = job["steps"]
        commands = "\n".join(step.get("run", "") for step in steps)
        self.assertIn("build-android.sh", commands)
        self.assertIn("build-glibc.sh", commands)
        self.assertIn("--cross-file", commands)
        self.assertIn("validate-binary.sh", commands)
        self.assertIn("record-ci-build.py", commands)
        uploads = [step for step in steps if step.get("uses", "").startswith("actions/upload-artifact@")]
        self.assertTrue(any("g615-dev-" in step["with"]["name"] for step in uploads))

    def test_release_is_manual_downloads_selected_run_and_validates_before_publish(self):
        workflow = self.workflow("release.yml")
        self.assertEqual(set(workflow["on"]), {"workflow_dispatch"})
        self.assertEqual(set(workflow["on"]["workflow_dispatch"]["inputs"]), {"tag", "source_run_id"})
        steps = workflow["jobs"]["release"]["steps"]
        commands = "\n".join(step.get("run", "") for step in steps)
        self.assertIn("gh run download", commands)
        self.assertIn("validate-release-candidate.py", commands)
        self.assertLess(commands.index("validate-release-candidate.py"), commands.index("gh release create"))
        self.assertNotIn("./scripts/build-", commands)

    def test_release_assets_attach_dev_builds_on_publish_without_rebuilding(self):
        workflow = self.workflow("release-assets.yml")
        self.assertEqual(workflow["on"]["release"]["types"], ["published"])
        self.assertIn("workflow_dispatch", workflow["on"])
        job = workflow["jobs"]["assets"]
        self.assertGreater(int(job["timeout-minutes"]), 90)
        self.assertEqual(job["steps"][0]["with"]["ref"],
                         "${{ github.event.repository.default_branch }}")
        commands = "\n".join(step.get("run", "") for step in job["steps"])
        self.assertIn("upload-ci-release-assets.py", commands)
        self.assertNotIn("./scripts/build-", commands)
        self.assertEqual(workflow["permissions"]["contents"], "write")
        self.assertEqual(workflow["permissions"]["actions"], "read")

    def test_glibc_installs_target_xrandr_for_x11_wsi(self):
        steps = self.workflow("build.yml")["jobs"]["build"]["steps"]
        step = next(step for step in steps
                    if step.get("name") == "Prepare glibc AArch64 dependencies")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sudo = root / "sudo"
            sudo.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$APT_LOG"\n')
            sudo.chmod(0o755)
            log = root / "apt.log"
            result = subprocess.run(
                ["bash", "-e", "-o", "pipefail", "-c", step["run"]],
                cwd=root, env=dict(os.environ, PATH=f"{root}:{os.environ['PATH']}",
                                   APT_LOG=str(log)),
                text=True, capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            packages = next(shlex.split(line)[3:] for line in log.read_text().splitlines()
                            if line.startswith("apt-get install -y "))
            self.assertIn("libxrandr-dev:arm64", packages)
            self.assertNotIn("libxrandr-dev", packages)

    def test_native_spirv_tools_checks_installed_linker_api(self):
        steps = self.workflow("build.yml")["jobs"]["build"]["steps"]
        command = next(step["run"] for step in steps
                       if step.get("name") == "Build pinned native SPIRV-Tools")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            binaries = root / "bin"
            binaries.mkdir()
            stubs = {
                "git": "exit 0",
                "cmake": "exit 0",
                "pkg-config": '[ "$PKG_CONFIG_STATUS" = 0 ] || exit "$PKG_CONFIG_STATUS"\n'
                              'printf "%s\\n" "-I$PWD/work/ci-host-deps/include"',
                "c++": 'cat > "$PROBE_SOURCE"; exit "$PROBE_STATUS"',
            }
            for name, body in stubs.items():
                path = binaries / name
                path.write_text("#!/bin/sh\nset -eu\n" + body + "\n")
                path.chmod(0o755)
            source = root / "probe.cpp"
            environment = dict(os.environ, PATH=f"{binaries}:{os.environ['PATH']}",
                               PANVK_JOBS="2", PROBE_SOURCE=str(source))
            for status, pkg_status in (("0", "0"), ("47", "0"), ("0", "48")):
                with self.subTest(compiler_status=status, pkg_config_status=pkg_status):
                    source.unlink(missing_ok=True)
                    result = subprocess.run(
                        ["bash", "-e", "-o", "pipefail", "-c", command],
                        cwd=root, env=dict(environment, PROBE_STATUS=status,
                                           PKG_CONFIG_STATUS=pkg_status),
                        text=True, capture_output=True,
                    )
                    expected_status = pkg_status if pkg_status != "0" else status
                    self.assertEqual(result.returncode, int(expected_status), result.stderr)
                    if pkg_status != "0":
                        self.assertFalse(source.exists())
                        continue
                    self.assertTrue(source.exists(), "installed API was not checked")
                    self.assertIn("#include <spirv-tools/linker.hpp>", source.read_text())
                    self.assertIn("SetAllowPtrTypeMismatch(true)", source.read_text())


if __name__ == "__main__":
    unittest.main()
