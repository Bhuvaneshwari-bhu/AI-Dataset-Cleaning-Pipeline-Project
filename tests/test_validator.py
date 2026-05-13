"""
test_validator.py
Unit and integration tests for validator.py.

Tests cover:
  - Missing value detection
  - Duplicate detection
  - Column profiling
  - Schema dtype, nullable, range, allowed-values validation
  - Regex validation (email, phone, custom pattern)
  - Quality score computation
  - Invalid-row export
  - YAML schema loading
  - Backward-compatible legacy kwargs
"""

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from validator import (
    ColumnProfile,
    DataValidator,
    ValidationResult,
    load_schema_from_yaml,
)


# ══════════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════════

def _simple_df() -> pd.DataFrame:
    """Minimal clean DataFrame for focused single-concern tests."""
    return pd.DataFrame({
        "id":   [1, 2, 3, 4, 5],
        "age":  [25.0, 30.0, 45.0, 60.0, 35.0],
        "name": ["Alice", "Bob", "Carol", "Dave", "Eve"],
    })


# ══════════════════════════════════════════════════════════════════════════════
# Missing value detection
# ══════════════════════════════════════════════════════════════════════════════

def test_missing_detected_correctly() -> None:
    df = _simple_df()
    df.loc[[0, 2], "age"] = float("nan")
    result = DataValidator().run(df)
    assert "age" in result.missing_summary
    assert result.missing_summary["age"]["count"] == 2
    assert result.missing_summary["age"]["pct"] == 40.0


def test_no_missing_clean_data(clean_df: pd.DataFrame) -> None:
    # Remove the email/status columns that conftest may have added
    df = clean_df[["id", "age", "income"]].copy()
    result = DataValidator().run(df)
    assert result.missing_summary == {}


# ══════════════════════════════════════════════════════════════════════════════
# Duplicate detection
# ══════════════════════════════════════════════════════════════════════════════

def test_duplicates_detected() -> None:
    df = _simple_df()
    df = pd.concat([df, df.iloc[:2]], ignore_index=True)
    result = DataValidator().run(df)
    assert result.duplicate_count == 2


def test_no_duplicates_clean_data(clean_df: pd.DataFrame) -> None:
    result = DataValidator().run(clean_df)
    assert result.duplicate_count == 0


# ══════════════════════════════════════════════════════════════════════════════
# Column profiling
# ══════════════════════════════════════════════════════════════════════════════

def test_profile_computed_for_all_columns(clean_df: pd.DataFrame) -> None:
    result = DataValidator().run(clean_df)
    assert set(result.profiles.keys()) == set(clean_df.columns)


def test_numeric_profile_has_stats(clean_df: pd.DataFrame) -> None:
    result = DataValidator().run(clean_df)
    age_profile = result.profiles["age"]
    assert isinstance(age_profile, ColumnProfile)
    assert age_profile.mean is not None
    assert age_profile.median is not None
    assert age_profile.std is not None
    assert age_profile.min_val is not None
    assert age_profile.max_val is not None


def test_string_profile_has_no_numeric_stats(clean_df: pd.DataFrame) -> None:
    result = DataValidator().run(clean_df)
    email_profile = result.profiles["email"]
    assert email_profile.mean is None
    assert email_profile.std is None


def test_profile_null_count_correct() -> None:
    df = _simple_df()
    df.loc[[0, 1], "age"] = float("nan")
    result = DataValidator().run(df)
    assert result.profiles["age"].null_count == 2
    assert result.profiles["age"].null_pct == 40.0


# ══════════════════════════════════════════════════════════════════════════════
# Schema: dtype check
# ══════════════════════════════════════════════════════════════════════════════

def test_dtype_mismatch_detected() -> None:
    df = _simple_df()
    # age is float64 but we declare it as int64
    result = DataValidator(schema={"age": {"dtype": "int64"}}).run(df)
    assert len(result.type_issues) == 1
    assert "age" in result.type_issues[0]
    assert not result.passed


def test_correct_dtype_passes() -> None:
    df = _simple_df()
    result = DataValidator(schema={"age": {"dtype": "float64"}}).run(df)
    assert result.type_issues == []


# ══════════════════════════════════════════════════════════════════════════════
# Schema: nullable check
# ══════════════════════════════════════════════════════════════════════════════

def test_nullable_false_catches_nans() -> None:
    df = _simple_df()
    df.loc[0, "age"] = float("nan")
    result = DataValidator(schema={"age": {"nullable": False}}).run(df)
    assert "age" in result.schema_violations
    assert not result.passed


def test_nullable_true_ignores_nans() -> None:
    df = _simple_df()
    df.loc[0, "age"] = float("nan")
    result = DataValidator(schema={"age": {"nullable": True}}).run(df)
    assert "age" not in result.schema_violations


