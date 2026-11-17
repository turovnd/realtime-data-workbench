from fastapi import APIRouter

from common.infrastructure.database import check_database
from common.schemas.common import HealthResponse
from modules.api.dependencies import AppSettings, Database

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    operation_id="getHealth",
    summary="Check API/database readiness",
    description=(
        "Checks a PostgreSQL connection. It does not prove worker progress or "
        "model-provider availability. No credentials or worker internals are "
        "returned."
    ),
)
async def health(database: Database, settings: AppSettings) -> HealthResponse:
    await check_database(database)
    return HealthResponse(provider=settings.provider_id)
