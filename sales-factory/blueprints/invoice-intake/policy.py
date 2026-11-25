"""Select field evidence for one customer-configured requirement."""


def select(observations):
    if not observations:
        return None, "missing"
    if len({item["text"] for item in observations}) > 1:
        return None, "conflicting values"
    return max(observations, key=lambda item: item["confidence"]), None
