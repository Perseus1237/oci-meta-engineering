import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import se_factory as factory


class CustomerFactoryTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)

    def test_reuse_and_customer_evidence(self):
        for name in ("juniper", "harbor", "cedar"):
            project = self.root / name
            engagement = factory.EXAMPLES / name
            factory.commission(engagement, project)
            self.assertTrue(factory.evaluate(engagement, project)["passed"])
            self.assertEqual(factory.read(project / "brief.json")["customer"],
                             factory.read(engagement / "brief.json")["customer"])
            if name == "harbor":
                subprocess.run([sys.executable, "-B", "solution.py"], cwd=project, check=True,
                               stdout=subprocess.DEVNULL)
                html = (project / "output/review.html").read_text()
                self.assertIn("2 of 3 documents", html)
                self.assertIn("PO-732 (p. 1", html)
                self.assertIn("PO-723 (p. 2", html)
                self.assertIn("PurchaseOrder: conflicting values", html)

    def test_cli_shape_and_initial_failure(self):
        sample = factory.read(factory.EXAMPLES / "harbor/samples/two-po-numbers.json")
        cli_keys = {"pageNumber": "page-number", "documentFields": "document-fields",
                    "fieldLabel": "field-label", "fieldValue": "field-value", "fieldType": "field-type"}

        def cli(value):
            if isinstance(value, dict):
                return {cli_keys.get(k, k): cli(v) for k, v in value.items()}
            if isinstance(value, list):
                return [cli(v) for v in value]
            return value

        engagement = self.root / "brief"
        factory.engagement_copy(factory.EXAMPLES / "harbor", engagement)
        factory.write(engagement / "samples/two-po-numbers.json", {"data": cli(sample)})
        project = self.root / "poc"
        factory.commission(engagement, project)
        self.assertTrue(factory.evaluate(engagement, project)["passed"])
        (project / "policy.py").write_bytes((factory.ASSETS / "history/invoice-intake-initial.py").read_bytes())
        report = factory.evaluate(engagement, project)
        self.assertFalse(report["passed"])
        self.assertEqual([r["id"] for r in report["cases"] if not r["passed"]], ["two-po-numbers"])

    def test_source_inputs_and_grader_stay_authoritative(self):
        engagement, project = factory.EXAMPLES / "juniper", self.root / "poc"
        factory.commission(engagement, project)
        (project / "acceptance.json").write_text("[]")
        (project / "check.py").write_text("print('pass')")
        result = factory.evaluate(engagement, project)
        self.assertFalse(result["passed"])
        self.assertEqual(set(result["input_changes"]), {"acceptance.json", "check.py"})
        self.assertEqual(len(result["cases"]), 2)
        with self.assertRaises(ValueError):
            factory.commission(engagement, project)

    def test_new_factory_and_codex_build_entry_point(self):
        practice = self.root / "practice"
        factory.new_factory(practice)
        cmd = [sys.executable, "-B", str(practice / "se_factory.py")]
        subprocess.run([*cmd, "new-pattern", "triage"], cwd=self.root, check=True, capture_output=True)
        engagement = practice / "sales-factory/engagements/triage-pilot"
        first = subprocess.run([*cmd, "run", str(engagement), str(self.root / "before")], capture_output=True)
        self.assertEqual(first.returncode, 1)
        self.assertFalse(factory.read(self.root / "before/output/acceptance-report.json")["passed"])

        # Exercise orchestration without sending a model request during a test.
        binary = self.root / "codex"
        binary.write_text(
            f"#!{sys.executable}\n"
            "import json, sys\nfrom pathlib import Path\n"
            "assert sys.argv[1:] == ['exec', '--sandbox', 'workspace-write', '--skip-git-repo-check', '--json', '-']\n"
            "assert 'solve(document, brief)' in sys.stdin.read()\n"
            "Path('solution.py').write_text(\"def solve(document, brief):\\n"
            "    text = document['request'].lower()\\n"
            "    if 'damaged' in text: return {'queue': 'claims'}\\n"
            "    if 'arrive' in text: return {'queue': 'delivery-status'}\\n"
            "    return {'queue': 'manual-review'}\\n\")\n"
            "Path('HANDOFF.md').write_text('Run python3 check.py to replay the customer example.')\n"
            "print(json.dumps({'test': 'simulated builder'}))\n")
        binary.chmod(0o700)
        project = self.root / "built"
        env = {**os.environ, "PATH": str(self.root) + os.pathsep + os.environ["PATH"]}
        subprocess.run([*cmd, "run", str(engagement), str(project), "--codex"], check=True,
                       cwd=self.root, env=env, capture_output=True)
        report = factory.read(project / "output/acceptance-report.json")
        self.assertTrue(report["passed"])
        self.assertEqual(report["builder"], "codex")
        self.assertIn("simulated builder", (project / ".runs/codex.jsonl").read_text())
        (project / "HANDOFF.md").unlink()
        self.assertFalse(factory.evaluate(engagement, project, codex_build=True)["passed"])
