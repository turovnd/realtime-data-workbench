from workbench.schemas.common import ErrorResponse

ERRORS: dict[int | str, dict[str, object]] = {
    400: {
        "model": ErrorResponse,
        "description": "Invalid, tampered, evicted or filter/workspace-mismatched cursor",
    },
    401: {
        "model": ErrorResponse,
        "description": "Invalid credentials, missing, expired or revoked bearer session",
    },
    403: {"model": ErrorResponse, "description": "Mutation origin is not allowed"},
    409: {
        "model": ErrorResponse,
        "description": (
            "Conflicting operation, exhausted capacity or selection outside this workspace"
        ),
    },
    410: {"model": ErrorResponse, "description": "Frozen view expired; restart without a cursor"},
    413: {
        "model": ErrorResponse,
        "description": "A declared request body of at most 16 KiB is required",
    },
    429: {
        "model": ErrorResponse,
        "description": "Authentication admission limit reached",
        "headers": {
            "Retry-After": {
                "description": "Retry delay in seconds",
                "schema": {"type": "integer", "example": 900},
            }
        },
    },
}


def errors(*statuses: int) -> dict[int | str, dict[str, object]]:
    return {status: ERRORS[status] for status in statuses}
