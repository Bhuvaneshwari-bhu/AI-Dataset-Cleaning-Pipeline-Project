"""Request body schemas for the pipeline API."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    """Options that control how the pipeline processes an uploaded dataset."""

    anomaly_method: Literal["iqr", "zscore"] = Field(
        default="iqr",
        description=(
            "Outlier detection algorithm. 'iqr' is robust for skewed distributions; "
            "'zscore' works better for near-normal distributions."
        ),
    )
    anomaly_threshold: float = Field(
        default=1.5,
        gt=0,
        description="IQR multiplier (iqr mode) or standard-deviation cutoff (zscore mode).",
    )
    fill_strategy: Literal["median", "mean", "mode", "drop"] = Field(
        default="median",
        description="Missing-value imputation strategy applied to numeric columns.",
    )
    schema_file: str | None = Field(
        default=None,
        description=(
            "Path to a YAML schema file that defines per-column validation rules "
            "(dtype, nullable, min/max, allowed_values, regex). "
            "Falls back to config/schema.yaml when omitted. "
            "Validation is skipped when the resolved file does not exist."
        ),
    )
