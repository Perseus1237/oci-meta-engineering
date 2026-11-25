"""Grade one generated solution against the engagement owner's acceptance examples."""
import argparse
import importlib.util
import json
import sys
from pathlib import Path


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def grade(project, engagement):
    spec = importlib.util.spec_from_file_location("solution", project / "solution.py")
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(project))
    spec.loader.exec_module(module)
    brief = read(engagement / "brief.json")
    cases = read(engagement / "acceptance.json")
    if not isinstance(cases, list) or not cases:
        raise ValueError("add at least one independently agreed acceptance case")
    results = []
    ids = set()
    for case in cases:
        case_id, filename, expected = case["id"], case["sample"], case["expect"]
        if not isinstance(case_id, str) or not case_id or case_id in ids:
            raise ValueError("case IDs must be unique and nonempty")
        if Path(filename).name != filename or not isinstance(expected, dict) or not expected:
            raise ValueError("each case needs a sample filename and at least one expected output")
        ids.add(case_id)
        sample = read(engagement / "samples" / filename)
        try:
            output = module.solve(sample, brief)
            actual = {key: output[key] for key in expected}
            item = {"id": case_id, "passed": actual == expected, "expected": expected, "actual": actual}
        except Exception as exc:
            item = {"id": case_id, "passed": False, "error": str(exc), "expected": expected}
        results.append(item)
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--engagement", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    results = grade(args.project.resolve(), args.engagement.resolve())
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for row in results:
            print(("PASS" if row["passed"] else "FAIL"), row["id"])
            if not row["passed"]:
                print(json.dumps(row, indent=2))
    sys.exit(0 if all(row["passed"] for row in results) else 1)
