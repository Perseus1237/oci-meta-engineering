"""Create an OCI solution engineering AI factory and commission customer PoCs."""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory, mkdtemp

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "sales-factory"
BLUEPRINTS = ASSETS / "blueprints"
COMMON = ASSETS / "common"
EXAMPLES = ASSETS / "examples"
COMMON_FILES = ("AGENTS.md", "work-order.md", "check.py")
IGNORE = "build/\noutput/\n.runs/\n__pycache__/\n.DS_Store\n"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def slug(value):
    if not isinstance(value, str) or not re.fullmatch(r"[a-z][a-z0-9-]{0,62}", value):
        raise ValueError("blueprint names use lowercase letters, digits and hyphens")
    return value


def check_new(path):
    if path.exists() or path.is_symlink():
        raise ValueError(f"choose a new destination, {path} already exists")


def copy_files(source, target, names):
    target.mkdir(parents=True, exist_ok=True)
    for name in names:
        if not isinstance(name, str) or not name or Path(name).name != name or name in (".", ".."):
            raise ValueError(f"expected a plain filename in {source}")
        shutil.copyfile(source / name, target / name)


def blueprint_files(path):
    files = read(path / "blueprint.json")["files"]
    reserved = {*COMMON_FILES, "brief.json", "acceptance.json", "factory-record.json", ".gitignore",
                "blueprint.json", "samples", "output"}
    if not isinstance(files, list) or "solution.py" not in files or reserved.intersection(files):
        raise ValueError("the blueprint must supply solution.py and use distinct workspace filenames")
    return files


def engagement_copy(source, target):
    copy_files(source, target, ["brief.json", "acceptance.json"])
    samples = {case["sample"] for case in read(source / "acceptance.json")}
    copy_files(source / "samples", target / "samples", sorted(samples))


def commission(engagement, dest, blueprint=None):
    check_new(dest)
    brief = read(engagement / "brief.json")
    for key in ("customer", "user", "decision", "deliverable"):
        if not isinstance(brief.get(key), str) or not brief[key].strip():
            raise ValueError(f"brief needs a nonempty {key}")
    name = slug(brief["blueprint"])
    source = blueprint or BLUEPRINTS / name
    payload = blueprint_files(source)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=dest.parent) as tmp:
        staged = Path(tmp) / "poc"
        engagement_copy(engagement, staged)
        copy_files(COMMON, staged, COMMON_FILES)
        copy_files(source, staged, payload)
        (staged / ".gitignore").write_text(IGNORE)
        files = {key: hashlib.sha256((staged / key).read_bytes()).hexdigest()
                 for key in [*payload, *COMMON_FILES, "brief.json", "acceptance.json"]}
        write(staged / "factory-record.json", {"blueprint": name, "input_sha256": files})
        staged.rename(dest)


def run_builder(work):
    logs = work / ".runs"
    logs.mkdir(exist_ok=True, mode=0o700)
    command = ["codex", "exec", "--sandbox", "workspace-write", "--skip-git-repo-check", "--json", "-"]
    with (work / "work-order.md").open("rb") as order, (logs / "codex.jsonl").open("wb") as events:
        subprocess.run(command, cwd=work, stdin=order, stdout=events, check=True)


def evaluate(engagement, work, codex_build=False):
    # Run the factory's grader against the original brief, expectations and fixtures.
    cmd = [sys.executable, "-B", str(COMMON / "check.py"), "--project", str(work.resolve()),
           "--engagement", str(engagement.resolve()), "--json"]
    proc = subprocess.run(cmd, text=True, capture_output=True, timeout=60)
    if proc.returncode not in (0, 1) or not proc.stdout:
        raise ValueError(proc.stderr.strip() or "grader stopped before completing the cases")
    cases = json.loads(proc.stdout)
    guards = {}
    for p in [Path("brief.json"), Path("acceptance.json"),
              *(Path("samples") / c["sample"] for c in read(engagement / "acceptance.json"))]:
        if not (work / p).is_file() or (work / p).read_bytes() != (engagement / p).read_bytes():
            guards[str(p)] = "commissioned inputs changed"
    for key in COMMON_FILES:
        if not (work / key).is_file() or (work / key).read_bytes() != (COMMON / key).read_bytes():
            guards[key] = "factory instructions or grader changed"
    missing = []
    if codex_build and not ((work / "HANDOFF.md").is_file() and (work / "HANDOFF.md").read_text().strip()):
        missing.append("HANDOFF.md")
    report = {"passed": bool(cases) and all(c["passed"] for c in cases) and not guards and not missing,
              "builder": "codex" if codex_build else "blueprint replay",
              "cases": cases, "input_changes": guards, "missing_artifacts": missing}
    out = work / "output"
    out.mkdir(exist_ok=True)
    write(out / "acceptance-report.json", report)
    return report


