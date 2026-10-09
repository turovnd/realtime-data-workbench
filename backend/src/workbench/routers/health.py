from fastapi import APIRouter

from workbench.dependencies import AppSettings, Database
from workbench.infrastructure.database import check_database
from workbench.schemas.common import HealthResponse

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
