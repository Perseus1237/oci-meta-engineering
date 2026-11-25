"""Original selection rule from the first engagement."""


def select(observations):
    if not observations:
        return None, "missing"
    return max(observations, key=lambda item: item["confidence"]), None
