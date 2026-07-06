def clamp_limit(value: int | None, *, default: int = 50, maximum: int = 100) -> int:
    """Clamp a pagination limit to a safe positive range."""
    if value is None:
        return default
    return max(1, min(value, maximum))
