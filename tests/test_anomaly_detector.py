"""
test_anomaly_detector.py
Unit tests for anomaly_detector.py.

Tests cover:
  - IQR outlier detection
  - Z-score outlier detection
  - remove_outliers produces smaller DataFrame
  - No outliers detected in clean data
  - Invalid method raises ValueError
  - Zero-std column handled gracefully (zscore)
  - AnomalyReport structure and counts
"""

import numpy as np
import pandas as pd
import pytest

from anomaly_detector import AnomalyDetector, AnomalyReport

# ══════════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════════


def _df_with_known_outlier() -> pd.DataFrame:
    """DataFrame where row 0 is a clear outlier in 'value'."""
    rng = np.random.default_rng(0)
    values = rng.normal(50.0, 3.0, 50).tolist()
    values[0] = 500.0  # extreme outlier — will be flagged by both methods
    return pd.DataFrame({"id": range(50), "value": values})


def _clean_numeric_df() -> pd.DataFrame:
    """Tightly clustered data — no outliers at threshold 1.5."""
    rng = np.random.default_rng(1)
    return pd.DataFrame({"a": rng.normal(0, 1, 100), "b": rng.normal(10, 1, 100)})


# ══════════════════════════════════════════════════════════════════════════════
# IQR detection
# ══════════════════════════════════════════════════════════════════════════════


def test_iqr_detects_known_outlier() -> None:
    df = _df_with_known_outlier()
    report = AnomalyDetector(method="iqr", threshold=1.5).detect(df)
    assert report.column_results["value"]["count"] >= 1
    assert 0 in report.column_results["value"]["outlier_indices"]


def test_iqr_report_structure() -> None:
    df = _df_with_known_outlier()
    report = AnomalyDetector(method="iqr").detect(df)
    assert isinstance(report, AnomalyReport)
    assert report.method == "iqr"
    assert "value" in report.column_results
    assert "count" in report.column_results["value"]
    assert "pct" in report.column_results["value"]
    assert "outlier_indices" in report.column_results["value"]


def test_iqr_total_outliers_matches_column_sum() -> None:
    df = _df_with_known_outlier()
    report = AnomalyDetector(method="iqr").detect(df)
    total = sum(v["count"] for v in report.column_results.values())
    assert report.total_outliers == total


# ══════════════════════════════════════════════════════════════════════════════
# Z-score detection
# ══════════════════════════════════════════════════════════════════════════════


def test_zscore_detects_known_outlier() -> None:
    df = _df_with_known_outlier()
    report = AnomalyDetector(method="zscore", threshold=3.0).detect(df)
    assert 0 in report.column_results["value"]["outlier_indices"]


def test_zscore_zero_std_handled_gracefully() -> None:
    # Column of constant values — std = 0; no outliers should be flagged
    df = pd.DataFrame({"constant": [5.0] * 50})
    report = AnomalyDetector(method="zscore").detect(df)
    assert report.column_results["constant"]["count"] == 0


# ══════════════════════════════════════════════════════════════════════════════
# No outliers in clean data
# ══════════════════════════════════════════════════════════════════════════════


def test_no_outliers_in_clean_data_iqr() -> None:
    # Use a high threshold to ensure tightly clustered data passes
    df = _clean_numeric_df()
    report = AnomalyDetector(method="iqr", threshold=3.0).detect(df)
    assert report.total_outliers == 0


# ══════════════════════════════════════════════════════════════════════════════
# remove_outliers
# ══════════════════════════════════════════════════════════════════════════════


def test_remove_outliers_reduces_row_count() -> None:
    df = _df_with_known_outlier()
    clean = AnomalyDetector(method="iqr").remove_outliers(df)
    assert len(clean) < len(df)


def test_remove_outliers_returns_dataframe() -> None:
    df = _df_with_known_outlier()
    clean = AnomalyDetector(method="iqr").remove_outliers(df)
    assert isinstance(clean, pd.DataFrame)


def test_remove_outliers_reset_index() -> None:
    df = _df_with_known_outlier()
    clean = AnomalyDetector(method="iqr").remove_outliers(df)
    # Index should start at 0 and be contiguous after reset
    assert list(clean.index) == list(range(len(clean)))


def test_remove_outliers_no_change_for_clean_data() -> None:
    df = _clean_numeric_df()
    # threshold=4 is very permissive — nothing should be removed
    clean = AnomalyDetector(method="iqr", threshold=4.0).remove_outliers(df)
    assert len(clean) == len(df)


# ══════════════════════════════════════════════════════════════════════════════
# Error handling
# ══════════════════════════════════════════════════════════════════════════════


def test_invalid_method_raises_value_error() -> None:
    with pytest.raises(ValueError, match="method must be one of"):
        AnomalyDetector(method="invalid")


def test_non_numeric_columns_skipped() -> None:
    df = pd.DataFrame(
        {
            "text": ["a", "b", "c", "d"],
            "value": [1.0, 2.0, 3.0, 1_000.0],  # 1000 is an outlier
        }
    )
    report = AnomalyDetector(method="iqr").detect(df)
    # Only 'value' should be in results; 'text' is skipped
    assert "text" not in report.column_results
    assert "value" in report.column_results
