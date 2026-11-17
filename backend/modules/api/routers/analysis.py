from fastapi import APIRouter, HTTPException, Response

from common.infrastructure.database import run_transaction
from common.logic.analysis import start_analysis
from common.schemas.analysis import AnalysisInput
from common.schemas.feedback import RecordView
from modules.api.dependencies import AppSettings, Database, Dispatcher, Workspace
from modules.api.routers.responses import errors

router = APIRouter(prefix="/api/feedback", tags=["Feedback"])


@router.post(
    "/{record_id}/analysis",
    response_model=RecordView,
    status_code=202,
    operation_id="analyzeFeedback",
    summary="Request a new AI analysis of one feedback message",
    description=(
        "Creates a new durable analysis run using the configured real provider. Previous "
        "results remain visible while it runs. Retain identity for network retries: a replay "
        "returns 200 without another run; a new request returns 202. One active run per "
        "feedback; concurrent requests return 409. There is no lifetime run limit. "
        "Record responses include the latest ten jobs and successful outputs. Missing or foreign "
        "records return 404. Real-provider mode and calls must be enabled, otherwise 503. "
        "Provider budgets, timeouts, output validation and three-attempt limit still apply; "
        "acceptance does not guarantee provider availability or successful completion."
    ),
    responses={
        200: {"model": RecordView, "description": "Previously admitted request"},
        **errors(401, 403, 404, 409, 413, 503),
    },
)
async def analyze(
    record_id: str,
    request: AnalysisInput,
    response: Response,
    database: Database,
    workspace_id: Workspace,
    settings: AppSettings,
    dispatcher: Dispatcher,
) -> RecordView:
    if not settings.live_calls_enabled:
        raise HTTPException(
            status_code=503,
            detail="AI analysis is not configured. Enable the real provider to continue.",
        )
    record, inserted = await run_transaction(
        database, start_analysis, workspace_id, record_id, request, settings.provider_id
    )
    response.status_code = 202 if inserted else 200
    await dispatcher.notify(workspace_id, record_ids=[record.id])
    return record
