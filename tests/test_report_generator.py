"""
test_report_generator.py
Tests for report_generator.py.

Tests cover:
  - HTML report file created
  - HTML contains expected section headings
  - Missing bar chart created when missing values present
  - Chart skipped (returns None) when no missing values
  - Distribution charts created for each numeric column
  - Chart files are non-empty PNGs
  - No seaborn FutureWarning raised
  - Drift section rendered when drift_report provided
  - PDF step skipped gracefully when weasyprint not installed
"""

import sys
import warnings
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

# Force Agg backend before any matplotlib import so tests run headless
import matplotlib
matplotlib.use("Agg")

from anomaly_detector import AnomalyDetector
from cleaner import DataCleaner
from report_generator import ReportGenerator, _save_distribution_plots, _save_missing_bar
from validator import DataValidator


# ══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def sample_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Returns (df_raw, df_clean) for report generation tests."""
    rng = np.random.default_rng(7)
    df_raw = pd.DataFrame({
        "age":    rng.integers(20, 70, 60).astype(float),
        "income": rng.normal(50_000, 10_000, 60).round(2),
        "label":  rng.choice(["A", "B"], 60).tolist(),
    })
    df_raw.loc[[0, 1], "age"] = float("nan")

    cleaner = DataCleaner()
    df_clean, _ = cleaner.run(df_raw)
    return df_raw, df_clean


# ══════════════════════════════════════════════════════════════════════════════
# HTML report generation
# ══════════════════════════════════════════════════════════════════════════════

def test_html_report_created(tmp_path: Path, sample_data: tuple) -> None:
    df_raw, df_clean = sample_data
    val_result = DataValidator().run(df_raw)
    anomaly_report = AnomalyDetector().detect(df_clean)
    _, clean_log = DataCleaner().run(df_raw)

    gen = ReportGenerator(output_dir=tmp_path)
    report_path = gen.generate(df_raw, df_clean, val_result, anomaly_report, clean_log)

    assert report_path.exists()
    assert report_path.suffix == ".html"
    assert report_path.stat().st_size > 0


def test_html_contains_required_sections(tmp_path: Path, sample_data: tuple) -> None:
    df_raw, df_clean = sample_data
    val_result = DataValidator().run(df_raw)
    anomaly_report = AnomalyDetector().detect(df_clean)
    _, clean_log = DataCleaner().run(df_raw)

    gen = ReportGenerator(output_dir=tmp_path)
    report_path = gen.generate(df_raw, df_clean, val_result, anomaly_report, clean_log)
    html = report_path.read_text()

    assert "Quality Score" in html
    assert "Dataset Overview" in html
    assert "Column Profiles" in html
    assert "Cleaning Log" in html
    assert "Anomaly Detection" in html
    assert "Distributions" in html


def test_html_reflects_quality_score(tmp_path: Path, sample_data: tuple) -> None:
    df_raw, df_clean = sample_data
    val_result = DataValidator().run(df_raw)
    anomaly_report = AnomalyDetector().detect(df_clean)
    _, clean_log = DataCleaner().run(df_raw)

    gen = ReportGenerator(output_dir=tmp_path)
    report_path = gen.generate(df_raw, df_clean, val_result, anomaly_report, clean_log)
    html = report_path.read_text()

    assert str(val_result.quality_score) in html


# ══════════════════════════════════════════════════════════════════════════════
# Missing-value bar chart
# ══════════════════════════════════════════════════════════════════════════════

def test_missing_bar_chart_created(tmp_path: Path) -> None:
    missing_summary = {"age": {"count": 5, "pct": 10.0}, "income": {"count": 2, "pct": 4.0}}
    path = _save_missing_bar(missing_summary, tmp_path)
    assert path is not None
    png = Path(path)
    assert png.exists()
    assert png.stat().st_size > 0


