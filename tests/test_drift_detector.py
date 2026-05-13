"""
test_drift_detector.py
Tests for drift_detector.py — column-level and report-level drift detection.

Covers:
  - Normal compare() returning DriftReport
  - Early return when a series has < 2 non-null values (line 143)
  - No-scipy fallback: no drift on similar distributions (lines 170-176)
  - No-scipy fallback: mean-shift triggers drifted=True (line 171)
  - No-scipy fallback: std-ratio triggers drifted=True (line 176)
  - Non-numeric / non-shared column handling
  - overall_drift_score calculation
"""

from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from drift_detector import DriftDetector, DriftReport

# ══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def base_df() -> pd.DataFrame:
    rng = np.random.default_rng(0)
    return pd.DataFrame({"x": rng.normal(0, 1, 50), "y": rng.normal(10, 2, 50)})


@pytest.fixture
def similar_df() -> pd.DataFrame:
    rng = np.random.default_rng(1)
    return pd.DataFrame({"x": rng.normal(0, 1, 50), "y": rng.normal(10, 2, 50)})


# ══════════════════════════════════════════════════════════════════════════════
# Basic compare()
# ══════════════════════════════════════════════════════════════════════════════


def test_compare_returns_drift_report(base_df: pd.DataFrame, similar_df: pd.DataFrame) -> None:
    report = DriftDetector().compare(base_df, similar_df)
    assert isinstance(report, DriftReport)
    assert report.baseline_rows == 50
    assert report.incoming_rows == 50
    assert set(report.column_results.keys()) == {"x", "y"}


def test_no_numeric_cols_returns_empty_report() -> None:
    df = pd.DataFrame({"label": ["a", "b"], "name": ["x", "y"]})
    report = DriftDetector().compare(df, df.copy())
    assert report.column_results == {}
    assert report.overall_drift_score == 0.0


def test_non_shared_cols_skipped() -> None:
    base = pd.DataFrame({"x": [1.0, 2.0, 3.0]})
    incoming = pd.DataFrame({"y": [1.0, 2.0, 3.0]})
    report = DriftDetector().compare(base, incoming)
    assert report.column_results == {}


# ══════════════════════════════════════════════════════════════════════════════
# Early return: < 2 non-null values (line 143)
# ══════════════════════════════════════════════════════════════════════════════


def test_early_return_on_short_series() -> None:
    # incoming has only 1 non-null value → _compare_column returns ColumnDriftResult()
    base = pd.DataFrame({"x": [1.0, 2.0, 3.0, 4.0, 5.0]})
    incoming = pd.DataFrame({"x": [np.nan, np.nan, np.nan, np.nan, 1.0]})
    report = DriftDetector().compare(base, incoming)
    result = report.column_results["x"]
    assert result.mean_shift is None
    assert result.std_ratio is None
    assert result.ks_statistic is None
    assert result.drifted is False


def test_early_return_when_baseline_short() -> None:
    # baseline has only 1 non-null value → also triggers early return
    base = pd.DataFrame({"x": [np.nan, 1.0]})
    incoming = pd.DataFrame({"x": [1.0, 2.0, 3.0]})
    report = DriftDetector().compare(base, incoming)
    result = report.column_results["x"]
    assert result.mean_shift is None
    assert result.drifted is False


# ══════════════════════════════════════════════════════════════════════════════
# No-scipy fallback (lines 170-176)
# ══════════════════════════════════════════════════════════════════════════════


def test_fallback_no_drift_similar_distributions(
    base_df: pd.DataFrame, similar_df: pd.DataFrame
) -> None:
    """Fallback path: nearly-identical distributions → no drift flagged."""
    with patch("drift_detector._HAS_SCIPY", False):
        report = DriftDetector(mean_shift_threshold=0.5, std_ratio_threshold=2.0).compare(
            base_df, similar_df
        )
    assert report.overall_drift_score == 0.0


def test_fallback_mean_shift_triggers_drift() -> None:
    """Fallback path: mean shifts by >>0.5σ → drifted=True."""
    rng = np.random.default_rng(10)
    base = pd.DataFrame({"x": rng.normal(0, 1, 50)})
    incoming = pd.DataFrame({"x": rng.normal(10, 1, 50)})  # 10σ shift
    with patch("drift_detector._HAS_SCIPY", False):
        report = DriftDetector(mean_shift_threshold=0.5).compare(base, incoming)
    assert report.column_results["x"].drifted is True


def test_fallback_std_ratio_triggers_drift() -> None:
    """Fallback path: std ratio >> threshold → drifted=True."""
    rng = np.random.default_rng(20)
    base = pd.DataFrame({"x": rng.normal(0, 1, 50)})
    incoming = pd.DataFrame({"x": rng.normal(0, 10, 50)})  # 10× std increase
    with patch("drift_detector._HAS_SCIPY", False):
        report = DriftDetector(std_ratio_threshold=2.0).compare(base, incoming)
    assert report.column_results["x"].drifted is True


# ══════════════════════════════════════════════════════════════════════════════
# overall_drift_score
# ══════════════════════════════════════════════════════════════════════════════


def test_overall_drift_score_all_drifted(base_df: pd.DataFrame) -> None:
    rng = np.random.default_rng(30)
    # Extreme shift guarantees KS p < 0.05 for both columns
    shifted = pd.DataFrame({"x": rng.normal(1000, 1, 50), "y": rng.normal(1000, 1, 50)})
    report = DriftDetector(ks_alpha=0.05).compare(base_df, shifted)
    assert report.overall_drift_score == 100.0
    assert len(report.drifted_columns) == 2
