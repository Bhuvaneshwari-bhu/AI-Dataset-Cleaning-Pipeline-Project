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
"""

import os
import sys

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

# ── Configuration ────────────────────────────────────────────────────────────
# Adjust these paths to match your dataset.

DATA_FILE = "data/sample_dataset.csv"
OUTPUT_FILE = "output/clean_dataset.csv"
REPORTS_DIR = "reports"
INVALID_ROWS_FILE = "output/invalid_rows.csv"

# Optional: load schema rules from YAML instead of hard-coding them here.
# Set to None to skip schema validation, or provide a path like "config/schema.yaml".
SCHEMA_FILE: str | None = "config/schema.yaml"

CLEANER_CONFIG = {
    "fill_strategy": "median",   # "median" | "mean" | "mode" | "drop"
    "drop_duplicate": True,
    "strip_whitespace": True,
}

ANOMALY_CONFIG = {
    "method": "iqr",      # "iqr" | "zscore"
    "threshold": 1.5,
}


# ── Pipeline ─────────────────────────────────────────────────────────────────

def run_pipeline(data_file: str = DATA_FILE) -> pd.DataFrame:
    """
    Execute the full pipeline and return the cleaned DataFrame.

    Parameters
    ----------
    data_file : path to the raw CSV (default DATA_FILE)
    """
    logger.info("=" * 60)
    logger.info("AI Dataset Cleaning & Validation Pipeline")
    logger.info("=" * 60)

    # ── Stage 1: Load ────────────────────────────────────────────────
    df_raw = load_csv(data_file)

    info = get_basic_info(df_raw)
    logger.info("Columns: %s", info["column_names"])
    logger.info("Memory: %.1f KB", info["memory_usage_kb"])

    logger.info("First 5 rows:\n%s", df_raw.head().to_string())

    # ── Stage 2: Validate ────────────────────────────────────────────
    schema: dict | None = None
    if SCHEMA_FILE and os.path.exists(SCHEMA_FILE):
        try:
            schema = load_schema_from_yaml(SCHEMA_FILE)
        except Exception as exc:
            logger.warning("Could not load schema from '%s': %s — running without schema.", SCHEMA_FILE, exc)

    validator = DataValidator(schema=schema)
    validation_result = validator.run(df_raw, export_invalid_to=INVALID_ROWS_FILE)

    # ── Stage 3: Clean ───────────────────────────────────────────────
    cleaner = DataCleaner(**CLEANER_CONFIG)
    df_clean, clean_log = cleaner.run(df_raw)

    # ── Stage 4: Anomaly Detection ───────────────────────────────────
    detector = AnomalyDetector(**ANOMALY_CONFIG)
    anomaly_report = detector.detect(df_clean)

    # ── Stage 5: Export ──────────────────────────────────────────────
    os.makedirs(os.path.dirname(OUTPUT_FILE) or ".", exist_ok=True)
    df_clean.to_csv(OUTPUT_FILE, index=False)
    logger.info("Clean dataset saved to '%s'", OUTPUT_FILE)

    # ── Stage 6: Report ──────────────────────────────────────────────
    reporter = ReportGenerator(output_dir=REPORTS_DIR)
    reporter.generate(
        df_raw=df_raw,
        df_clean=df_clean,
        validation_result=validation_result,
        anomaly_report=anomaly_report,
        clean_log=clean_log,
    )

    logger.info("Pipeline complete.")
    return df_clean


# ── Sample dataset generator ─────────────────────────────────────────────────

def _create_sample_csv(path: str) -> None:
    """Generate a small synthetic dataset so the pipeline runs out of the box."""
    import numpy as np

    rng = np.random.default_rng(42)
    n = 200

    df = pd.DataFrame({
        "id":       range(1, n + 1),
        "age":      rng.integers(18, 75, size=n).astype(float),
        "income":   rng.normal(50_000, 15_000, size=n).round(2),
        "score":    rng.uniform(0, 100, size=n).round(1),
        "category": rng.choice(np.array(["A", "B", "C", None], dtype=object), size=n),
        "region":   rng.choice(["North", "South", "East", "West"], size=n),
    })

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
    if not os.path.exists(DATA_FILE):
        logger.info("'%s' not found — generating sample dataset...", DATA_FILE)
        _create_sample_csv(DATA_FILE)

    run_pipeline(DATA_FILE)