def test_missing_bar_chart_skipped_when_no_missing(tmp_path: Path) -> None:
    path = _save_missing_bar({}, tmp_path)
    assert path is None


def test_missing_bar_no_seaborn_warning(tmp_path: Path) -> None:
    missing_summary = {"col_a": {"count": 3, "pct": 6.0}, "col_b": {"count": 1, "pct": 2.0}}
    with warnings.catch_warnings():
        warnings.simplefilter("error", FutureWarning)
        _save_missing_bar(missing_summary, tmp_path)  # must not raise


# ══════════════════════════════════════════════════════════════════════════════
# Distribution charts
# ══════════════════════════════════════════════════════════════════════════════

def test_distribution_charts_created_for_numeric_cols(tmp_path: Path) -> None:
    rng = np.random.default_rng(3)
    df = pd.DataFrame({"x": rng.normal(0, 1, 50), "y": rng.normal(5, 2, 50)})
    paths = _save_distribution_plots(df, tmp_path)
    assert len(paths) == 2
    for p in paths:
        assert Path(p).exists()
        assert Path(p).stat().st_size > 0


def test_no_distribution_charts_for_string_only_df(tmp_path: Path) -> None:
    df = pd.DataFrame({"name": ["Alice", "Bob", "Carol"]})
    paths = _save_distribution_plots(df, tmp_path)
    assert paths == []


# ══════════════════════════════════════════════════════════════════════════════
# Drift section
# ══════════════════════════════════════════════════════════════════════════════

def test_drift_section_rendered_when_provided(tmp_path: Path, sample_data: tuple) -> None:
    df_raw, df_clean = sample_data
    val_result = DataValidator().run(df_raw)
    anomaly_report = AnomalyDetector().detect(df_clean)
    _, clean_log = DataCleaner().run(df_raw)

    from drift_detector import DriftDetector

    rng = np.random.default_rng(99)
    df_incoming = pd.DataFrame({
        "age":    (rng.integers(20, 70, 60).astype(float)),
        "income": rng.normal(80_000, 10_000, 60).round(2),  # shifted mean
        "label":  rng.choice(["A", "B"], 60).tolist(),
    })
    drift_report = DriftDetector().compare(df_raw, df_incoming)

    gen = ReportGenerator(output_dir=tmp_path)
    report_path = gen.generate(
        df_raw, df_clean, val_result, anomaly_report, clean_log,
        drift_report=drift_report,
    )
    html = report_path.read_text()
    assert "Drift Detection" in html


def test_drift_section_absent_when_not_provided(tmp_path: Path, sample_data: tuple) -> None:
    df_raw, df_clean = sample_data
    val_result = DataValidator().run(df_raw)
    anomaly_report = AnomalyDetector().detect(df_clean)
    _, clean_log = DataCleaner().run(df_raw)

    gen = ReportGenerator(output_dir=tmp_path)
    report_path = gen.generate(df_raw, df_clean, val_result, anomaly_report, clean_log)
    html = report_path.read_text()
    assert "Drift Detection" not in html


# ══════════════════════════════════════════════════════════════════════════════
# PDF export: graceful skip when weasyprint missing
# ══════════════════════════════════════════════════════════════════════════════

def test_pdf_export_skipped_gracefully(tmp_path: Path, sample_data: tuple) -> None:
    df_raw, df_clean = sample_data
    val_result = DataValidator().run(df_raw)
    anomaly_report = AnomalyDetector().detect(df_clean)
    _, clean_log = DataCleaner().run(df_raw)

    gen = ReportGenerator(output_dir=tmp_path)
    # Patch weasyprint to simulate it not being installed
    with patch.dict(sys.modules, {"weasyprint": None}):
        # generate() should complete without raising
        report_path = gen.generate(df_raw, df_clean, val_result, anomaly_report, clean_log)

    assert report_path.exists()
    pdf_path = tmp_path / "report.pdf"
    assert not pdf_path.exists()  # PDF should not have been created
