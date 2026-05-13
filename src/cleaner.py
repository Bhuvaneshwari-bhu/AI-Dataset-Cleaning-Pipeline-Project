"""
cleaner.py
Applies a sequence of cleaning transformations to the DataFrame.
Each method returns a new DataFrame (immutable style) and logs what it did,
making it easy to audit exactly what changed at each step.

Pandas chained-assignment note
───────────────────────────────
Patterns like  df[col].fillna(value, inplace=True)  are "chained" because
they first index into df (producing a temporary Series), then call a mutating
method on that temporary.  Pandas cannot guarantee whether the temporary is a
view or a copy of the underlying data, so the mutation may silently do nothing
on a copy while appearing to work on a view.  Pandas 2.x raises a
FutureWarning for this; pandas 3.0 removes inplace= from indexing results
entirely and will raise a ChainedAssignmentError.

The safe pattern is explicit column reassignment:
  df[col] = df[col].fillna(value)
This always writes back to the original DataFrame unambiguously, regardless
of whether the right-hand side was a view or a copy.

ETL systems should avoid inplace mutation because it makes pipelines harder
to debug — once you mutate a DataFrame in place, you lose the original state
and cannot compare before/after without keeping an explicit copy.  Returning
new DataFrames at each step keeps the audit trail clear and the data lineage
explicit.
"""

from typing import Any

import pandas as pd

from logger import get_logger

logger = get_logger("cleaner")


class DataCleaner:
    """
    Cleans a DataFrame through a configurable series of steps.

    Each step is isolated in its own method.  Returning new DataFrames (rather
    than mutating in place) means every step is testable in isolation and the
    original DataFrame is always preserved for comparison.

    Parameters
    ----------
    fill_strategy   : how to impute missing numeric values —
                      "median" | "mean" | "mode" | "drop"
    custom_fills    : per-column override, e.g. {"age": 0, "label": "unknown"}
    drop_duplicate  : remove fully duplicate rows (default True)
    strip_whitespace: strip leading/trailing whitespace from string columns
    """

    def __init__(
        self,
        fill_strategy: str = "median",
        custom_fills: dict[str, Any] | None = None,
        drop_duplicate: bool = True,
        strip_whitespace: bool = True,
    ) -> None:
        self.fill_strategy = fill_strategy
        self.custom_fills = custom_fills or {}
        self.drop_duplicate = drop_duplicate
        self.strip_whitespace = strip_whitespace
        self._log: list[str] = []

    # ── Private helpers ──────────────────────────────────────────────────────

    def _log_step(self, message: str) -> None:
        self._log.append(message)
        logger.info(message)

    def _handle_missing(self, df: pd.DataFrame) -> pd.DataFrame:
        # df.copy() is called by the caller before this method, so df is
        # already a fresh copy.  All assignments below use explicit column
        # reassignment (df[col] = ...) to avoid chained-assignment warnings.
        for col in df.columns:
            n_missing = int(df[col].isnull().sum())
            if n_missing == 0:
                continue

            if col in self.custom_fills:
                # Explicit reassignment: avoids chained write on df[col]
                df[col] = df[col].fillna(self.custom_fills[col])
                self._log_step(
                    f"Filled {n_missing} NaN(s) in '{col}' with custom value "
                    f"'{self.custom_fills[col]}'."
                )
            elif self.fill_strategy == "drop":
                # dropna returns a new DataFrame; reassign keeps data lineage clear
                df = df.dropna(subset=[col]).reset_index(drop=True)
                self._log_step(f"Dropped rows with NaN in '{col}' ({n_missing} rows).")
            elif pd.api.types.is_numeric_dtype(df[col]):
                if self.fill_strategy == "mean":
                    fill_val: Any = df[col].mean()
                elif self.fill_strategy == "mode":
                    fill_val = df[col].mode()[0]
                else:
                    fill_val = df[col].median()
                # Explicit reassignment: new Series written back into df directly
                df[col] = df[col].fillna(fill_val)
                self._log_step(
                    f"Filled {n_missing} NaN(s) in '{col}' with "
                    f"{self.fill_strategy} ({fill_val:.4g})."
                )
            else:
                fill_val = df[col].mode()[0] if not df[col].mode().empty else "UNKNOWN"
                # Same explicit-reassignment pattern for categorical/object columns
                df[col] = df[col].fillna(fill_val)
                self._log_step(
                    f"Filled {n_missing} NaN(s) in categorical '{col}' with mode ('{fill_val}')."
                )
        return df

    def _remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        before = len(df)
        df = df.drop_duplicates().reset_index(drop=True)
        removed = before - len(df)
        if removed:
            self._log_step(f"Removed {removed} duplicate row(s).")
        return df

    def _strip_strings(self, df: pd.DataFrame) -> pd.DataFrame:
        str_cols = df.select_dtypes(include="object").columns
        for col in str_cols:
            df[col] = df[col].str.strip()
        if len(str_cols):
            self._log_step(f"Stripped whitespace from {len(str_cols)} string column(s).")
        return df

    def _standardize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        # snake_case column names keep downstream code consistent
        df.columns = (
            df.columns
            .str.strip()
            .str.lower()
            .str.replace(r"[\s\-]+", "_", regex=True)
            .str.replace(r"[^\w]", "", regex=True)
        )
        self._log_step("Standardized column names to snake_case.")
        return df

    # ── Public API ───────────────────────────────────────────────────────────

    def run(self, df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
        """
        Apply all cleaning steps and return (clean_df, change_log).

        The input DataFrame is never mutated; a copy is made at the start of
        _handle_missing so callers can compare before/after freely.
        """
        self._log = []
        logger.info("Starting cleaning pipeline on %d rows × %d columns", len(df), len(df.columns))

        df = self._standardize_column_names(df.copy())
        if self.strip_whitespace:
            df = self._strip_strings(df)
        if self.drop_duplicate:
            df = self._remove_duplicates(df)
        df = self._handle_missing(df)

        logger.info("Cleaning complete — %d transformation(s) applied", len(self._log))
        return df, list(self._log)
