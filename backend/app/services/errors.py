class ServiceError(RuntimeError):
    """A safe, instructor-readable provider failure (never include keys/raw responses)."""