def render_handoff(blueprint, work):
    entry = read(blueprint / "blueprint.json").get("demo_entry")
    if entry:
        if entry not in blueprint_files(blueprint):
            raise ValueError("demo_entry must name a file in the blueprint manifest")
        subprocess.run([sys.executable, "-B", entry], cwd=work, check=True, timeout=60)


def fresh_dir(prefix):
    build = ROOT / "build"
    build.mkdir(exist_ok=True)
    return Path(mkdtemp(prefix=prefix, dir=build))


def demo():
    out = fresh_dir("customer-pocs-")
    current = BLUEPRINTS / "invoice-intake"
    initial = out / "initial-blueprint"
    copy_files(current, initial, ["blueprint.json", *blueprint_files(current)])
    shutil.copyfile(ASSETS / "history/invoice-intake-initial.py", initial / "policy.py")
    summary = {}
    for name, blueprint in (("initial", initial), ("candidate", current)):
        summary[name] = {}
        for customer in ("juniper", "harbor"):
            engagement, work = EXAMPLES / customer, out / name / customer
            commission(engagement, work, blueprint)
            result = evaluate(engagement, work)
            summary[name][customer] = result
            passed = sum(row["passed"] for row in result["cases"])
            print(f"{name:10} {read(engagement / 'brief.json')['customer']:24} {passed}/{len(result['cases'])}")
            for row in result["cases"]:
                if not row["passed"]:
                    print(f"  {row['id']}: expected {row['expected']}, observed {row.get('actual', row.get('error'))}")
    eligible = all(result["passed"] for result in summary["candidate"].values())
    summary["decision"] = "eligible for SE review" if eligible else "hold"
    if eligible:
        # This copy simulates an approved release in the demo directory.
        release = out / "release-preview"
        copy_files(current, release, ["blueprint.json", *blueprint_files(current)])
        third = out / "reuse" / "cedar"
        commission(EXAMPLES / "cedar", third, release)
        summary["reuse"] = evaluate(EXAMPLES / "cedar", third)
        for work in (out / "candidate/juniper", out / "candidate/harbor", third):
            render_handoff(release, work)
        print(f"Fresh engagement: Cedar Repairs — {'PASS' if summary['reuse']['passed'] else 'HOLD'}")
    write(out / "replay.json", summary)
    print(f"Review decision: {summary['decision']}\nEvidence: {out / 'replay.json'}")
    if eligible:
        print(f"Show the customer: {out / 'candidate/harbor/output/review.html'}")
    return eligible and summary["reuse"]["passed"]


def new_factory(dest):
    check_new(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=dest.parent) as tmp:
        staged = Path(tmp) / "factory"
        assets = staged / "sales-factory"
        copy_files(COMMON, assets / "common", COMMON_FILES)
        copy_files(ASSETS / "history", assets / "history", ["invoice-intake-initial.py"])
        bp = BLUEPRINTS / "invoice-intake"
        copy_files(bp, assets / "blueprints/invoice-intake", ["blueprint.json", *blueprint_files(bp)])
        for customer in ("juniper", "harbor", "cedar"):
            engagement_copy(EXAMPLES / customer, assets / "examples" / customer)
        copy_files(ROOT, staged, ["se_factory.py"])
        copy_files(ASSETS, assets, ["QUICKSTART.md", "FACTORY.md"])
        shutil.copyfile(assets / "QUICKSTART.md", staged / "README.md")
        shutil.copyfile(assets / "FACTORY.md", staged / "AGENTS.md")
        (staged / ".gitignore").write_text(IGNORE + "sales-factory/engagements/\n")
        staged.rename(dest)
    print(f"Created {dest}. Open README.md to run the factory and add a solution pattern.")


