"""Ownership rule for Terraform JSON freeform_tags."""


def with_owner(tags, owner):
    if not isinstance(tags, dict):
        raise ValueError("unsupported tag expression")
    if "owner" in tags and tags["owner"] != owner:
        raise ValueError("existing owner differs")
    return {**tags, "owner": owner}
