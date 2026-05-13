"""
StorageManager — filesystem layout for uploaded, cleaned, and reported artefacts.

Layout
------
    storage/
      uploads/   {upload_id}.csv        — raw uploaded files
      cleaned/   {upload_id}.csv        — output of DataCleaner
      reports/   {upload_id}/           — ReportGenerator output directory
                   report.html
                   missing_values.png
                   dist_*.png
"""

from __future__ import annotations

from pathlib import Path

# Navigate from src/api/services/storage.py → project root (4 levels up)
_PROJECT_ROOT: Path = Path(__file__).resolve().parents[3]
_DEFAULT_STORAGE_ROOT: Path = _PROJECT_ROOT / "storage"


class StorageManager:
    """Centralises all path logic so the rest of the API never hard-codes paths."""

    def __init__(self, root: Path | str | None = None) -> None:
        self.root: Path = Path(root) if root is not None else _DEFAULT_STORAGE_ROOT
        self.uploads_dir: Path = self.root / "uploads"
        self.cleaned_dir: Path = self.root / "cleaned"
        self.reports_dir: Path = self.root / "reports"

    def ensure_dirs(self) -> None:
        """Create all storage sub-directories if they do not already exist."""
        for directory in (self.uploads_dir, self.cleaned_dir, self.reports_dir):
            directory.mkdir(parents=True, exist_ok=True)

    # ── Per-upload paths ──────────────────────────────────────────────────────

    def upload_path(self, upload_id: str) -> Path:
        return self.uploads_dir / f"{upload_id}.csv"

    def cleaned_path(self, upload_id: str) -> Path:
        return self.cleaned_dir / f"{upload_id}.csv"

    def report_dir(self, upload_id: str) -> Path:
        """Directory passed to ReportGenerator; contains report.html + PNGs."""
        return self.reports_dir / upload_id

    def report_html_path(self, upload_id: str) -> Path:
        return self.report_dir(upload_id) / "report.html"

    # ── Existence checks ──────────────────────────────────────────────────────

    def upload_exists(self, upload_id: str) -> bool:
        return self.upload_path(upload_id).exists()

    def report_exists(self, upload_id: str) -> bool:
        return self.report_html_path(upload_id).exists()

    def cleaned_exists(self, upload_id: str) -> bool:
        return self.cleaned_path(upload_id).exists()


def get_storage() -> StorageManager:
    """FastAPI dependency: returns a StorageManager backed by the default storage root."""
    manager = StorageManager()
    manager.ensure_dirs()
    return manager
