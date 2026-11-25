import io
import json
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from zipfile import ZipFile

from demo import worker
from factory import ROOT, create
from review_job import check_job, review, zip_contents


class JobReviewTests(unittest.TestCase):
    def test_reject_other_jobs(self):
        job = {"id": "job", "stack-id": "stack", "operation": "PLAN", "lifecycle-state": "SUCCEEDED"}
        for key, value in (("id", "other"), ("stack-id", "other"), ("operation", "APPLY"),
                           ("lifecycle-state", "FAILED")):
            with self.subTest(key=key), self.assertRaises(ValueError):
                check_job({**job, key: value}, "stack", "job")

    def test_reviews_committed_source_and_rejects_different_job_archive(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            factory = root / "factory"
            create(json.loads((ROOT / "specs/platform.json").read_text()), factory)
            self.assertEqual(worker(factory).returncode, 0)
            subprocess.run(["git", "init", "-q", str(factory)], check=True)
            git = ["git", "-C", str(factory)]
            subprocess.run([*git, "add", "."], check=True)
            subprocess.run([*git, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                            "-c", "commit.gpgsign=false", "commit", "-qm", "Fixture"], check=True)
            revision = subprocess.check_output([*git, "rev-parse", "HEAD"], text=True).strip()
            bundle = subprocess.check_output([*git, "archive", "--format=zip", "HEAD:infra"])
            job = {"id": "job", "stack-id": "stack", "operation": "PLAN", "lifecycle-state": "SUCCEEDED"}
            real_run = subprocess.run

            def simulated_cli(command, **kwargs):
                if command[0] != "oci":
                    return real_run(command, **kwargs)
                action = command[3]
                if action == "get":
                    return subprocess.CompletedProcess(command, 0, json.dumps({"data": job}).encode())
                output = Path(command[command.index("--file") + 1])
                if action == "get-job-tf-config":
                    output.write_bytes(bundle)
                elif action == "get-job-tf-plan":
                    output.write_bytes((ROOT / "evals/owner-update.plan.json").read_bytes())
                else:
                    self.fail(f"unexpected OCI operation {action}")
                return subprocess.CompletedProcess(command, 0)

            with patch("subprocess.run", side_effect=simulated_cli):
                review(factory, revision, "cloud-platform", "stack", "job", root / "pass")
                record = json.loads((root / "pass/review.json").read_text())
                self.assertEqual(record["commit"], revision)
                self.assertEqual(record["config_files_sha256"], zip_contents(io.BytesIO(bundle)))
                changed = io.BytesIO()
                with ZipFile(changed, "w") as archive:
                    archive.writestr("extra.tf", "# different candidate")
                bundle = changed.getvalue()
                with self.assertRaisesRegex(ValueError, "configuration differs"):
                    review(factory, revision, "cloud-platform", "stack", "job", root / "fail")
                self.assertFalse((root / "fail").exists())
