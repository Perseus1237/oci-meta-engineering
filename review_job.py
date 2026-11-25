"""Verify a completed OCI plan job against a committed candidate and ticket."""

import argparse
import hashlib
import io
import json
import re
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import BadZipFile, ZipFile

from verify_plan import verify


def zip_contents(archive):
    files = {}
    with ZipFile(archive) as bundle:
        for entry in bundle.infolist():
            if entry.is_dir():
                continue
            if entry.filename in files:
                raise ValueError("duplicate file in configuration archive")
            files[entry.filename] = hashlib.sha256(bundle.read(entry)).hexdigest()
    return files


def check_job(job, stack_id, job_id):
    if job.get("id") != job_id or job.get("stack-id") != stack_id:
        raise ValueError("job and stack must match the requested IDs")
    if job.get("operation") != "PLAN" or job.get("lifecycle-state") != "SUCCEEDED":
        raise ValueError("expected a successful PLAN job")


def review(factory, revision, owner, stack_id, job_id, evidence):
    if not re.fullmatch(r"[a-f0-9]{40}|[a-f0-9]{64}", revision):
        raise ValueError("supply the full reviewed Git commit ID")
    if evidence.exists() or evidence.is_symlink():
        raise ValueError("choose a new evidence directory")
    git = ["git", "-C", str(factory)]
    commit = subprocess.check_output([*git, "rev-parse", "--verify", revision + "^{commit}"],
                                     text=True).strip()
    if commit != revision:
        raise ValueError("revision must identify a commit")
    candidate = subprocess.check_output([*git, "archive", "--format=zip", revision + ":infra"])
    expected = zip_contents(io.BytesIO(candidate))

    oci_job = ["oci", "resource-manager", "job"]
    response = subprocess.check_output([*oci_job, "get", "--job-id", job_id, "--output", "json"])
    check_job(json.loads(response)["data"], stack_id, job_id)
    evidence.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=evidence.parent) as tmp:
        staged = Path(tmp) / "review"
        staged.mkdir(mode=0o700)
        config = staged / "job-config.zip"
        subprocess.run([*oci_job, "get-job-tf-config", "--job-id", job_id,
                        "--file", str(config)], check=True)
        if zip_contents(config) != expected:
            raise ValueError("job configuration differs from the reviewed infra/ tree")
        plan = staged / "job.plan.json"
        subprocess.run([*oci_job, "get-job-tf-plan", "--job-id", job_id,
                        "--tf-plan-format", "JSON", "--file", str(plan)], check=True)
        data = plan.read_bytes()
        verify(json.loads(data), owner)
        summary = {
            "ticket": "owner-tag", "owner": owner, "commit": revision, "stack_id": stack_id,
            "plan_job_id": job_id, "plan_sha256": hashlib.sha256(data).hexdigest(),
            "config_files_sha256": expected, "result": "passed",
        }
        (staged / "review.json").write_text(json.dumps(summary, indent=2) + "\n")
        staged.rename(evidence)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--factory", type=Path, required=True, help="generated team Git checkout")
    parser.add_argument("--revision", required=True, help="full candidate commit SHA")
    parser.add_argument("--owner", required=True, help="expected owner from the approved ticket")
    parser.add_argument("--stack-id", required=True)
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--evidence", type=Path, required=True, help="new private output directory")
    args = parser.parse_args()
    try:
        review(args.factory, args.revision, args.owner, args.stack_id, args.job_id, args.evidence)
    except (ValueError, KeyError, TypeError, AttributeError, OSError, BadZipFile,
            subprocess.CalledProcessError) as exc:
        sys.exit(f"Review stopped: {exc}")
    print(f"Plan and source verified. Review record: {args.evidence / 'review.json'}")
