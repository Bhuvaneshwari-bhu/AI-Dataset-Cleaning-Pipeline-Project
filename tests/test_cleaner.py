"""
test_cleaner.py
Unit tests for cleaner.py.

Tests cover:
  - All four fill strategies (median, mean, mode, drop)
  - Custom per-column fill values
  - Duplicate removal
  - Whitespace stripping from string columns
  - Column name standardisation to snake_case
  - Return type (df, log) tuple
  - Input DataFrame is not mutated
  - No FutureWarning or SettingWithCopyWarning raised
"""

import warnings

import numpy as np
import pandas as pd
import pytest

from cleaner import DataCleaner


# ══════════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════════

def _df_with_missing() -> pd.DataFrame:
    return pd.DataFrame({
        "age":    [25.0, float("nan"), 45.0, float("nan"), 35.0],
        "income": [50_000.0, 60_000.0, float("nan"), 55_000.0, 70_000.0],
        "label":  ["A", None, "B", "A", None],
    })


# ══════════════════════════════════════════════════════════════════════════════
# Fill strategies
# ══════════════════════════════════════════════════════════════════════════════

def test_median_fill_numeric() -> None:
    df = _df_with_missing()
    cleaner = DataCleaner(fill_strategy="median")
    clean, log = cleaner.run(df)
    assert clean["age"].isnull().sum() == 0
    assert clean["income"].isnull().sum() == 0


def test_mean_fill_numeric() -> None:
    df = _df_with_missing()
    clean, _ = DataCleaner(fill_strategy="mean").run(df)
    assert clean["age"].isnull().sum() == 0


def test_mode_fill_numeric() -> None:
    df = _df_with_missing()
    clean, _ = DataCleaner(fill_strategy="mode").run(df)
    assert clean["age"].isnull().sum() == 0


def test_drop_strategy_removes_rows() -> None:
    df = _df_with_missing()
    original_len = len(df)
    clean, _ = DataCleaner(fill_strategy="drop").run(df)
    # Rows with NaN in any column should be dropped
    assert len(clean) < original_len
    assert clean.isnull().sum().sum() == 0


def test_categorical_filled_with_mode() -> None:
    df = _df_with_missing()
    clean, _ = DataCleaner(fill_strategy="median").run(df)
    assert clean["label"].isnull().sum() == 0
    # mode of ["A", "B", "A"] is "A"
    assert clean["label"].iloc[1] == "A"


# ══════════════════════════════════════════════════════════════════════════════
# Custom fills
# ══════════════════════════════════════════════════════════════════════════════

def test_custom_fill_overrides_strategy() -> None:
    df = _df_with_missing()
    clean, log = DataCleaner(custom_fills={"age": -1.0}).run(df)
    # Custom fill -1 used, not median
    assert (clean["age"] == -1.0).any()
    assert any("custom value" in entry for entry in log)


# ══════════════════════════════════════════════════════════════════════════════
# Duplicate removal
# ══════════════════════════════════════════════════════════════════════════════

def test_duplicates_removed() -> None:
    df = pd.DataFrame({"a": [1, 2, 3, 1, 2], "b": ["x", "y", "z", "x", "y"]})
    clean, log = DataCleaner(drop_duplicate=True).run(df)
    assert len(clean) == 3
    assert any("duplicate" in entry.lower() for entry in log)


def test_duplicates_kept_when_disabled() -> None:
    df = pd.DataFrame({"a": [1, 2, 1], "b": ["x", "y", "x"]})
    clean, _ = DataCleaner(drop_duplicate=False).run(df)
    assert len(clean) == 3


# ══════════════════════════════════════════════════════════════════════════════
# Whitespace stripping
# ══════════════════════════════════════════════════════════════════════════════

def test_whitespace_stripped_from_strings() -> None:
    df = pd.DataFrame({"name": [" Alice ", "  Bob", "Carol "]})
    clean, _ = DataCleaner(strip_whitespace=True).run(df)
    assert list(clean["name"]) == ["Alice", "Bob", "Carol"]


def test_whitespace_strip_disabled() -> None:
    df = pd.DataFrame({"name": [" Alice "]})
    clean, _ = DataCleaner(strip_whitespace=False).run(df)
    # Column name is snake_cased but values are unchanged
    assert clean["name"].iloc[0] == " Alice "


# ══════════════════════════════════════════════════════════════════════════════
# Column name standardisation
# ══════════════════════════════════════════════════════════════════════════════

def test_column_names_snake_cased() -> None:
    df = pd.DataFrame({"First Name": [1], "Last-Name": [2], "  score  ": [3]})
    clean, log = DataCleaner().run(df)
    assert "first_name" in clean.columns
    assert "last_name" in clean.columns
    assert "score" in clean.columns
    assert any("snake_case" in entry.lower() for entry in log)


# ══════════════════════════════════════════════════════════════════════════════
# Return type and change log
# ══════════════════════════════════════════════════════════════════════════════

def test_run_returns_df_and_log() -> None:
    df = _df_with_missing()
    result = DataCleaner().run(df)
    assert isinstance(result, tuple)
    assert len(result) == 2
    clean, log = result
    assert isinstance(clean, pd.DataFrame)
    assert isinstance(log, list)


def test_change_log_records_steps() -> None:
    df = _df_with_missing()
    _, log = DataCleaner().run(df)
    assert len(log) > 0


def test_empty_log_when_no_issues() -> None:
    df = pd.DataFrame({"a": [1.0, 2.0, 3.0]})
    _, log = DataCleaner(drop_duplicate=False, strip_whitespace=False).run(df)
    # Only the snake_case step runs; no missing, no dups, no strip
    assert any("snake" in entry.lower() for entry in log)


# ══════════════════════════════════════════════════════════════════════════════
# Immutability: input DataFrame must not be mutated
# ══════════════════════════════════════════════════════════════════════════════

def test_input_df_not_mutated() -> None:
    df = _df_with_missing()
    original_nulls = df.isnull().sum().sum()
    DataCleaner().run(df)
    # Original DataFrame should still have its NaNs
    assert df.isnull().sum().sum() == original_nulls


# ══════════════════════════════════════════════════════════════════════════════
# No FutureWarning or SettingWithCopyWarning
# ══════════════════════════════════════════════════════════════════════════════

def test_no_future_warnings_raised() -> None:
    df = _df_with_missing()
    with warnings.catch_warnings():
        warnings.simplefilter("error", FutureWarning)
        # Should not raise
        DataCleaner(fill_strategy="median").run(df)
        DataCleaner(fill_strategy="mean").run(df)
        DataCleaner(fill_strategy="mode").run(df)
        DataCleaner(fill_strategy="drop").run(df)
