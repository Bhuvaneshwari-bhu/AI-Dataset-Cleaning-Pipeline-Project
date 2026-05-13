"""
PipelineService — wires the existing pipeline modules together for the API.

This module deliberately contains no business logic: it delegates entirely to
loader, validator, cleaner, anomaly_detector, and report_generator, then maps
their outputs to Pydantic response models.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

# Safety-net: ensure src/ is importable if this module is loaded independently
_SRC_DIR: Path = Path(__file__).resolve().parents[2]
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from anomaly_detector import AnomalyDetector
from api.schemas.requests import AnalyzeRequest
from api.schemas.responses import (
    AnalyzeResponse,
    ColumnProfileInfo,
    FormatViolationInfo,
    MissingValueInfo,
    OutlierInfo,
    RangeViolationInfo,
)
from api.services.storage import StorageManager
from cleaner import DataCleaner
from loader import load_csv
from logger import get_logger
from report_generator import ReportGenerator
from validator import DataValidator, load_schema_from_yaml

logger = get_logger("api.pipeline")

_DEFAULT_SCHEMA_FILE = "config/schema.yaml"


def run_pipeline(
    upload_id: str,
    request: AnalyzeRequest,
    storage: StorageManager,
) -> AnalyzeResponse:
    """
    Execute the full cleaning/validation pipeline for one uploaded file.

    Stages
    ------
    1. Load         — read the uploaded CSV
    2. Validate     — run schema + profiling + quality scoring
    3. Clean        — impute, deduplicate, normalise column names
    4. Detect       — IQR or Z-score outlier detection
    5. Export       — write cleaned CSV to storage/cleaned/
    6. Report       — generate HTML quality report to storage/reports/{upload_id}/

    Parameters
    ----------
    upload_id : UUID string assigned at upload time
    request   : analysis options (anomaly method, fill strategy, optional schema path)
    storage   : StorageManager that resolves all file paths
    """
    upload_path = storage.upload_path(upload_id)
    logger.info("Pipeline start — upload_id=%s", upload_id)

    # ── Stage 1: Load ──────────────────────────────────────────────────
    df_raw = load_csv(str(upload_path))
    logger.info("Loaded %d rows × %d columns", len(df_raw), len(df_raw.columns))

    # ── Stage 2: Validate ──────────────────────────────────────────────
    schema_file = request.schema_file or _DEFAULT_SCHEMA_FILE
    schema: dict[str, Any] | None = None
    if os.path.exists(schema_file):
        try:
            schema = load_schema_from_yaml(schema_file)
            logger.info("Schema loaded from '%s'", schema_file)
        except Exception as exc:
            logger.warning("Schema load failed (%s) — proceeding without schema", exc)

    validator = DataValidator(schema=schema)
    validation_result = validator.run(df_raw)

    # ── Stage 3: Clean ─────────────────────────────────────────────────
    cleaner = DataCleaner(
        fill_strategy=request.fill_strategy,
        drop_duplicate=True,
        strip_whitespace=True,
    )
    df_clean, clean_log = cleaner.run(df_raw)

    # ── Stage 4: Anomaly Detection ─────────────────────────────────────
    detector = AnomalyDetector(
        method=request.anomaly_method,
        threshold=request.anomaly_threshold,
    )
    anomaly_report = detector.detect(df_clean)

    # ── Stage 5: Export cleaned CSV ────────────────────────────────────
    cleaned_path = storage.cleaned_path(upload_id)
    df_clean.to_csv(str(cleaned_path), index=False)
    logger.info("Cleaned CSV → '%s'", cleaned_path)

    # ── Stage 6: Generate HTML report ──────────────────────────────────
    report_dir = storage.report_dir(upload_id)
    report_dir.mkdir(parents=True, exist_ok=True)
    ReportGenerator(output_dir=str(report_dir)).generate(
        df_raw=df_raw,
        df_clean=df_clean,
        validation_result=validation_result,
        anomaly_report=anomaly_report,
        clean_log=clean_log,
    )
    logger.info("Pipeline complete — upload_id=%s", upload_id)

    # ── Build Pydantic response ────────────────────────────────────────
    missing_summary = {
        col: MissingValueInfo(count=v["count"], pct=v["pct"])
        for col, v in validation_result.missing_summary.items()
    }

    format_violations = {
        col: FormatViolationInfo(
            pattern=v["pattern"],
            invalid_count=v["invalid_count"],
            sample_values=list(v["sample_values"]),
        )
        for col, v in validation_result.format_violations.items()
    }

    out_of_range = {
        col: RangeViolationInfo(
            violations=v["violations"],
            min_found=float(v["min_found"]),
            max_found=float(v["max_found"]),
            expected_min=v["expected_range"][0],
            expected_max=v["expected_range"][1],
        )
        for col, v in validation_result.out_of_range.items()
    }

    profiles = {
        col: ColumnProfileInfo(
            dtype=p.dtype,
            null_count=p.null_count,
            null_pct=p.null_pct,
            unique_count=p.unique_count,
            min_val=p.min_val,
            max_val=p.max_val,
            mean=p.mean,
            median=p.median,
            std=p.std,
        )
        for col, p in validation_result.profiles.items()
    }

    outlier_summary = {
        col: OutlierInfo(count=v["count"], pct=v["pct"])
        for col, v in anomaly_report.column_results.items()
    }

    return AnalyzeResponse(
        upload_id=upload_id,
        quality_score=validation_result.quality_score,
        passed=validation_result.passed,
        row_count_raw=len(df_raw),
        row_count_clean=len(df_clean),
        column_count=len(df_raw.columns),
        duplicate_count=validation_result.duplicate_count,
        missing_summary=missing_summary,
        type_issues=validation_result.type_issues,
        schema_violations=dict(validation_result.schema_violations),
        format_violations=format_violations,
        out_of_range=out_of_range,
        profiles=profiles,
        total_outliers=anomaly_report.total_outliers,
        outlier_summary=outlier_summary,
        clean_log=clean_log,
        report_url=f"/report/{upload_id}",
        download_url=f"/download-cleaned/{upload_id}",
    )
