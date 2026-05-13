"""POST /analyze/{upload_id} — run the full pipeline on an uploaded file."""

from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, status

from api.schemas.requests import AnalyzeRequest
from api.schemas.responses import AnalyzeResponse
from api.services.pipeline import run_pipeline
from api.services.storage import StorageManager, get_storage
from logger import get_logger

logger = get_logger("api.analyze")

router = APIRouter(tags=["Pipeline"])


@router.post(
    "/analyze/{upload_id}",
    response_model=AnalyzeResponse,
    status_code=status.HTTP_200_OK,
    summary="Run the cleaning and validation pipeline",
    description=(
        "Executes the full pipeline on a previously uploaded file:\n\n"
        "1. **Load** — read the CSV\n"
        "2. **Validate** — schema checks, profiling, quality score\n"
        "3. **Clean** — impute missing values, remove duplicates, normalise columns\n"
        "4. **Detect** — IQR or Z-score outlier detection\n"
        "5. **Export** — save cleaned CSV to `storage/cleaned/`\n"
        "6. **Report** — generate HTML report to `storage/reports/{upload_id}/`\n\n"
        "All pipeline options have sensible defaults; the request body is optional."
    ),
)
def analyze(
    upload_id: str,
    request: AnalyzeRequest = Body(default=AnalyzeRequest()),
    storage: StorageManager = Depends(get_storage),
) -> AnalyzeResponse:
    if not storage.upload_exists(upload_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Upload '{upload_id}' not found. Upload a file first via POST /upload.",
        )

    try:
        return run_pipeline(upload_id, request, storage)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    except Exception as exc:
        logger.exception("Pipeline error — upload_id=%s", upload_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline execution failed: {exc}",
        ) from exc