# ══════════════════════════════════════════════════════════════════════════════
# Schema: numeric range check
# ══════════════════════════════════════════════════════════════════════════════

def test_range_violation_detected() -> None:
    df = _simple_df()
    df.loc[0, "age"] = 200.0   # > max 120
    result = DataValidator(schema={"age": {"min": 0, "max": 120}}).run(df)
    assert "age" in result.out_of_range
    assert result.out_of_range["age"]["violations"] == 1
    assert not result.passed


def test_range_within_bounds_passes() -> None:
    df = _simple_df()  # all ages 25-60
    result = DataValidator(schema={"age": {"min": 0, "max": 120}}).run(df)
    assert "age" not in result.out_of_range


def test_one_sided_range_min_only() -> None:
    df = _simple_df()
    df.loc[0, "age"] = -5.0
    result = DataValidator(schema={"age": {"min": 0}}).run(df)
    assert "age" in result.out_of_range


# ══════════════════════════════════════════════════════════════════════════════
# Schema: allowed values
# ══════════════════════════════════════════════════════════════════════════════

def test_allowed_values_violation_detected(clean_df: pd.DataFrame) -> None:
    df = clean_df.copy()
    df.loc[0, "status"] = "BANNED"
    result = DataValidator(
        schema={"status": {"allowed_values": ["active", "inactive"]}}
    ).run(df)
    assert "status" in result.schema_violations
    assert not result.passed


def test_allowed_values_all_valid(clean_df: pd.DataFrame) -> None:
    result = DataValidator(
        schema={"status": {"allowed_values": ["active", "inactive"]}}
    ).run(clean_df)
    assert "status" not in result.schema_violations


def test_allowed_values_ignores_nulls() -> None:
    df = pd.DataFrame({"cat": ["A", "B", None, "A"]})
    result = DataValidator(
        schema={"cat": {"nullable": True, "allowed_values": ["A", "B"]}}
    ).run(df)
    assert "cat" not in result.schema_violations


# ══════════════════════════════════════════════════════════════════════════════
# Regex: email
# ══════════════════════════════════════════════════════════════════════════════

def test_email_regex_detects_invalid(clean_df: pd.DataFrame) -> None:
    df = clean_df.copy()
    df.loc[[0, 1], "email"] = "not-an-email"
    result = DataValidator(schema={"email": {"regex": "email"}}).run(df)
    assert "email" in result.format_violations
    assert result.format_violations["email"]["invalid_count"] == 2
    assert not result.passed


def test_email_regex_passes_valid(clean_df: pd.DataFrame) -> None:
    result = DataValidator(schema={"email": {"regex": "email"}}).run(clean_df)
    assert "email" not in result.format_violations


# ══════════════════════════════════════════════════════════════════════════════
# Regex: phone
# ══════════════════════════════════════════════════════════════════════════════

def test_phone_regex_invalid_detected() -> None:
    df = pd.DataFrame({"phone": ["800.555.1234", "not-a-phone", "800.555.9999"]})
    result = DataValidator(schema={"phone": {"regex": "phone"}}).run(df)
    assert "phone" in result.format_violations
    assert result.format_violations["phone"]["invalid_count"] == 1


def test_phone_regex_valid_passes() -> None:
    df = pd.DataFrame({"phone": ["800.555.1234", "800.555.9999", "800.555.0001"]})
    result = DataValidator(schema={"phone": {"regex": "phone"}}).run(df)
    assert "phone" not in result.format_violations


# ══════════════════════════════════════════════════════════════════════════════
# Regex: custom pattern
# ══════════════════════════════════════════════════════════════════════════════

def test_custom_regex_applied() -> None:
    df = pd.DataFrame({"code": ["ABC-001", "DEF-002", "bad", "GHI-003"]})
    result = DataValidator(
        schema={"code": {"regex": r"^[A-Z]{3}-\d{3}$"}}
    ).run(df)
    assert "code" in result.format_violations
    assert result.format_violations["code"]["invalid_count"] == 1


def test_invalid_regex_raises() -> None:
    df = pd.DataFrame({"x": ["a", "b"]})
    validator = DataValidator(schema={"x": {"regex": r"[invalid("}})
    with pytest.raises(ValueError, match="Invalid regex"):
        validator.run(df)


# ══════════════════════════════════════════════════════════════════════════════
# Quality score
# ══════════════════════════════════════════════════════════════════════════════

def test_quality_score_perfect_clean_data(clean_df: pd.DataFrame) -> None:
    result = DataValidator().run(clean_df)
    assert result.quality_score == 100.0


