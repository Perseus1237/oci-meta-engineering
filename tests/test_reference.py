import copy
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from demo import CANDIDATE, compare, read, replay
from factory import BUCKET, ROOT, RULE, create
from verify_plan import verify


class FactoryTests(unittest.TestCase):
    def test_create_is_reproducible_and_preserves_existing_directory(self):
        spec = read(ROOT / "specs/platform.json")
        with TemporaryDirectory() as tmp:
            dest = Path(tmp) / "one"
            first = create(spec, dest)
            other = Path(tmp) / "two"
            second = create(spec, other)
            self.assertEqual(first, second)
            self.assertEqual(read(dest / "factory.json"), first)
            self.assertEqual(read(dest / BUCKET), read(other / BUCKET))
            with self.assertRaisesRegex(ValueError, "already exists"):
                create(spec, dest)
            changed = Path(tmp) / "changed_rule.py"
            changed.write_text((ROOT / "template" / RULE).read_text() + "\n# Test revision\n")
            candidate = create(spec, Path(tmp) / "candidate", changed)
            self.assertNotEqual(first["template_sha256"], candidate["template_sha256"])

    def test_invalid_spec_creates_nothing(self):
        with TemporaryDirectory() as tmp:
            dest = Path(tmp) / "factory"
            spec = read(ROOT / "specs/platform.json")
            for key, value in (("owner", "two teams"), ("name", "../bad"), ("tag_source", "other")):
                with self.subTest(key=key), self.assertRaises(ValueError):
                    create({**spec, key: value}, dest)
                self.assertFalse(dest.exists())

    def test_frozen_cases(self):
        spec = read(ROOT / "specs/platform.json")
        baseline = replay(spec)
        self.assertTrue(all(result for name, result in baseline.items() if name != "shared-team-tags"))
        candidate = replay(spec, CANDIDATE)
        self.assertTrue(all(candidate.values()), candidate)
        self.assertIn(compare(baseline, candidate), {"ready-for-review", "no-new-coverage"})
        self.assertEqual(compare(candidate, candidate), "no-new-coverage")
        self.assertEqual(compare(candidate, {**candidate, "owner-conflict": False}), "hold")


class PlanTests(unittest.TestCase):
    def setUp(self):
        self.plan = read(ROOT / "evals/owner-update.plan.json")
        self.resource = self.plan["resource_changes"][0]
        self.change = self.resource["change"]

    def reject(self):
        with self.assertRaises(ValueError):
            verify(self.plan, "cloud-platform")

    def test_expected_update_and_unaffected_resources(self):
        self.plan["resource_changes"].append({"address": "other", "change": {"actions": ["no-op"]}})
        verify(self.plan, "cloud-platform")

    def test_reject_wrong_owner_missing_old_tags_and_non_tag_changes(self):
        for key, value in (("freeform_tags", {"owner": "cloud-platform"}),
                           ("freeform_tags", {"owner": "other", "environment": "dev"}),
                           ("access_type", "ObjectRead"), ("name", "different")):
            with self.subTest(key=key, value=value):
                after = self.change["after"].copy()
                self.change["after"][key] = value
                self.reject()
                self.change["after"] = after

    def test_reject_existing_owner(self):
        self.change["before"]["freeform_tags"]["owner"] = "old-owner"
        self.reject()

    def test_reject_replacement_creation_and_noop(self):
        for actions in (["create", "delete"], ["create"], ["delete"], ["no-op"]):
            with self.subTest(actions=actions):
                self.change["actions"] = actions
                self.reject()

    def test_reject_additional_update(self):
        self.plan["resource_changes"].append(copy.deepcopy(self.resource))
        self.reject()

    def test_reject_unknowns_and_imports(self):
        self.change["after_unknown"] = {"freeform_tags": {"environment": True}}
        self.reject()
        self.change["after_unknown"] = {}
        self.change["importing"] = {"id": "bucket"}
        self.reject()

    def test_reject_other_plan_effects(self):
        for key, value in (("resource_drift", [{}]), ("deferred_changes", [{}]), ("errored", True),
                           ("complete", False), ("checks", [{"status": "unknown"}]),
                           ("output_changes", {"bucket": {"actions": ["update"]}})):
            with self.subTest(key=key):
                self.plan[key] = value
                self.reject()
                del self.plan[key]


if __name__ == "__main__":
    unittest.main()
