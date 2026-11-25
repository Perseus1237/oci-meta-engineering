"""Candidate rule for teams that inherit tags through var.common_tags."""


def with_owner(tags, owner):
    # Give inherited tags precedence so a different existing owner survives for review.
    shared = '${merge({owner = "' + owner + '"}, var.common_tags)}'
    if tags == "${var.common_tags}" or tags == shared:
        return shared
    if not isinstance(tags, dict):
        raise ValueError("unsupported tag expression")
    if "owner" in tags and tags["owner"] != owner:
        raise ValueError("existing owner differs")
    return {**tags, "owner": owner}
