from pathlib import Path
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


if __name__ == "__main__":
    unittest.main()