def new_pattern(name):
    slug(name)
    blueprint = BLUEPRINTS / name
    engagement = ASSETS / "engagements" / (name + "-pilot")
    for path in (blueprint, engagement):
        check_new(path)
    blueprint.mkdir(parents=True)
    try:
        write(blueprint / "blueprint.json", {"files": ["solution.py"]})
        (blueprint / "solution.py").write_text('def solve(document, brief):\n'
                                               '    raise NotImplementedError("Implement the customer workflow")\n')
        engagement.parent.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(dir=engagement.parent) as tmp:
            example = Path(tmp) / "engagement"
            (example / "samples").mkdir(parents=True)
            write(example / "brief.json", {"blueprint": name, "customer": "Fictional pilot customer",
                  "user": "Service desk lead", "decision": "Which queue should receive this request?",
                  "deliverable": "A routing suggestion with a reason.", "settings": {}})
            cases = []
            for case_id, request, queue in (
                ("damaged-shipment", "A shipment arrived damaged.", "claims"),
                ("delivery-status", "When will my shipment arrive?", "delivery-status"),
                ("unclear-request", "I need some help.", "manual-review"),
            ):
                filename = case_id + ".json"
                write(example / "samples" / filename, {"request": request})
                cases.append({"id": case_id, "sample": filename, "expect": {"queue": queue}})
            write(example / "acceptance.json", cases)
            example.rename(engagement)
    except Exception:
        shutil.rmtree(blueprint)
        raise
    print(f"Created {blueprint} and {engagement}. Replace the example brief and case before building.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="command", required=True)
    subs.add_parser("demo", help="replay two engagements and prove reuse on a third")
    subs.add_parser("new-factory", help="create a standalone SE practice factory").add_argument("destination", type=Path)
    subs.add_parser("new-pattern", help="scaffold a solution pattern and pilot brief").add_argument("name")
    run = subs.add_parser("run", help="commission a customer workspace, optionally build with Codex, and grade it")
    run.add_argument("engagement", type=Path)
    run.add_argument("destination", type=Path)
    run.add_argument("--codex", action="store_true", help="invoke an installed, authenticated Codex CLI")
    replay = subs.add_parser("replay", help="grade a proposed blueprint across engagement briefs")
    replay.add_argument("blueprint", type=Path)
    replay.add_argument("engagements", type=Path, nargs="+")
    args = parser.parse_args()
    if args.command == "demo":
        return demo()
    if args.command == "new-factory":
        new_factory(args.destination)
    elif args.command == "new-pattern":
        new_pattern(args.name)
    elif args.command == "run":
        commission(args.engagement, args.destination)
        if args.codex:
            run_builder(args.destination)
        report = evaluate(args.engagement, args.destination, codex_build=args.codex)
        print(f"{'PASS' if report['passed'] else 'HOLD'} — {args.destination / 'output/acceptance-report.json'}")
        if report["passed"]:
            render_handoff(BLUEPRINTS / slug(read(args.engagement / "brief.json")["blueprint"]), args.destination)
        return report["passed"]
    else:
        out = fresh_dir("replay-")
        passed = True
        for i, eng in enumerate(args.engagements, 1):
            work = out / str(i)
            commission(eng, work, args.blueprint)
            result = evaluate(eng, work)
            passed = passed and result["passed"]
            print(f"{'PASS' if result['passed'] else 'HOLD'} — {eng} — {work / 'output/acceptance-report.json'}")
        return passed
    return True


if __name__ == "__main__":
    try:
        sys.exit(0 if main() else 1)
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        sys.exit(f"Factory stopped: {exc}")
