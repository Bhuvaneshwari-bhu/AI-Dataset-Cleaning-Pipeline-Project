"""
drift_detector.py
Lightweight data drift detection for numeric columns.

Data drift is the statistical change in a feature's distribution between
two datasets — typically a "baseline" (training set or last known-good batch)
and an "incoming" batch (new data arriving in production).

Why drift detection matters for ML pipelines:
  • A model trained on one distribution degrades silently when the input
    distribution shifts — there is no obvious error, just quietly wrong
    predictions.
  • Detecting drift early lets you retrain before accuracy degrades, rather
    than after users complain.
  • It is distinct from data quality (missing values, wrong types): data can
    be structurally valid but statistically different from the training set.

This module keeps dependencies minimal: numpy and pandas are always present.
scipy is used for the Kolmogorov–Smirnov test when available; when it is
not, a simpler threshold-based check on mean/std shift is used as a fallback.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from logger import get_logger

logger = get_logger("drift_detector")

try:
    from scipy import stats as _scipy_stats

    _HAS_SCIPY = True
except ImportError:  # pragma: no cover
    _HAS_SCIPY = False
    logger.warning("scipy not found — KS test unavailable; using mean/std thresholds only.")


# ══════════════════════════════════════════════════════════════════════════════
# Result types
# ══════════════════════════════════════════════════════════════════════════════


@dataclass
class ColumnDriftResult:
    """
    Drift statistics for one numeric column.

    Attributes
    ----------
    mean_shift    : normalised shift = (new_mean - base_mean) / base_std.
                    |mean_shift| > 0.5 is a typical "significant" threshold.
    std_ratio     : new_std / base_std.  Values far from 1.0 indicate the
                    spread of the distribution has changed.
    ks_statistic  : Kolmogorov–Smirnov D-statistic (0 = identical, 1 = maximally
                    different distributions).  None when scipy is unavailable.
    ks_p_value    : p-value of the KS test.  Small values (< alpha) indicate
                    the two samples come from different distributions.
    drifted       : True when the column is flagged as drifted.
    """

    mean_shift: float | None = None
    std_ratio: float | None = None
    ks_statistic: float | None = None
    ks_p_value: float | None = None
    drifted: bool = False


@dataclass
class DriftReport:
    """
    Summary of drift across all shared numeric columns.

    Attributes
    ----------
    baseline_rows      : number of rows in the baseline dataset
    incoming_rows      : number of rows in the incoming dataset
    column_results     : per-column drift statistics
    drifted_columns    : names of columns flagged as drifted
    overall_drift_score: 0 = no drift detected, 100 = all columns drifted
    """

    baseline_rows: int
    incoming_rows: int
    column_results: dict[str, ColumnDriftResult] = field(default_factory=dict)
    drifted_columns: list[str] = field(default_factory=list)
    overall_drift_score: float = 0.0


# ══════════════════════════════════════════════════════════════════════════════
# Detector
# ══════════════════════════════════════════════════════════════════════════════


class DriftDetector:
    """
    Compares numeric distributions between a baseline and an incoming DataFrame.

    Usage
    -----
        detector = DriftDetector(ks_alpha=0.05, mean_shift_threshold=0.5)
        report = detector.compare(df_baseline, df_incoming)

        if report.drifted_columns:
            print(f"Drift detected in: {report.drifted_columns}")

    Parameters
    ----------
    ks_alpha             : p-value threshold for the KS test; below this the
                           column is flagged as drifted (default 0.05).
    mean_shift_threshold : |normalised mean shift| above which a column is
                           flagged when scipy is unavailable (default 0.5 std).
    std_ratio_threshold  : std ratio outside (1/t, t) flags the column
                           (default 2.0, i.e. the spread doubled or halved).
    """

    def __init__(
        self,
        ks_alpha: float = 0.05,
        mean_shift_threshold: float = 0.5,
        std_ratio_threshold: float = 2.0,
    ) -> None:
        self.ks_alpha = ks_alpha
        self.mean_shift_threshold = mean_shift_threshold
        self.std_ratio_threshold = std_ratio_threshold

    # ── Private helpers ──────────────────────────────────────────────────────

    def _compare_column(
        self,
        baseline: pd.Series,
        incoming: pd.Series,
    ) -> ColumnDriftResult:
        """Compute drift statistics between two numeric series."""
        base_clean = baseline.dropna().to_numpy(dtype=float)
        inc_clean = incoming.dropna().to_numpy(dtype=float)

        if len(base_clean) < 2 or len(inc_clean) < 2:
            return ColumnDriftResult()

        base_mean = float(np.mean(base_clean))
        base_std = float(np.std(base_clean, ddof=1))
        inc_mean = float(np.mean(inc_clean))
        inc_std = float(np.std(inc_clean, ddof=1))

        # Normalised mean shift: how many baseline std-devs did the mean move?
        mean_shift = (inc_mean - base_mean) / base_std if base_std > 0 else None

        # Std ratio: did the spread change significantly?
        std_ratio = (inc_std / base_std) if base_std > 0 else None

        # KS test: are the two samples drawn from the same distribution?
        ks_stat: float | None = None
        ks_pval: float | None = None
        if _HAS_SCIPY:
            result = _scipy_stats.ks_2samp(base_clean, inc_clean)
            ks_stat = float(result.statistic)
            ks_pval = float(result.pvalue)

        # Flag as drifted
        drifted = False
        if _HAS_SCIPY and ks_pval is not None:
            drifted = ks_pval < self.ks_alpha
        else:
            # Fallback: flag on mean shift or std ratio
            if mean_shift is not None and abs(mean_shift) > self.mean_shift_threshold:
                drifted = True
            if std_ratio is not None:
                lo = 1.0 / self.std_ratio_threshold
                hi = self.std_ratio_threshold
                if not (lo <= std_ratio <= hi):
                    drifted = True

        return ColumnDriftResult(
            mean_shift=round(mean_shift, 4) if mean_shift is not None else None,
            std_ratio=round(std_ratio, 4) if std_ratio is not None else None,
            ks_statistic=round(ks_stat, 4) if ks_stat is not None else None,
            ks_p_value=round(ks_pval, 4) if ks_pval is not None else None,
            drifted=drifted,
        )

    # ── Public API ───────────────────────────────────────────────────────────

    def compare(
        self,
        baseline: pd.DataFrame,
        incoming: pd.DataFrame,
    ) -> DriftReport:
        """
        Compare distributions of all shared numeric columns.

        Only columns present in both DataFrames and of numeric dtype are
        evaluated.  Non-numeric columns are skipped without error.

        Parameters
        ----------
        baseline : reference dataset (e.g. training data or last good batch)
        incoming : new data to check against the baseline

        Returns
        -------
        DriftReport with per-column statistics and an overall drift score.
        """
        logger.info(
            "Comparing distributions — baseline: %d rows, incoming: %d rows",
            len(baseline),
            len(incoming),
        )

        shared_cols = sorted(set(baseline.columns) & set(incoming.columns))
        numeric_cols = [
            c
            for c in shared_cols
            if pd.api.types.is_numeric_dtype(baseline[c])
            and pd.api.types.is_numeric_dtype(incoming[c])
        ]

        report = DriftReport(
            baseline_rows=len(baseline),
            incoming_rows=len(incoming),
        )

        for col in numeric_cols:
            result = self._compare_column(baseline[col], incoming[col])
            report.column_results[col] = result
            if result.drifted:
                report.drifted_columns.append(col)

        # overall_drift_score: fraction of columns that drifted, scaled to 0–100
        if numeric_cols:
            report.overall_drift_score = round(
                len(report.drifted_columns) / len(numeric_cols) * 100, 1
            )

        logger.info(
            "Drift check complete — %d/%d numeric column(s) drifted | score: %.1f/100",
            len(report.drifted_columns),
            len(numeric_cols),
            report.overall_drift_score,
        )
        return report
