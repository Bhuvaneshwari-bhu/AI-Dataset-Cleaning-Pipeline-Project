"""
validator.py
Advanced configurable validation engine.

Architecture overview
─────────────────────
Three concerns are deliberately separated:

  1. Schema definition  – what the data *should* look like (ColumnSchema)
  2. Profiling          – what the data *actually* looks like (ColumnProfile)
  3. Validation         – the gap between 1 and 2 (DataValidator + ValidationResult)

Keeping them separate means you can reuse profiling for EDA without running
validation, and you can swap out the scoring formula without touching the
individual checks.

YAML schema support
───────────────────
Rules can be loaded from config/schema.yaml (via load_schema_from_yaml) instead
of hard-coded dicts.  Externalising rules to YAML lets non-engineers update them
without touching Python source code.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from logger import get_logger

logger = get_logger("validator")


# ══════════════════════════════════════════════════════════════════════════════
# Built-in regex patterns
# ══════════════════════════════════════════════════════════════════════════════
# Regex validation lets you assert that a string column obeys a structural
# format (e.g. every value in an "email" column must look like an email address)
# without writing custom loop logic.  Callers can pass a raw regex string
# instead of a named key.

_BUILT_IN_PATTERNS: dict[str, str] = {
    # RFC-5321-ish email: local@domain.tld (simplified, catches 99 % of typos)
    "email": r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$",

    # Phone: +1-800-555-0100, (800) 555-0100, 800.555.0100
    "phone": r"^(\+?\d{1,3}[\s\-.])?(\(?\d{3}\)?[\s\-.])\d{3}[\s\-\.]\d{4}$",

    # US ZIP: 12345 or 12345-6789
    "zip_us": r"^\d{5}(-\d{4})?$",

    # ISO 8601 date: 2024-01-31
    "date_iso": r"^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$",
}


# ══════════════════════════════════════════════════════════════════════════════
# YAML schema loader
# ══════════════════════════════════════════════════════════════════════════════

def load_schema_from_yaml(path: str | Path) -> dict[str, Any]:
    """
    Load schema rules from a YAML file and return them as a plain dict.

    The returned dict can be passed directly to DataValidator(schema=...).

    Expected YAML format:
        schema:
          age:
            dtype: float64
            min: 0
            max: 120
          email:
            regex: email
            nullable: false

    Parameters
    ----------
    path : path to the YAML config file (e.g. "config/schema.yaml")

    Raises
    ------
    FileNotFoundError : if the file does not exist
    KeyError          : if the YAML has no top-level "schema" key
    ImportError       : if pyyaml is not installed
    """
    try:
        import yaml
    except ImportError as exc:
        raise ImportError(
            "pyyaml is required for YAML schema loading. "
            "Install it with: pip install pyyaml"
        ) from exc

    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Schema config not found: {config_path}")

    with config_path.open() as fh:
        raw: dict[str, Any] = yaml.safe_load(fh)

    if "schema" not in raw:
        raise KeyError(
            f"YAML file '{config_path}' must have a top-level 'schema' key."
        )

    logger.info("Loaded schema from '%s' (%d column rules)", config_path, len(raw["schema"]))
    return raw["schema"]


# ══════════════════════════════════════════════════════════════════════════════
# Schema definition
# ══════════════════════════════════════════════════════════════════════════════
# Schema-based validation means you describe the *expected contract* of each
# column in one place (a Python dict or ColumnSchema object) and the validator
# checks every row against that contract automatically.  This is the same idea
# as JSON Schema, Pydantic models, or SQL CREATE TABLE constraints, but applied
# at runtime to DataFrames.
#
# Centralising rules in a schema:
#   • makes them easy to review and version-control alongside the code
#   • eliminates ad-hoc if/else checks scattered through preprocessing
#   • produces structured violation reports instead of silent data corruption

@dataclass
class ColumnSchema:
    """
    Rules for a single column.  All fields are optional; only those provided
    are checked.

    Parameters
    ----------
    dtype          : expected pandas dtype string, e.g. "float64", "object"
    nullable       : False means any NaN is a violation (default: True)
    min_val        : inclusive lower bound for numeric columns
    max_val        : inclusive upper bound for numeric columns
    allowed_values : exhaustive set of permitted values (categorical columns)
    regex          : named key ("email", "phone", …) or raw regex pattern string
    """
    dtype: str | None = None
    nullable: bool = True
    min_val: float | None = None
    max_val: float | None = None
    allowed_values: list[Any] | None = None
    regex: str | None = None


def _parse_schema(raw: dict[str, Any]) -> dict[str, ColumnSchema]:
    """
    Convert a plain dict (beginner-friendly) into {col: ColumnSchema}.

    Accepted dict format per column::

        {
            "age":    {"dtype": "float64", "nullable": True,  "min": 0, "max": 120},
            "email":  {"dtype": "object",  "nullable": False, "regex": "email"},
            "status": {"dtype": "object",  "nullable": False,
                       "allowed_values": ["active", "inactive"]},
        }
    """
    schema: dict[str, ColumnSchema] = {}
    for col, rules in raw.items():
        schema[col] = ColumnSchema(
            dtype=rules.get("dtype"),
            nullable=rules.get("nullable", True),
            min_val=rules.get("min"),
            max_val=rules.get("max"),
            allowed_values=rules.get("allowed_values"),
            regex=rules.get("regex"),
        )
    return schema


# ══════════════════════════════════════════════════════════════════════════════
# Column profiling
# ══════════════════════════════════════════════════════════════════════════════
# Profiling answers "what does this column actually contain?" before any
# cleaning happens.  In ML preprocessing this matters because:
#
#   • Skewed distributions → choose median imputation over mean
#   • High null rates       → decide whether to drop the column entirely
#   • Low unique counts     → identify pseudo-categorical numeric columns
#   • Extreme std/range     → flag candidates for scaling/normalisation
#
# Running profiling inside the validator means you get both the "is this valid?"
# answer AND the "what does it look like?" answer in one pass.

@dataclass
class ColumnProfile:
    """Descriptive statistics for one column."""
    dtype: str
    null_count: int
    null_pct: float
    unique_count: int
    # Numeric-only fields (None for non-numeric columns)
    min_val: float | None = None
    max_val: float | None = None
    mean: float | None = None
    median: float | None = None
    std: float | None = None


# ══════════════════════════════════════════════════════════════════════════════
# Validation result
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class ValidationResult:
    """
    Container for every finding produced by DataValidator.run().

    Attributes
    ----------
    passed              : False if any hard rule was violated
    missing_summary     : {col: {"count": n, "pct": x}} for cols with NaNs
    duplicate_count     : number of fully-duplicate rows
    type_issues         : list of dtype mismatch messages
    out_of_range        : {col: {violations, min_found, max_found, expected_range}}
    format_violations   : {col: {"pattern", "invalid_count", "invalid_indices", "sample_values"}}
    schema_violations   : {col: [violation message, ...]}
    profiles            : {col: ColumnProfile}
    quality_score       : 0–100 composite data quality score
    invalid_row_indices : set of row indices that failed at least one check
    warnings            : non-fatal advisory messages
    """
    passed: bool = True
    missing_summary: dict[str, Any] = field(default_factory=dict)
    duplicate_count: int = 0
    type_issues: list[str] = field(default_factory=list)
    out_of_range: dict[str, Any] = field(default_factory=dict)
    format_violations: dict[str, Any] = field(default_factory=dict)
    schema_violations: dict[str, Any] = field(default_factory=dict)
    profiles: dict[str, ColumnProfile] = field(default_factory=dict)
    quality_score: float = 100.0
    invalid_row_indices: set[Any] = field(default_factory=set)
    warnings: list[str] = field(default_factory=list)


# ══════════════════════════════════════════════════════════════════════════════
# Validator
# ══════════════════════════════════════════════════════════════════════════════

class DataValidator:
    """
    Validates a DataFrame against a configurable schema and set of rules.

    Parameters
    ----------
    schema : dict
        Per-column rules in plain-dict format (converted internally to
        ColumnSchema objects).  See _parse_schema() for the accepted format.
        Can also be loaded from YAML via load_schema_from_yaml().
    required_columns : list[str]
        Columns that must be present; their absence is a hard failure.
    expected_dtypes : dict  (legacy — prefer schema)
        {"col": "dtype"} pairs.  Merged into schema when provided.
    numeric_ranges : dict  (legacy — prefer schema)
        {"col": (min, max)} pairs.  Merged into schema when provided.

    Usage
    -----
        # From Python dict
        validator = DataValidator(
            schema={
                "email":  {"dtype": "object", "nullable": False, "regex": "email"},
                "age":    {"dtype": "float64", "nullable": True, "min": 0, "max": 120},
                "status": {"allowed_values": ["active", "inactive"]},
            },
        )

        # From YAML file
        from validator import DataValidator, load_schema_from_yaml
        validator = DataValidator(schema=load_schema_from_yaml("config/schema.yaml"))

        result = validator.run(df, export_invalid_to="output/invalid_rows.csv")
        print(f"Quality score: {result.quality_score:.1f}/100")
    """

    # ── Scoring weights ──────────────────────────────────────────────────────
    # Data quality scoring works by starting at 100 and subtracting penalties
    # that are proportional to how severe each problem is.  Weights are kept
    # here so they can be adjusted without touching the scoring logic.
    #
    # Design principle: missing data and duplicates are penalised proportionally
    # (the more missing, the bigger the cut) while structural violations use flat
    # per-column penalties (one bad column is as bad as ten bad values in it,
    # because the column is untrustworthy either way).

    _SCORE_MISSING_PER_PCT: float = 0.30    # 30 % missing overall → −9 pts
    _SCORE_DUPLICATE_PER_PCT: float = 0.20  # 10 % duplicate rows  → −2 pts
    _SCORE_TYPE_ISSUE: float = 5.0          # per dtype mismatch    → −5 pts each
    _SCORE_FORMAT_VIOLATION: float = 5.0    # per column with bad regex values
    _SCORE_SCHEMA_VIOLATION: float = 4.0    # per column with schema violations
    _SCORE_REQUIRED_MISSING: float = 5.0    # per missing required column

    def __init__(
        self,
        schema: dict[str, Any] | None = None,
        required_columns: list[str] | None = None,
        # Legacy kwargs kept for backward-compatibility with old callsites
        expected_dtypes: dict[str, str] | None = None,
        numeric_ranges: dict[str, tuple[float, float]] | None = None,
    ) -> None:
        self._schema: dict[str, ColumnSchema] = _parse_schema(schema or {})
        self.required_columns: list[str] = required_columns or []

        # Merge legacy kwargs into the schema so old code keeps working
        for col, dtype in (expected_dtypes or {}).items():
            self._schema.setdefault(col, ColumnSchema()).dtype = dtype

        for col, (lo, hi) in (numeric_ranges or {}).items():
            entry = self._schema.setdefault(col, ColumnSchema())
            entry.min_val = lo
            entry.max_val = hi

    # ── Profiling ────────────────────────────────────────────────────────────

    def _profile_columns(self, df: pd.DataFrame) -> dict[str, ColumnProfile]:
        """
        Compute descriptive statistics for every column.

        Why run this inside the validator?  Because the same pass that flags
        violations also needs to know the column's null rate (for scoring) and
        numeric distribution (for range checks).  Computing it once and caching
        in the result avoids re-reading the DataFrame later.
        """
        profiles: dict[str, ColumnProfile] = {}
        n = len(df)
        for col in df.columns:
            series = df[col]
            null_count = int(series.isnull().sum())
            profile = ColumnProfile(
                dtype=str(series.dtype),
                null_count=null_count,
                null_pct=round(null_count / n * 100, 2) if n else 0.0,
                unique_count=int(series.nunique(dropna=True)),
            )
            if pd.api.types.is_numeric_dtype(series):
                clean = series.dropna()
                if len(clean):
                    profile.min_val = float(clean.min())
                    profile.max_val = float(clean.max())
                    profile.mean = float(clean.mean())
                    profile.median = float(clean.median())
                    profile.std = float(clean.std())
            profiles[col] = profile
        return profiles

    # ── Basic checks ────────────────────────────────────────────────────────

    def _check_missing(self, df: pd.DataFrame) -> dict[str, Any]:
        missing = df.isnull().sum()
        pct = (missing / len(df) * 100).round(2)
        return {
            col: {"count": int(cnt), "pct": float(pct[col])}
            for col, cnt in missing.items()
            if cnt > 0
        }

    def _check_duplicates(self, df: pd.DataFrame) -> int:
        return int(df.duplicated().sum())

    def _check_required_columns(self, df: pd.DataFrame) -> list[str]:
        return [c for c in self.required_columns if c not in df.columns]

    # ── Schema validation ────────────────────────────────────────────────────

    def _check_schema(
        self, df: pd.DataFrame
    ) -> tuple[list[str], dict[str, Any], dict[str, list[str]], set[Any]]:
        """
        Validate each column against its ColumnSchema.

        Schema validation is "contract testing" for data: instead of writing
        ad-hoc guards like ``if df['age'].max() > 120: raise`` everywhere, you
        declare the contract once and validate it consistently.  The output is
        structured enough to be diff-ed between pipeline runs.

        Returns
        -------
        type_issues       : list of dtype mismatch messages
        out_of_range      : {col: range violation details}
        schema_violations : {col: [violation messages]}
        invalid_indices   : set of row indices that violated any schema rule
        """
        type_issues: list[str] = []
        out_of_range: dict[str, Any] = {}
        schema_violations: dict[str, list[str]] = {}
        invalid_indices: set[Any] = set()

        for col, rule in self._schema.items():
            if col not in df.columns:
                schema_violations.setdefault(col, []).append(
                    f"Column '{col}' declared in schema but not found in data."
                )
                continue

            series = df[col]
            col_violations: list[str] = []

            # ── dtype check ──────────────────────────────────────────────────
            if rule.dtype is not None:
                actual = str(series.dtype)
                if actual != rule.dtype:
                    type_issues.append(
                        f"'{col}': expected dtype '{rule.dtype}', got '{actual}'."
                    )

            # ── nullable check ───────────────────────────────────────────────
            # "nullable: False" means the column must never contain NaN.
            # Useful for primary keys, mandatory labels, target variables.
            if not rule.nullable:
                null_mask = series.isnull()
                if null_mask.any():
                    bad_idx = series[null_mask].index.tolist()
                    invalid_indices.update(bad_idx)
                    col_violations.append(
                        f"Non-nullable column has {int(null_mask.sum())} NaN(s)."
                    )

            # ── numeric range check ──────────────────────────────────────────
            if rule.min_val is not None or rule.max_val is not None:
                lo = rule.min_val if rule.min_val is not None else -np.inf
                hi = rule.max_val if rule.max_val is not None else np.inf
                range_mask = (series < lo) | (series > hi)
                if range_mask.any():
                    bad_idx = series[range_mask].index.tolist()
                    invalid_indices.update(bad_idx)
                    out_of_range[col] = {
                        "violations": int(range_mask.sum()),
                        "min_found": float(series.min()),
                        "max_found": float(series.max()),
                        "expected_range": [rule.min_val, rule.max_val],
                    }

            # ── allowed-values check ─────────────────────────────────────────
            # Categorical columns often have a fixed vocabulary (e.g. status
            # must be one of ["active", "inactive"]).  Checking this prevents
            # typos and data-entry errors from silently polluting downstream
            # one-hot encoders or groupby aggregations.
            if rule.allowed_values is not None:
                allowed = set(rule.allowed_values)
                non_null = series.dropna()
                bad_mask = non_null.apply(lambda v: v not in allowed)
                bad_idx = non_null[bad_mask].index.tolist()
                if bad_idx:
                    invalid_indices.update(bad_idx)
                    actual_vals = non_null[bad_mask].unique().tolist()
                    col_violations.append(
                        f"Found {len(bad_idx)} value(s) not in allowed set "
                        f"{rule.allowed_values}. Sample: {actual_vals[:5]}"
                    )

            if col_violations:
                schema_violations[col] = col_violations

        return type_issues, out_of_range, schema_violations, invalid_indices

    # ── Regex / format validation ────────────────────────────────────────────

    def _resolve_pattern(self, regex_key: str) -> str:
        """
        Return the regex pattern string for a named key or raw pattern.

        Regex validation is useful for string columns whose values must match a
        specific structural format (email, phone, date, custom code).  Checking
        format in the validation layer — rather than during feature engineering —
        means bad values are caught early, before they cause cryptic errors
        inside a tokeniser or parser many steps later.
        """
        return _BUILT_IN_PATTERNS.get(regex_key, regex_key)

    def _check_regex(
        self, df: pd.DataFrame
    ) -> tuple[dict[str, Any], set[Any]]:
        """
        For every schema column that declares a regex, test each non-null value.

        Returns
        -------
        format_violations : {col: {"pattern", "invalid_count", "invalid_indices",
                                   "sample_values"}}
        invalid_indices   : set of row indices with at least one format failure
        """
        format_violations: dict[str, Any] = {}
        invalid_indices: set[Any] = set()

        for col, rule in self._schema.items():
            if rule.regex is None or col not in df.columns:
                continue

            pattern = self._resolve_pattern(rule.regex)
            try:
                compiled = re.compile(pattern)
            except re.error as exc:
                raise ValueError(
                    f"Invalid regex for column '{col}': {pattern!r} — {exc}"
                ) from exc

            # Test only non-null string values; NaN handling is covered by nullable
            non_null = df[col].dropna().astype(str)
            bad_mask = ~non_null.str.match(compiled)
            bad_idx = non_null[bad_mask].index.tolist()

            if bad_idx:
                invalid_indices.update(bad_idx)
                format_violations[col] = {
                    "pattern": pattern,
                    "invalid_count": len(bad_idx),
                    "invalid_indices": bad_idx,
                    "sample_values": non_null[bad_mask].head(5).tolist(),
                }

        return format_violations, invalid_indices

    # ── Quality scoring ──────────────────────────────────────────────────────

    def _compute_quality_score(
        self,
        df: pd.DataFrame,
        result: ValidationResult,
        missing_required: list[str],
    ) -> float:
        """
        Produce a single 0–100 quality score summarising all findings.

        Scoring philosophy
        ──────────────────
        A score of 100 means "no problems found at all."  Deductions are
        proportional for volume problems (missing data, duplicates) and flat
        per-column for structural violations (type errors, bad formats), because
        one structurally broken column contaminates every row, not just a few.

        This score is NOT a replacement for domain-specific thresholds — callers
        should decide their own "acceptable" minimum (e.g. reject with score < 80).
        """
        score = 100.0
        n_rows = len(df)
        n_cells = n_rows * len(df.columns) if len(df.columns) else 1

        # 1. Missing values – proportional to overall missing-cell rate
        total_missing = sum(v["count"] for v in result.missing_summary.values())
        overall_missing_pct = total_missing / n_cells * 100
        score -= overall_missing_pct * self._SCORE_MISSING_PER_PCT

        # 2. Duplicates – proportional to duplicate row rate
        dup_pct = result.duplicate_count / n_rows * 100 if n_rows else 0
        score -= dup_pct * self._SCORE_DUPLICATE_PER_PCT

        # 3. Type mismatches – flat penalty per affected column
        score -= len(result.type_issues) * self._SCORE_TYPE_ISSUE

        # 4. Format (regex) violations – flat penalty per affected column
        score -= len(result.format_violations) * self._SCORE_FORMAT_VIOLATION

        # 5. Schema violations – flat penalty per affected column
        score -= len(result.schema_violations) * self._SCORE_SCHEMA_VIOLATION

        # 6. Missing required columns – flat penalty per absent column
        score -= len(missing_required) * self._SCORE_REQUIRED_MISSING

        return round(max(0.0, score), 1)

    # ── Invalid rows export ──────────────────────────────────────────────────

    def _export_invalid_rows(
        self,
        df: pd.DataFrame,
        invalid_indices: set[Any],
        output_path: str | Path,
    ) -> None:
        """
        Save rows that failed at least one validation check to a CSV file.

        Exporting invalid rows separately allows data engineers to:
          • Inspect and manually correct bad records
          • Feed them into a quarantine / human-review queue
          • Track the proportion of bad data across pipeline runs
        """
        if not invalid_indices:
            logger.info("No invalid rows to export.")
            return

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        invalid_df = df.loc[sorted(invalid_indices)].copy()
        invalid_df.to_csv(path, index=True)
        logger.info("%d invalid row(s) exported to '%s'", len(invalid_df), path)

    # ── Public API ───────────────────────────────────────────────────────────

    def run(
        self,
        df: pd.DataFrame,
        export_invalid_to: str | Path | None = None,
    ) -> ValidationResult:
        """
        Execute all checks, compute quality score, and return a ValidationResult.

        Parameters
        ----------
        df                : DataFrame to validate
        export_invalid_to : if provided, invalid rows are saved to this CSV path
        """
        logger.info("Running validation on %d rows × %d columns", len(df), len(df.columns))
        result = ValidationResult()

        # ── Required columns ─────────────────────────────────────────────────
        missing_required = self._check_required_columns(df)
        if missing_required:
            result.warnings.append(f"Missing required columns: {missing_required}")
            result.passed = False
            logger.warning("Missing required columns: %s", missing_required)

        # ── Basic checks ─────────────────────────────────────────────────────
        result.missing_summary = self._check_missing(df)
        result.duplicate_count = self._check_duplicates(df)

        # ── Column profiling ─────────────────────────────────────────────────
        result.profiles = self._profile_columns(df)

        # ── Schema validation ────────────────────────────────────────────────
        type_issues, out_of_range, schema_violations, schema_bad_idx = (
            self._check_schema(df)
        )
        result.type_issues = type_issues
        result.out_of_range = out_of_range
        result.schema_violations = schema_violations
        result.invalid_row_indices.update(schema_bad_idx)

        # ── Regex / format validation ────────────────────────────────────────
        format_violations, format_bad_idx = self._check_regex(df)
        result.format_violations = format_violations
        result.invalid_row_indices.update(format_bad_idx)

        # ── Determine overall pass/fail ──────────────────────────────────────
        if (result.type_issues or result.out_of_range
                or result.schema_violations or result.format_violations):
            result.passed = False

        # ── Quality score ────────────────────────────────────────────────────
        result.quality_score = self._compute_quality_score(df, result, missing_required)

        # ── Export invalid rows ──────────────────────────────────────────────
        if export_invalid_to is not None:
            self._export_invalid_rows(df, result.invalid_row_indices, export_invalid_to)

        # ── Summary ─────────────────────────────────────────────────────────
        status = "PASSED" if result.passed else "FAILED"
        log_fn = logger.info if result.passed else logger.warning
        log_fn(
            "%s | score: %s/100 | missing_cols: %d | duplicates: %d | "
            "type_issues: %d | format_violations: %d | schema_violations: %d",
            status,
            result.quality_score,
            len(result.missing_summary),
            result.duplicate_count,
            len(result.type_issues),
            len(result.format_violations),
            len(result.schema_violations),
        )
        return result
