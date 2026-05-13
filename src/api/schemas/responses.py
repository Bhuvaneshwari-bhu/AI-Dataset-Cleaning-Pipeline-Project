"""Response body schemas for the pipeline API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

# ── Upload ────────────────────────────────────────────────────────────────────


class UploadResponse(BaseModel):
    upload_id: str
    filename: str
    size_bytes: int
    message: str


# ── Analyze sub-models ────────────────────────────────────────────────────────


class MissingValueInfo(BaseModel):
    """Missing-value counts for one column."""

    count: int
    pct: float


class OutlierInfo(BaseModel):
    """Outlier counts for one numeric column."""

    count: int
    pct: float


class FormatViolationInfo(BaseModel):
    """Regex validation failures for one column."""

    pattern: str
    invalid_count: int
    sample_values: list[Any]


class RangeViolationInfo(BaseModel):
    """Numeric range violations for one column."""

    violations: int
    min_found: float
    max_found: float
    expected_min: float | None
    expected_max: float | None


class ColumnProfileInfo(BaseModel):
    """Descriptive statistics for one column, collected during validation."""

    dtype: str
    null_count: int
    null_pct: float
    unique_count: int
    min_val: float | None = None
    max_val: float | None = None
    mean: float | None = None
    median: float | None = None
    std: float | None = None


# ── Analyze ───────────────────────────────────────────────────────────────────


class AnalyzeResponse(BaseModel):
    """Structured quality report returned after running the full pipeline."""

    upload_id: str
    quality_score: float
    passed: bool
    row_count_raw: int
    row_count_clean: int
    column_count: int
    duplicate_count: int
    missing_summary: dict[str, MissingValueInfo]
    type_issues: list[str]
    schema_violations: dict[str, list[str]]
    format_violations: dict[str, FormatViolationInfo]
    out_of_range: dict[str, RangeViolationInfo]
    profiles: dict[str, ColumnProfileInfo]
    total_outliers: int
    outlier_summary: dict[str, OutlierInfo]
    clean_log: list[str]
    report_url: str
    download_url: str


# ── Health ────────────────────────────────────────────────────────────────────


class HealthResponse(BaseModel):
    status: str
    version: str
    pipeline_modules: list[str]
