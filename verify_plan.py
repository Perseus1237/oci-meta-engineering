"""Check the planned effects of the pilot tag ticket against a trusted owner."""

import argparse
import json
import re
import sys
from pathlib import Path

TARGET = "oci_objectstorage_bucket.pilot"


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def any_unknown(mask):
    if isinstance(mask, dict):
        return any(any_unknown(value) for value in mask.values())
    if isinstance(mask, list):
        return any(any_unknown(value) for value in mask)
    return mask is not False


def verify(plan, owner):
    require(isinstance(plan, dict) and re.fullmatch(r"1\.\d+", str(plan.get("format_version"))),
            "expected a Terraform JSON plan with format 1.x")
    require(isinstance(owner, str) and re.fullmatch(r"[a-z][a-z0-9-]{0,62}", owner),
            "invalid expected owner")
    require(plan.get("errored", False) is False and plan.get("complete", True) is True
            and plan.get("applyable", True) is True, "plan is incomplete or errored")
    for key in ("resource_drift", "deferred_changes", "action_invocations"):
        require(not plan.get(key), f"plan includes {key}")
    require(all(check.get("status") == "pass" for check in plan.get("checks", [])),
            "plan contains an unresolved or failed check")
    for change in plan.get("output_changes", {}).values():
        require(change.get("actions") == ["no-op"], "unexpected output change")

    changes = plan.get("resource_changes")
    require(isinstance(changes, list), "missing resource changes")
    updates = []
    for resource in changes:
        change = resource["change"]
        require(not any(k in resource for k in ("previous_address", "deposed"))
                and "importing" not in change, "move, deposed instance or import in plan")
        if change["actions"] == ["no-op"]:
            continue
        require(resource["address"] == TARGET and change["actions"] == ["update"],
                "expected only an in-place update of the pilot bucket")
        require(resource.get("mode") == "managed" and resource.get("type") == "oci_objectstorage_bucket"
                and resource.get("provider_name") == "registry.terraform.io/oracle/oci",
                "unexpected resource type or provider")
        updates.append(change)
    require(len(updates) == 1, "expected exactly one bucket update")
    change = updates[0]
    require("after_unknown" in change and not any_unknown(change["after_unknown"]),
            "planned values are unknown")
    before, after = change["before"], change["after"]
    require(isinstance(before, dict) and isinstance(after, dict), "missing bucket values")
    require(before.get("access_type") == "NoPublicAccess", "expected a private bucket")
    tags = before.get("freeform_tags")
    if tags is None:
        tags = {}
    require(isinstance(tags, dict) and "owner" not in tags, "expected an unowned bucket")
    expected = {**before, "freeform_tags": {**tags, "owner": owner}}
    require(after == expected, "plan differs from the single requested owner-tag addition")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    parser.add_argument("--owner", required=True, help="expected team slug from the reviewed ticket")
    args = parser.parse_args()
    try:
        verify(json.loads(args.plan.read_text()), args.owner)
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        sys.exit(f"Rejected plan: {exc}")
    print(f"Accepted one in-place update of {TARGET} adding owner={args.owner}.")
