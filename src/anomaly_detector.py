"""
anomaly_detector.py
Detects statistical anomalies (outliers) in numeric columns.

Two strategies are provided:
  IQR    – classic fence method, robust and interpretable.
           Threshold = IQR multiplier: 1.5 (standard), 3.0 (extreme only).
  ZScore – standard-deviation based, better for near-normal distributions.
           Threshold = number of std-devs: typically 2.5–3.0.
"""

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from logger import get_logger

logger = get_logger("anomaly_detector")


@dataclass
class AnomalyReport:
    """Holds the findings for every numeric column."""
    method: str
    column_results: dict[str, dict[str, Any]] = field(default_factory=dict)
    total_outliers: int = 0


class AnomalyDetector:
    """
    Detects and optionally removes outliers from numeric columns.

    Parameters
    ----------
    method    : "iqr" or "zscore"
    threshold : IQR multiplier (iqr) or number of std-devs (zscore)

    Usage
    -----
        detector = AnomalyDetector(method="iqr", threshold=1.5)
        report   = detector.detect(df)
        clean_df = detector.remove_outliers(df)
    """

    SUPPORTED_METHODS = ("iqr", "zscore")

    def __init__(self, method: str = "iqr", threshold: float = 1.5) -> None:
        if method not in self.SUPPORTED_METHODS:
            raise ValueError(f"method must be one of {self.SUPPORTED_METHODS}, got '{method}'.")
        self.method = method
        self.threshold = threshold

    # ── Private mask builders ────────────────────────────────────────────────

    def _iqr_mask(self, series: "pd.Series[float]") -> "pd.Series[bool]":
        """Return a boolean mask where True = outlier (IQR method)."""
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - self.threshold * iqr
        upper = q3 + self.threshold * iqr
        return (series < lower) | (series > upper)

    def _zscore_mask(self, series: "pd.Series[float]") -> "pd.Series[bool]":
        """Return a boolean mask where True = outlier (Z-score method)."""
        mean = series.mean()
        std = series.std()
        if std == 0:
            return pd.Series(False, index=series.index)
        z = (series - mean).abs() / std
        return z > self.threshold

    # ── Public API ───────────────────────────────────────────────────────────

    def detect(self, df: pd.DataFrame) -> AnomalyReport:
        """Scan all numeric columns and return an AnomalyReport."""
        logger.info(
            "Running '%s' outlier detection (threshold=%.2f) on %d rows",
            self.method, self.threshold, len(df),
        )
        report = AnomalyReport(method=self.method)
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        for col in numeric_cols:
            series = df[col].dropna()
            mask = (
                self._iqr_mask(series) if self.method == "iqr"
                else self._zscore_mask(series)
            )
            outlier_indices = series[mask].index.tolist()
            count = len(outlier_indices)
            report.column_results[col] = {
                "outlier_indices": outlier_indices,
                "count": count,
                "pct": round(count / len(series) * 100, 2) if len(series) else 0,
            }
            report.total_outliers += count

        logger.info(
            "Found %d total outlier(s) across %d numeric column(s)",
            report.total_outliers, len(numeric_cols),
        )
        return report

    def remove_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Drop all rows flagged as outliers in any numeric column."""
        report = self.detect(df)
        all_outlier_indices: set[Any] = set()
        for info in report.column_results.values():
            all_outlier_indices.update(info["outlier_indices"])

        before = len(df)
        df_clean = df.drop(index=list(all_outlier_indices)).reset_index(drop=True)
        logger.info(
            "Removed %d outlier row(s) — %d rows remaining",
            before - len(df_clean), len(df_clean),
        )
        return df_clean
