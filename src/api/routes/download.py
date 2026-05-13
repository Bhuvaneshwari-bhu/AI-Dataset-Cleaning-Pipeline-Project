"""GET /download-cleaned/{upload_id} — download the cleaned CSV."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from api.services.storage import StorageManager, get_storage
from logger import get_logger

logger = get_logger("api.download")

router = APIRouter(tags=["Reports"])


@router.get(
    "/download-cleaned/{upload_id}",
    response_class=FileResponse,
    status_code=status.HTTP_200_OK,
    summary="Download the cleaned CSV",
    description=(
        "Download the cleaned and transformed dataset produced by the pipeline. "
        "Requires `POST /analyze/{upload_id}` to have been called first."
    ),
)
def download_cleaned(
    upload_id: str,
    storage: StorageManager = Depends(get_storage),
) -> FileResponse:
    if not storage.upload_exists(upload_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Upload '{upload_id}' not found.",
        )
    if not storage.cleaned_exists(upload_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Cleaned file for '{upload_id}' not found. Run POST /analyze/{upload_id} first."
            ),
        )

    cleaned_path = storage.cleaned_path(upload_id)
    short_id = upload_id[:8]
    return FileResponse(
        path=str(cleaned_path),
        filename=f"cleaned_{short_id}.csv",
        media_type="text/csv",
    )
