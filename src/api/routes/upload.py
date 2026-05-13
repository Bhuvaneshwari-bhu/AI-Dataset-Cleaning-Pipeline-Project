"""POST /upload — accept a CSV file and store it for later analysis."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from api.schemas.responses import UploadResponse
from api.services.storage import StorageManager, get_storage
from logger import get_logger

logger = get_logger("api.upload")

router = APIRouter(tags=["Data Ingestion"])

_MAX_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB hard limit


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a CSV dataset",
    description=(
        "Upload a CSV file to begin the pipeline. "
        "Returns an **upload_id** that must be passed to `POST /analyze/{upload_id}`. "
        "Only `.csv` files are accepted. Maximum file size: 100 MB."
    ),
)
def upload_file(
    file: UploadFile = File(..., description="CSV file to process"),
    storage: StorageManager = Depends(get_storage),
) -> UploadResponse:
    filename = file.filename or ""

    if not filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only .csv files are accepted.",
        )

    try:
        raw = file.file.read()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not read uploaded file: {exc}",
        ) from exc

    if len(raw) == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded file is empty.",
        )

    if len(raw) > _MAX_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"File is {len(raw):,} bytes; "
                f"maximum allowed is {_MAX_SIZE_BYTES:,} bytes (100 MB)."
            ),
        )

    upload_id = str(uuid.uuid4())
    storage.upload_path(upload_id).write_bytes(raw)
    logger.info("Upload saved — id=%s filename=%s size=%d B", upload_id, filename, len(raw))

    return UploadResponse(
        upload_id=upload_id,
        filename=filename,
        size_bytes=len(raw),
        message="File uploaded. Send POST /analyze/{upload_id} to run the pipeline.",
    )
