"""Create a team-owned Codex factory from the reviewed template files."""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parent
SKILL = Path(".agents/skills/tag-bucket")
RULE = SKILL / "scripts/tag_rule.py"
WORKER = SKILL / "scripts/tag_bucket.py"
BUCKET = Path("infra/bucket.tf.json")
# An explicit payload keeps local state, credentials and provider caches out of copies.
PAYLOAD = (
    Path("README.md"), Path("AGENTS.md"), Path(".gitignore"), Path("tickets/owner-tag.md"),
    SKILL / "SKILL.md", RULE, WORKER, BUCKET, Path("infra/variables.tf"),
    Path("infra/versions.tf"), Path("infra/.terraform.lock.hcl"),
)


def create(spec, destination, candidate_rule=None):
    if not isinstance(spec, dict) or set(spec) != {"name", "owner", "tag_source"}:
        raise ValueError("spec requires exactly name, owner and tag_source")
    for key in ("name", "owner"):
        if not isinstance(spec[key], str) or not re.fullmatch(r"[a-z][a-z0-9-]{0,62}", spec[key]):
            raise ValueError(f"{key} must be a lowercase slug of 1 to 63 characters")
    if spec["tag_source"] not in ("literal", "common_tags"):
        raise ValueError("tag_source must be literal or common_tags")
    if destination.exists() or destination.is_symlink():
        raise ValueError(f"destination already exists: {destination}")

    destination.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    with TemporaryDirectory(dir=destination.parent) as tmp:
        staged = Path(tmp) / "factory"
        for relative in PAYLOAD:
            source = candidate_rule if relative == RULE and candidate_rule else ROOT / "template" / relative
            data = source.read_bytes()
            digest.update(relative.as_posix().encode() + b"\0" + hashlib.sha256(data).digest())
            target = staged / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        if spec["tag_source"] == "common_tags":
            path = staged / BUCKET
            module = json.loads(path.read_text())
            module["resource"]["oci_objectstorage_bucket"]["pilot"]["freeform_tags"] = "${var.common_tags}"
            path.write_text(json.dumps(module, indent=2) + "\n")
        manifest = {**spec, "template_sha256": digest.hexdigest()}
        (staged / "factory.json").write_text(json.dumps(manifest, indent=2) + "\n")
        staged.rename(destination)
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path)
    parser.add_argument("destination", type=Path, help="a new directory for the team checkout")
    args = parser.parse_args()
    try:
        manifest = create(json.loads(args.spec.read_text()), args.destination)
    except (ValueError, OSError) as exc:
        sys.exit(f"Cannot create factory: {exc}")
    print(f"Created {manifest['name']} for {manifest['owner']} at {args.destination}")
