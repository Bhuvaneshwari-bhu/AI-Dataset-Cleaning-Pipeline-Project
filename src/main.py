"""
main.py
Entry point for the AI Dataset Cleaning & Validation Pipeline.

Pipeline stages (in order):
  1. Load     – read raw CSV from data/
  2. Validate – check structure, missing values, types, ranges
  3. Clean    – impute missing values, drop duplicates, normalise column names
  4. Detect   – flag / remove statistical outliers
  5. Export   – save clean CSV to output/
  6. Report   – write HTML (and optionally PDF) report to reports/

Usage
-----
    # No-arg form — uses built-in defaults and auto-generates sample data if needed:
    python3 main.py

    # Explicit input + schema:
    python3 main.py --input data.csv --schema config/schema.yaml

    # Override output locations and detection method:
    python3 main.py --input raw.csv --output-dir results/ --report-dir html/ --anomaly-method zscore
"""

import argparse
import os
import sys
from pathlib import Path

import pandas as pd

# Allow imports from the same src/ directory
sys.path.insert(0, os.path.dirname(__file__))

from anomaly_detector import AnomalyDetector
from cleaner import DataCleaner
from loader import get_basic_info, load_csv
from logger import get_logger
from report_generator import ReportGenerator
from validator import DataValidator, load_schema_from_yaml

logger = get_logger("main")

# ── Defaults ──────────────────────────────────────────────────────────────────
# Centralised here so _build_parser() and run_pipeline() always agree on them.

DEFAULT_INPUT = "data/sample_dataset.csv"
DEFAULT_SCHEMA = "config/schema.yaml"
DEFAULT_OUTPUT_DIR = "output"
DEFAULT_REPORT_DIR = "reports"
DEFAULT_ANOMALY_METHOD = "iqr"
DEFAULT_ANOMALY_THRESHOLD = 1.5

CLEANER_CONFIG = {
    "fill_strategy": "median",  # "median" | "mean" | "mode" | "drop"
    "drop_duplicate": True,
    "strip_whitespace": True,
}


# ── Argument parser ───────────────────────────────────────────────────────────


