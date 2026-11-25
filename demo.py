"""Replay the same ownership tickets and demonstrate reuse in a second checkout."""

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory, mkdtemp

from factory import BUCKET, ROOT, WORKER, create
from verify_plan import verify

CASES = ROOT / "evals/cases.json"
CANDIDATE = ROOT / "experiments/shared_tags_rule.py"


def read(path):
    return json.loads(path.read_text())


def worker(directory):
    return subprocess.run([sys.executable, "-B", str(WORKER)], cwd=directory,
                          capture_output=True, text=True, timeout=15)


def snapshot(directory):
    return {p.relative_to(directory): p.read_bytes()
            for p in directory.rglob("*") if p.is_file() and p != directory / BUCKET}


def replay(spec, candidate_rule=None):
    results = {}
    for case in read(CASES):
        with TemporaryDirectory() as sandbox:
            directory = Path(sandbox) / "factory"
            create(spec, directory, candidate_rule)
            path = directory / BUCKET
            document = read(path)
            bucket = document["resource"]["oci_objectstorage_bucket"]["pilot"]
            bucket["freeform_tags"] = case["tags"]
            path.write_text(json.dumps(document, indent=2) + "\n")
            original = path.read_bytes()
            other_files = snapshot(directory)

            run = worker(directory)
            if "error" in case:
                passed = (run.returncode != 0 and case["error"] in run.stderr
                          and path.read_bytes() == original)
            else:
                bucket["freeform_tags"] = case["expected"]
                try:
                    passed = run.returncode == 0 and read(path) == document
                except (ValueError, OSError):
                    passed = False
                if passed:
                    first_run = path.read_bytes()
                    passed = worker(directory).returncode == 0 and path.is_file() and path.read_bytes() == first_run
            results[case["id"]] = passed and snapshot(directory) == other_files
    return results


def compare(baseline, candidate):
    if baseline.keys() != candidate.keys() or not all(candidate.values()):
        return "hold"
    if all(baseline.values()):
        return "no-new-coverage"
    return "ready-for-review"


def demo(candidate_rule=CANDIDATE):
    build = ROOT / "build"
    build.mkdir(exist_ok=True)
    out = Path(mkdtemp(prefix="demo-", dir=build))
    platform = read(ROOT / "specs/platform.json")
    baseline = replay(platform)
    candidate = replay(platform, candidate_rule)
    decision = compare(baseline, candidate)
    for name in baseline:
        values = ["pass" if result[name] else "fail" for result in (baseline, candidate)]
        print(f"{name:22} {values[0]:>8} {values[1]:>10}")
    for label, result in (("baseline", baseline), ("candidate", candidate)):
        print(f"{label}: {sum(result.values())}/{len(result)}")
    report = {
        "suite_sha256": hashlib.sha256(CASES.read_bytes()).hexdigest(),
        "candidate_rule_sha256": hashlib.sha256(candidate_rule.read_bytes()).hexdigest(),
        "baseline": baseline, "candidate": candidate, "decision": decision,
    }
    if decision != "hold":
        manifests = []
        for spec, rule in ((platform, None), (read(ROOT / "specs/analytics.json"), candidate_rule)):
            directory = out / spec["name"]
            manifests.append(create(spec, directory, rule))
            run = worker(directory)
            if run.returncode:
                raise ValueError(run.stderr.strip())
        report["factories"] = manifests
        verify(read(ROOT / "evals/owner-update.plan.json"), platform["owner"])
        report["plan_check"] = "passed on Terraform plan from synthetic prior state"
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"Decision: {decision}\nEvidence: {out / 'report.json'}")
    return decision


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-rule", type=Path, default=CANDIDATE,
                        help="a locally reviewed Python file implementing with_owner(tags, owner)")
    args = parser.parse_args()
    print(f"{'Frozen case':22} {'Baseline':>8} {'Candidate':>10}")
    try:
        result = demo(args.candidate_rule.resolve())
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        sys.exit(f"Replay failed: {exc}")
    sys.exit(1 if result == "hold" else 0)
