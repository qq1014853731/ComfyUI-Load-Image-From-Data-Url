MISSING_POLICIES = ("None", "Placeholder", "Throw error")


def validate_missing_policy(policy: str, name: str):
    if policy not in MISSING_POLICIES:
        raise ValueError(f"`{name}` must be one of: {', '.join(MISSING_POLICIES)}.")
