"""Run from a generated factory. Only the ticket's Terraform file is writable."""

import json
import re
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile

from tag_rule import with_owner


def run():
    owner = json.loads(Path("factory.json").read_text())["owner"]
    if not isinstance(owner, str) or not re.fullmatch(r"[a-z][a-z0-9-]{0,62}", owner):
        raise ValueError("invalid owner slug")

    path = Path("infra/bucket.tf.json")
    module = json.loads(path.read_text())
    bucket = module["resource"]["oci_objectstorage_bucket"]["pilot"]
    tags = bucket.get("freeform_tags", {})
    updated = with_owner(tags, owner)
    if tags == updated:
        print("Owner rule already present in the configuration.")
        return

    bucket["freeform_tags"] = updated
    with NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as handle:
        pending = Path(handle.name)
        try:
            json.dump(module, handle, indent=2)
            handle.write("\n")
            handle.close()
            pending.chmod(path.stat().st_mode & 0o777)
            pending.replace(path)
        finally:
            pending.unlink(missing_ok=True)
    print(f"Prepared owner={owner} for oci_objectstorage_bucket.pilot.")


if __name__ == "__main__":
    try:
        run()
    except (ValueError, KeyError, OSError, TypeError) as exc:
        sys.exit(f"Ticket blocked: {exc}")
