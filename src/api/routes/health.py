"""GET /health — liveness probe."""

from __future__ import annotations

from fastapi import APIRouter, status

from api.schemas.responses import HealthResponse

router = APIRouter(tags=["Monitoring"])

_VERSION = "1.0.0"
_PIPELINE_MODULES = [
    "loader",
    "validator",
    "cleaner",
    "anomaly_detector",
    "drift_detector",
    "report_generator",
]


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Returns API status, version, and the list of available pipeline modules.",
)
def health_check() -> HealthResponse:
    return HealthResponse(
        status="ok",
        version=_VERSION,
        pipeline_modules=_PIPELINE_MODULES,
    )
