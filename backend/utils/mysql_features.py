def mysql_required_response(feature: str, **extra) -> dict:
    """Standard response when a feature requires a live MySQL workspace database."""
    return {
        "executed": False,
        "message": f"{feature} requires a MySQL connection.",
        "status": "skipped",
        **extra,
    }
