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
from unittest.mock import patch

# Force Agg backend before any matplotlib import so tests run headless
import matplotlib
import numpy as np
import pandas as pd
import pytest

matplotlib.use("Agg")

from anomaly_detector import AnomalyDetector, AnomalyReport
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
    df_raw = pd.DataFrame(
        {
            "age": rng.integers(20, 70, 60).astype(float),
            "income": rng.normal(50_000, 10_000, 60).round(2),
            "label": rng.choice(["A", "B"], 60).tolist(),
        }
    )
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
    df_incoming = pd.DataFrame(
        {
            "age": (rng.integers(20, 70, 60).astype(float)),
            "income": rng.normal(80_000, 10_000, 60).round(2),  # shifted mean
            "label": rng.choice(["A", "B"], 60).tolist(),
        }
    )
    drift_report = DriftDetector().compare(df_raw, df_incoming)

    gen = ReportGenerator(output_dir=tmp_path)
    report_path = gen.generate(
        df_raw,
        df_clean,
        val_result,
        anomaly_report,
        clean_log,
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


def test_pdf_export_exception_handled(tmp_path: Path, sample_data: tuple) -> None:
    """Lines 184-185: weasyprint importable but write_pdf() raises → warning, no crash."""
    from unittest.mock import MagicMock

    df_raw, df_clean = sample_data
    val_result = DataValidator().run(df_raw)
    anomaly_report = AnomalyDetector().detect(df_clean)
    _, clean_log = DataCleaner().run(df_raw)

    mock_wp = MagicMock()
    mock_wp.HTML.return_value.write_pdf.side_effect = RuntimeError("fake pdf failure")

    gen = ReportGenerator(output_dir=tmp_path)
    with patch.dict(sys.modules, {"weasyprint": mock_wp}):
        report_path = gen.generate(df_raw, df_clean, val_result, anomaly_report, clean_log)

    assert report_path.exists()


# ══════════════════════════════════════════════════════════════════════════════
# score_colour branches (lines 217-219)
# ══════════════════════════════════════════════════════════════════════════════


def _make_anomaly_report() -> AnomalyReport:
    return AnomalyReport(method="iqr", column_results={}, total_outliers=0)


def test_score_colour_medium_range(tmp_path: Path) -> None:
    """score 60-79 → orange (#e65100) appears in HTML."""
    from validator import ValidationResult

    rng = np.random.default_rng(5)
    df = pd.DataFrame({"x": rng.normal(0, 1, 10)})
    val_result = ValidationResult(quality_score=70.0)
    anomaly_report = _make_anomaly_report()

    gen = ReportGenerator(output_dir=tmp_path)
    report_path = gen.generate(df, df.copy(), val_result, anomaly_report, [])
    html = report_path.read_text()

    assert "#e65100" in html


def test_score_colour_low_range(tmp_path: Path) -> None:
    """score < 60 → red (#c62828) appears as the score card border colour."""
    from validator import ValidationResult

    rng = np.random.default_rng(5)
    df = pd.DataFrame({"x": rng.normal(0, 1, 10)})
    val_result = ValidationResult(quality_score=45.0)
    anomaly_report = _make_anomaly_report()

    gen = ReportGenerator(output_dir=tmp_path)
    report_path = gen.generate(df, df.copy(), val_result, anomaly_report, [])
    html = report_path.read_text()

    assert "#c62828" in html


# ══════════════════════════════════════════════════════════════════════════════
# type_section (lines 271-272), schema/format/range violation sections
# ══════════════════════════════════════════════════════════════════════════════


def test_type_issues_section_rendered(tmp_path: Path) -> None:
    """Lines 271-272: type_issues present → <h3>Type Issues</h3> in HTML."""
    from validator import ValidationResult

    rng = np.random.default_rng(5)
    df = pd.DataFrame({"x": rng.normal(0, 1, 10)})
    val_result = ValidationResult(type_issues=["'age' expected float64, got object"])
    anomaly_report = _make_anomaly_report()

    gen = ReportGenerator(output_dir=tmp_path)
    report_path = gen.generate(df, df.copy(), val_result, anomaly_report, [])
    html = report_path.read_text()

    assert "Type Issues" in html
    assert "age" in html


def test_schema_violations_section_rendered(tmp_path: Path) -> None:
    """Lines 300-304: schema_violations present → violation table in HTML."""
    from validator import ValidationResult

    rng = np.random.default_rng(5)
    df = pd.DataFrame({"x": rng.normal(0, 1, 10)})
    val_result = ValidationResult(
        schema_violations={"age": ["2 value(s) exceed max 120"]},
        passed=False,
    )
    anomaly_report = _make_anomaly_report()

    gen = ReportGenerator(output_dir=tmp_path)
    report_path = gen.generate(df, df.copy(), val_result, anomaly_report, [])
    html = report_path.read_text()

    assert "Schema Violations" in html
    assert "exceed max 120" in html


def test_format_violations_section_rendered(tmp_path: Path) -> None:
    """Lines 318-325: format_violations present → format table in HTML."""
    from validator import ValidationResult

    rng = np.random.default_rng(5)
    df = pd.DataFrame({"x": rng.normal(0, 1, 10)})
    val_result = ValidationResult(
        format_violations={
            "email": {
                "pattern": "email",
                "invalid_count": 2,
                "invalid_indices": [4, 5],
                "sample_values": ["not-an-email", "alsowrong"],
            }
        },
        passed=False,
    )
    anomaly_report = _make_anomaly_report()

    gen = ReportGenerator(output_dir=tmp_path)
    report_path = gen.generate(df, df.copy(), val_result, anomaly_report, [])
    html = report_path.read_text()

    assert "Format Violations" in html
    assert "not-an-email" in html


def test_range_violations_section_rendered(tmp_path: Path) -> None:
    """Lines 339-346: out_of_range present → range table in HTML."""
    from validator import ValidationResult

    rng = np.random.default_rng(5)
    df = pd.DataFrame({"x": rng.normal(0, 1, 10)})
    val_result = ValidationResult(
        out_of_range={
            "age": {
                "violations": 1,
                "min_found": 5.0,
                "max_found": 200.0,
                "expected_range": (0, 120),
            }
        },
        passed=False,
    )
    anomaly_report = _make_anomaly_report()

    gen = ReportGenerator(output_dir=tmp_path)
    report_path = gen.generate(df, df.copy(), val_result, anomaly_report, [])
    html = report_path.read_text()

    assert "Range Violations" in html
    assert "200" in html