def _build_parser() -> argparse.ArgumentParser:
    """Return a configured ArgumentParser.  Isolated so it can be unit-tested."""
    parser = argparse.ArgumentParser(
        prog="main.py",
        description=(
            "AI Dataset Cleaning & Validation Pipeline — loads a CSV, validates it "
            "against an optional schema, cleans it, detects anomalies, and produces "
            "an HTML quality report."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--input",
        "-i",
        metavar="FILE",
        default=DEFAULT_INPUT,
        help=(
            "Path to the input CSV file. "
            "A synthetic sample is auto-generated when the file does not exist."
        ),
    )
    parser.add_argument(
        "--schema",
        "-s",
        metavar="FILE",
        default=DEFAULT_SCHEMA,
        help=(
            "Path to a YAML schema file that defines per-column validation rules "
            "(dtype, nullable, min/max, allowed_values, regex). "
            "Silently skipped when the file does not exist."
        ),
    )
    parser.add_argument(
        "--output-dir",
        metavar="DIR",
        default=DEFAULT_OUTPUT_DIR,
        help=(
            "Directory for the cleaned CSV (clean_dataset.csv) "
            "and invalid-rows file (invalid_rows.csv)."
        ),
    )
    parser.add_argument(
        "--report-dir",
        metavar="DIR",
        default=DEFAULT_REPORT_DIR,
        help="Directory for the HTML quality report (report.html) and optional PDF.",
    )
    parser.add_argument(
        "--anomaly-method",
        choices=["iqr", "zscore"],
        default=DEFAULT_ANOMALY_METHOD,
        help=(
            "Outlier detection algorithm. "
            "'iqr' (inter-quartile range) is robust for skewed distributions; "
            "'zscore' works better when the data is near-normal."
        ),
    )

    return parser


# ── Pipeline ──────────────────────────────────────────────────────────────────


def run_pipeline(
    data_file: str = DEFAULT_INPUT,
    *,
    schema_file: str | None = DEFAULT_SCHEMA,
    output_dir: str = DEFAULT_OUTPUT_DIR,
    report_dir: str = DEFAULT_REPORT_DIR,
    anomaly_method: str = DEFAULT_ANOMALY_METHOD,
    anomaly_threshold: float = DEFAULT_ANOMALY_THRESHOLD,
) -> pd.DataFrame:
    """
    Execute the full pipeline and return the cleaned DataFrame.

    All parameters are keyword-only (except *data_file*) so callers can override
    only the options they care about while defaults handle the rest.

    Parameters
    ----------
    data_file        : path to the raw input CSV
    schema_file      : YAML schema path; None or a non-existent path skips schema validation
    output_dir       : directory for clean_dataset.csv and invalid_rows.csv
    report_dir       : directory for report.html (and optional report.pdf)
    anomaly_method   : "iqr" or "zscore"
    anomaly_threshold: IQR multiplier (iqr mode) or std-dev cutoff (zscore mode)
    """
    out_path = Path(output_dir)
    output_file = out_path / "clean_dataset.csv"
    invalid_rows_file = out_path / "invalid_rows.csv"

    logger.info("=" * 60)
    logger.info("AI Dataset Cleaning & Validation Pipeline")
    logger.info("=" * 60)

    # ── Stage 1: Load ──────────────────────────────────────────────────
    df_raw = load_csv(data_file)

    info = get_basic_info(df_raw)
    logger.info("Columns: %s", info["column_names"])
    logger.info("Memory: %.1f KB", info["memory_usage_kb"])
    logger.info("First 5 rows:\n%s", df_raw.head().to_string())

    # ── Stage 2: Validate ──────────────────────────────────────────────
    schema: dict | None = None
    if schema_file and os.path.exists(schema_file):
        try:
            schema = load_schema_from_yaml(schema_file)
        except Exception as exc:
            logger.warning(
                "Could not load schema from '%s': %s — running without schema.",
                schema_file,
                exc,
            )

    validator = DataValidator(schema=schema)
    validation_result = validator.run(df_raw, export_invalid_to=str(invalid_rows_file))

    # ── Stage 3: Clean ─────────────────────────────────────────────────
    cleaner = DataCleaner(**CLEANER_CONFIG)
    df_clean, clean_log = cleaner.run(df_raw)

    # ── Stage 4: Anomaly Detection ─────────────────────────────────────
    detector = AnomalyDetector(method=anomaly_method, threshold=anomaly_threshold)
    anomaly_report = detector.detect(df_clean)

    # ── Stage 5: Export ────────────────────────────────────────────────
    out_path.mkdir(parents=True, exist_ok=True)
    df_clean.to_csv(output_file, index=False)
    logger.info("Clean dataset saved to '%s'", output_file)

    # ── Stage 6: Report ────────────────────────────────────────────────
    reporter = ReportGenerator(output_dir=report_dir)
    reporter.generate(
        df_raw=df_raw,
        df_clean=df_clean,
        validation_result=validation_result,
        anomaly_report=anomaly_report,
        clean_log=clean_log,
    )

    logger.info("Pipeline complete.")
    return df_clean


# ── Sample dataset generator ──────────────────────────────────────────────────


def _create_sample_csv(path: str) -> None:
    """Generate a small synthetic dataset so the pipeline runs out of the box."""
    import numpy as np

    rng = np.random.default_rng(42)
    n = 200

    df = pd.DataFrame(
        {
            "id": range(1, n + 1),
            "age": rng.integers(18, 75, size=n).astype(float),
            "income": rng.normal(50_000, 15_000, size=n).round(2),
            "score": rng.uniform(0, 100, size=n).round(1),
            "category": rng.choice(np.array(["A", "B", "C", None], dtype=object), size=n),
            "region": rng.choice(["North", "South", "East", "West"], size=n),
        }
    )

    for col in ["age", "income", "score"]:
        idx = rng.choice(df.index, size=16, replace=False)
        df.loc[idx, col] = float("nan")

    df.loc[0, "income"] = 999_999.0
    df.loc[1, "age"] = 130.0
    df = pd.concat([df, df.iloc[:5]], ignore_index=True)

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    df.to_csv(path, index=False)
    logger.info("Sample dataset created at '%s' (%d rows)", path, len(df))


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    args = _build_parser().parse_args()

    if not os.path.exists(args.input):
        logger.info("'%s' not found — generating sample dataset...", args.input)
        _create_sample_csv(args.input)

    run_pipeline(
        data_file=args.input,
        schema_file=args.schema,
        output_dir=args.output_dir,
        report_dir=args.report_dir,
        anomaly_method=args.anomaly_method,
    )