def test_quality_score_decreases_with_issues(dirty_df: pd.DataFrame) -> None:
    result = DataValidator(
        schema={
            "email":  {"regex": "email"},
            "status": {"allowed_values": ["active", "inactive"]},
            "income": {"min": 0, "max": 500_000},
        }
    ).run(dirty_df)
    assert result.quality_score < 100.0
    assert result.quality_score >= 0.0


def test_quality_score_bounded_0_to_100() -> None:
    # Extremely bad data — score should floor at 0, not go negative
    df = pd.DataFrame({"a": [float("nan")] * 100})
    result = DataValidator(
        schema={"a": {"nullable": False, "min": 0, "max": 1}}
    ).run(df)
    assert 0.0 <= result.quality_score <= 100.0


# ══════════════════════════════════════════════════════════════════════════════
# Invalid rows export
# ══════════════════════════════════════════════════════════════════════════════

def test_invalid_rows_exported(dirty_df: pd.DataFrame) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "invalid.csv"
        result = DataValidator(
            schema={
                "email":  {"regex": "email"},
                "status": {"allowed_values": ["active", "inactive"]},
            }
        ).run(dirty_df, export_invalid_to=out)

        assert out.exists()
        exported = pd.read_csv(out)
        assert len(exported) > 0
        assert len(exported) == len(result.invalid_row_indices)


def test_no_export_when_no_invalid_rows(clean_df: pd.DataFrame) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "invalid.csv"
        DataValidator().run(clean_df, export_invalid_to=out)
        # No invalid rows → file should NOT be created
        assert not out.exists()


# ══════════════════════════════════════════════════════════════════════════════
# YAML schema loading
# ══════════════════════════════════════════════════════════════════════════════

def test_load_schema_from_yaml(tmp_path: Path) -> None:
    yaml_content = """
schema:
  age:
    dtype: float64
    nullable: true
    min: 0
    max: 120
  status:
    allowed_values:
      - active
      - inactive
"""
    yaml_file = tmp_path / "test_schema.yaml"
    yaml_file.write_text(yaml_content)

    schema = load_schema_from_yaml(yaml_file)
    assert "age" in schema
    assert "status" in schema
    assert schema["age"]["min"] == 0
    assert schema["age"]["max"] == 120
    assert schema["status"]["allowed_values"] == ["active", "inactive"]


def test_yaml_schema_integrates_with_validator(tmp_path: Path) -> None:
    yaml_file = tmp_path / "schema.yaml"
    yaml_file.write_text("""
schema:
  age:
    min: 0
    max: 120
""")
    df = pd.DataFrame({"age": [25.0, 200.0, 30.0]})  # 200 is out of range
    schema = load_schema_from_yaml(yaml_file)
    result = DataValidator(schema=schema).run(df)
    assert "age" in result.out_of_range


def test_yaml_missing_schema_key_raises(tmp_path: Path) -> None:
    yaml_file = tmp_path / "bad.yaml"
    yaml_file.write_text("columns:\n  age: {}\n")
    with pytest.raises(KeyError, match="schema"):
        load_schema_from_yaml(yaml_file)


def test_yaml_missing_file_raises() -> None:
    with pytest.raises(FileNotFoundError):
        load_schema_from_yaml("/nonexistent/path/schema.yaml")


# ══════════════════════════════════════════════════════════════════════════════
# Backward compatibility: legacy kwargs
# ══════════════════════════════════════════════════════════════════════════════

def test_legacy_expected_dtypes() -> None:
    df = _simple_df()
    # age is float64; declaring it as int64 should trigger a type issue
    result = DataValidator(expected_dtypes={"age": "int64"}).run(df)
    assert len(result.type_issues) == 1


def test_legacy_numeric_ranges() -> None:
    df = _simple_df()
    df.loc[0, "age"] = 200.0
    result = DataValidator(numeric_ranges={"age": (0, 120)}).run(df)
    assert "age" in result.out_of_range


def test_legacy_kwargs_combined_with_schema() -> None:
    df = _simple_df()
    df.loc[0, "age"] = 200.0
    result = DataValidator(
        schema={"name": {"nullable": False}},
        expected_dtypes={"age": "float64"},
        numeric_ranges={"age": (0, 120)},
    ).run(df)
    # dtype matches → no type issue; range violated → out_of_range
    assert result.type_issues == []
    assert "age" in result.out_of_range


# ══════════════════════════════════════════════════════════════════════════════
# Required columns
# ══════════════════════════════════════════════════════════════════════════════

def test_missing_required_column_fails() -> None:
    df = _simple_df()
    result = DataValidator(required_columns=["missing_col"]).run(df)
    assert not result.passed
    assert any("missing_col" in w for w in result.warnings)
