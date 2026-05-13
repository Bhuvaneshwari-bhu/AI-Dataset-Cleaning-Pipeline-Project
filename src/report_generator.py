"""
report_generator.py
Produces a self-contained HTML data-quality report inspired by Great Expectations.

Report sections
───────────────
  1. Data Quality Score  – prominent colour-coded scorecard
  2. Dataset Overview    – row/column counts before and after cleaning
  3. Validation Results  – missing values, duplicates, type issues
  4. Column Profiles     – dtype, nulls, unique count, numeric stats
  5. Schema Violations   – allowed-value and nullable violations
  6. Format Violations   – regex validation failures with sample values
  7. Cleaning Log        – every transformation applied
  8. Anomaly Detection   – outlier counts per column
  9. Distributions       – histogram per numeric column
 10. Data Drift (opt.)   – mean/std/KS drift summary if a DriftReport is supplied

Seaborn palette-without-hue deprecation
────────────────────────────────────────
Until seaborn 0.12, passing ``palette=`` to barplot() coloured each bar using
the palette regardless of whether a ``hue`` grouping variable was present.
Seaborn 0.12 introduced a strict semantic model where palette only makes sense
alongside ``hue``.  Using palette without hue became a FutureWarning in 0.12–0.13
and will be a hard error in 0.14.

This is a common pattern in ML/data libraries: a convenience shortcut that worked
by accident gets formalised into an explicit API.  Maintainers deprecate rather
than silently break, giving users a migration window.  The lesson for production
code: always pin major library versions *and* run chart code under
``-W error::FutureWarning`` in CI so breakage surfaces before the library drops support.

Fix: set ``hue=x`` (same variable as the x-axis) and ``legend=False``.  Seaborn
maps one palette colour per category level, which is visually identical to the old
behaviour while satisfying the new semantic contract.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import matplotlib

matplotlib.use("Agg")  # headless backend – no display needed
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from anomaly_detector import AnomalyReport
from logger import get_logger
from validator import ValidationResult

if TYPE_CHECKING:
    from drift_detector import DriftReport

logger = get_logger("report_generator")


# ══════════════════════════════════════════════════════════════════════════════
# Chart helpers
# ══════════════════════════════════════════════════════════════════════════════


def _save_missing_bar(missing_summary: dict[str, Any], output_dir: Path) -> str | None:
    """Bar chart of missing-value percentages; returns the saved file path."""
    if not missing_summary:
        return None
    cols = list(missing_summary.keys())
    pcts = [v["pct"] for v in missing_summary.values()]

    fig, ax = plt.subplots(figsize=(max(6, len(cols)), 4))
    # hue=cols mirrors the x variable so each bar gets a distinct palette colour.
    # legend=False suppresses the redundant colour legend (x labels already
    # identify each bar).  This is the seaborn-recommended replacement for the
    # deprecated ``palette`` without ``hue`` pattern (removed in seaborn 0.14).
    sns.barplot(x=cols, y=pcts, hue=cols, palette="flare", legend=False, ax=ax)
    ax.set_title("Missing Values (%)")
    ax.set_ylabel("% Missing")
    ax.set_xlabel("Column")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    path = output_dir / "missing_values.png"
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return str(path)


def _save_distribution_plots(df: pd.DataFrame, output_dir: Path) -> list[str]:
    """Histogram for each numeric column; returns list of saved file paths."""
    paths: list[str] = []
    numeric_cols = df.select_dtypes(include="number").columns
    for col in numeric_cols:
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.histplot(df[col].dropna(), kde=True, color="steelblue", ax=ax)
        ax.set_title(f"Distribution: {col}")
        plt.tight_layout()
        path = output_dir / f"dist_{col}.png"
        fig.savefig(path, dpi=120)
        plt.close(fig)
        paths.append(str(path))
    return paths


# ══════════════════════════════════════════════════════════════════════════════
# Report generator
# ══════════════════════════════════════════════════════════════════════════════


class ReportGenerator:
    """
    Collects pipeline artefacts and writes a Great Expectations-inspired HTML report.

    Parameters
    ----------
    output_dir : directory where report.html and chart PNGs are saved

    Usage
    -----
        gen = ReportGenerator(output_dir="reports/")
        gen.generate(df_raw, df_clean, validation_result, anomaly_report, clean_log)
    """

    def __init__(self, output_dir: str | Path = "reports") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(
        self,
        df_raw: pd.DataFrame,
        df_clean: pd.DataFrame,
        validation_result: ValidationResult,
        anomaly_report: AnomalyReport,
        clean_log: list[str],
        title: str = "AI Dataset Cleaning & Validation Report",
        drift_report: DriftReport | None = None,
    ) -> Path:
        """
        Build the report and save it as HTML.  Returns the output path.

        Parameters
        ----------
        df_raw           : original unmodified DataFrame
        df_clean         : DataFrame after cleaning
        validation_result: output of DataValidator.run()
        anomaly_report   : output of AnomalyDetector.detect()
        clean_log        : list of transformation messages from DataCleaner.run()
        title            : report heading
        drift_report     : optional DriftReport for the drift section
        """
        logger.info("Generating report...")

        missing_chart = _save_missing_bar(validation_result.missing_summary, self.output_dir)
        dist_charts = _save_distribution_plots(df_clean, self.output_dir)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        html = self._build_html(
            title=title,
            timestamp=timestamp,
            df_raw=df_raw,
            df_clean=df_clean,
            validation_result=validation_result,
            anomaly_report=anomaly_report,
            clean_log=clean_log,
            missing_chart=missing_chart,
            dist_charts=dist_charts,
            drift_report=drift_report,
        )

        report_path = self.output_dir / "report.html"
        report_path.write_text(html, encoding="utf-8")
        logger.info("HTML report saved to '%s'", report_path)

        # Optional PDF export
        try:
            from weasyprint import HTML as WeasyprintHTML

            pdf_path = self.output_dir / "report.pdf"
            WeasyprintHTML(filename=str(report_path)).write_pdf(str(pdf_path))
            logger.info("PDF report saved to '%s'", pdf_path)
        except ImportError:
            logger.info("weasyprint not available — skipping PDF export.")
        except Exception as exc:
            logger.warning("PDF export failed: %s", exc)

        return report_path

    # ── HTML builder ────────────────────────────────────────────────────────

    def _build_html(
        self,
        title: str,
        timestamp: str,
        df_raw: pd.DataFrame,
        df_clean: pd.DataFrame,
        validation_result: ValidationResult,
        anomaly_report: AnomalyReport,
        clean_log: list[str],
        missing_chart: str | None,
        dist_charts: list[str],
        drift_report: DriftReport | None,
    ) -> str:

        # ── Helper fragments ─────────────────────────────────────────────────

        def badge(ok: bool) -> str:
            colour, text = ("#2e7d32", "✓ PASSED") if ok else ("#c62828", "✗ FAILED")
            return (
                f'<span style="background:{colour};color:#fff;padding:3px 12px;'
                f'border-radius:4px;font-size:.85em;font-weight:bold">{text}</span>'
            )

        def score_colour(score: float) -> str:
            if score >= 80:
                return "#2e7d32"
            if score >= 60:
                return "#e65100"
            return "#c62828"

        score = validation_result.quality_score
        sc = score_colour(score)

        # ── Section 1: Quality score card ────────────────────────────────────
        total_issues = (
            len(validation_result.missing_summary)
            + (1 if validation_result.duplicate_count else 0)
            + len(validation_result.type_issues)
            + len(validation_result.format_violations)
            + len(validation_result.schema_violations)
            + len(validation_result.out_of_range)
        )
        invalid_count = len(validation_result.invalid_row_indices)
        invalid_pct = round(invalid_count / len(df_raw) * 100, 1) if len(df_raw) else 0

        score_card = f"""
        <div style="display:flex;gap:20px;flex-wrap:wrap;margin-bottom:30px">
          <div class="card" style="border-left:6px solid {sc}">
            <div style="font-size:3em;font-weight:bold;color:{sc}">{score}</div>
            <div style="color:#555;font-size:.9em">Quality Score / 100</div>
          </div>
          <div class="card">
            <div style="font-size:2em;font-weight:bold">{len(df_raw):,}</div>
            <div style="color:#555;font-size:.9em">Raw Rows</div>
          </div>
          <div class="card">
            <div style="font-size:2em;font-weight:bold">{len(df_clean):,}</div>
            <div style="color:#555;font-size:.9em">Clean Rows</div>
          </div>
          <div class="card">
            <div style="font-size:2em;font-weight:bold;color:{"#c62828" if total_issues else "#2e7d32"}">{total_issues}</div>
            <div style="color:#555;font-size:.9em">Issue Types Found</div>
          </div>
          <div class="card">
            <div style="font-size:2em;font-weight:bold;color:{"#c62828" if invalid_count else "#2e7d32"}">{invalid_count}</div>
            <div style="color:#555;font-size:.9em">Invalid Rows ({invalid_pct}%)</div>
          </div>
        </div>"""

        # ── Section 2: Validation ────────────────────────────────────────────
        missing_rows = (
            "".join(
                f"<tr><td>{col}</td><td>{v['count']}</td><td>{v['pct']}%</td></tr>"
                for col, v in validation_result.missing_summary.items()
            )
            or "<tr><td colspan=3 style='color:#2e7d32'>No missing values.</td></tr>"
        )

        type_section = ""
        if validation_result.type_issues:
            items = "".join(f"<li>{i}</li>" for i in validation_result.type_issues)
            type_section = f"<h3>Type Issues</h3><ul>{items}</ul>"

        missing_chart_tag = (
            f'<img src="{missing_chart}" style="max-width:600px;margin-top:12px">'
            if missing_chart
            else ""
        )

        # ── Section 3: Column profiles ───────────────────────────────────────
        profile_rows = ""
        for col, p in validation_result.profiles.items():
            num_stats = (
                f"{p.min_val:.3g} / {p.max_val:.3g} / {p.mean:.3g} / {p.median:.3g}"
                if p.mean is not None
                else "—"
            )
            null_colour = (
                "#c62828" if p.null_pct > 10 else ("#e65100" if p.null_pct > 0 else "#2e7d32")
            )
            profile_rows += (
                f"<tr><td>{col}</td><td>{p.dtype}</td>"
                f"<td style='color:{null_colour}'>{p.null_count} ({p.null_pct}%)</td>"
                f"<td>{p.unique_count}</td><td>{num_stats}</td></tr>"
            )

        # ── Section 4: Schema violations ────────────────────────────────────
        schema_viol_html = ""
        if validation_result.schema_violations:
            rows = ""
            for col, msgs in validation_result.schema_violations.items():
                for msg in msgs:
                    rows += f"<tr><td>{col}</td><td>{msg}</td></tr>"
            schema_viol_html = f"""
            <h2>4. Schema Violations {badge(False)}</h2>
            <table>
              <tr><th>Column</th><th>Violation</th></tr>
              {rows}
            </table>"""
        else:
            schema_viol_html = (
                f"<h2>4. Schema Violations {badge(True)}</h2><p>No schema violations detected.</p>"
            )

        # ── Section 5: Format violations ────────────────────────────────────
        format_viol_html = ""
        if validation_result.format_violations:
            rows = ""
            for col, info in validation_result.format_violations.items():
                samples = ", ".join(str(v) for v in info["sample_values"])
                rows += (
                    f"<tr><td>{col}</td><td><code>{info['pattern'][:60]}</code></td>"
                    f"<td>{info['invalid_count']}</td><td>{samples}</td></tr>"
                )
            format_viol_html = f"""
            <h2>5. Format Violations {badge(False)}</h2>
            <table>
              <tr><th>Column</th><th>Pattern</th><th>Invalid Count</th><th>Sample Invalid Values</th></tr>
              {rows}
            </table>"""
        else:
            format_viol_html = (
                f"<h2>5. Format Violations {badge(True)}</h2><p>All format checks passed.</p>"
            )

        # ── Section 6: Range violations ──────────────────────────────────────
        range_viol_html = ""
        if validation_result.out_of_range:
            rows = ""
            for col, info in validation_result.out_of_range.items():
                rows += (
                    f"<tr><td>{col}</td><td>{info['violations']}</td>"
                    f"<td>{info['min_found']:.3g} – {info['max_found']:.3g}</td>"
                    f"<td>{info['expected_range'][0]} – {info['expected_range'][1]}</td></tr>"
                )
            range_viol_html = f"""
            <h2>6. Range Violations {badge(False)}</h2>
            <table>
              <tr><th>Column</th><th>Violations</th><th>Actual Range</th><th>Expected Range</th></tr>
              {rows}
            </table>"""

        # ── Section 7: Outliers ──────────────────────────────────────────────
        outlier_rows = (
            "".join(
                f"<tr><td>{col}</td><td>{v['count']}</td><td>{v['pct']}%</td></tr>"
                for col, v in anomaly_report.column_results.items()
                if v["count"] > 0
            )
            or "<tr><td colspan=3 style='color:#2e7d32'>No outliers detected.</td></tr>"
        )

        # ── Section 8: Drift ─────────────────────────────────────────────────
        drift_html = ""
        if drift_report is not None:
            drift_colour = "#c62828" if drift_report.drifted_columns else "#2e7d32"
            drift_rows = ""
            for col, dr in drift_report.column_results.items():
                flag = "⚠ DRIFT" if dr.drifted else "OK"
                flag_colour = "#c62828" if dr.drifted else "#2e7d32"
                # Pre-format optional floats so f-string format specs stay simple
                ms = f"{dr.mean_shift:.3f}" if dr.mean_shift is not None else "—"
                sr = f"{dr.std_ratio:.3f}" if dr.std_ratio is not None else "—"
                ks = f"{dr.ks_statistic:.3f}" if dr.ks_statistic is not None else "—"
                kp = f"{dr.ks_p_value:.4f}" if dr.ks_p_value is not None else "—"
                drift_rows += (
                    f"<tr><td>{col}</td><td>{ms}</td><td>{sr}</td>"
                    f"<td>{ks}</td><td>{kp}</td>"
                    f"<td style='color:{flag_colour};font-weight:bold'>{flag}</td></tr>"
                )
            drift_html = f"""
            <h2>9. Data Drift Detection
              <span style="background:{drift_colour};color:#fff;padding:2px 10px;
                border-radius:4px;font-size:.75em;margin-left:8px">
                {len(drift_report.drifted_columns)} column(s) drifted
              </span>
            </h2>
            <p>Baseline: {drift_report.baseline_rows:,} rows |
               Incoming: {drift_report.incoming_rows:,} rows |
               Overall drift score: {drift_report.overall_drift_score}/100</p>
            <table>
              <tr><th>Column</th><th>Mean Shift (σ)</th><th>Std Ratio</th>
                  <th>KS Statistic</th><th>KS p-value</th><th>Status</th></tr>
              {drift_rows}
            </table>"""

        # ── Cleaning log ──────────────────────────────────────────────────────
        clean_log_items = "".join(f"<li>{s}</li>" for s in clean_log) or "<li>No changes.</li>"

        # ── Distribution charts ───────────────────────────────────────────────
        dist_chart_tags = (
            "".join(f'<img src="{p}" style="max-width:400px;margin:8px">' for p in dist_charts)
            or "<p>No numeric columns for distribution plots.</p>"
        )

        # ── Assemble ─────────────────────────────────────────────────────────
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{title}</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; }}
    body   {{ font-family: "Segoe UI", Arial, sans-serif; margin: 40px; color: #222; background: #f9f9f9; }}
    h1     {{ color: #1a237e; margin-bottom: 4px; }}
    h2     {{ color: #283593; border-bottom: 2px solid #e8eaf6; padding-bottom: 6px; margin-top: 36px; }}
    h3     {{ color: #3949ab; }}
    table  {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; background: #fff; }}
    th, td {{ border: 1px solid #ddd; padding: 8px 12px; text-align: left; font-size: .9em; }}
    th     {{ background: #e8eaf6; font-weight: 600; }}
    tr:nth-child(even) {{ background: #f5f5f5; }}
    ul     {{ line-height: 1.9; }}
    code   {{ background: #efefef; padding: 1px 5px; border-radius: 3px; font-size: .85em; }}
    .meta  {{ color: #777; font-size: .85em; margin-bottom: 24px; }}
    .card  {{ background: #fff; border-radius: 8px; padding: 18px 24px;
              box-shadow: 0 1px 4px rgba(0,0,0,.1); min-width: 140px; }}
    .charts img {{ margin: 8px; border: 1px solid #ddd; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,.08); }}
  </style>
</head>
<body>
  <h1>{title}</h1>
  <p class="meta">Generated: {timestamp} &nbsp;|&nbsp;
     Validation: {badge(validation_result.passed)}</p>

  {score_card}

  <h2>1. Dataset Overview</h2>
  <table>
    <tr><th>Metric</th><th>Raw</th><th>After Cleaning</th></tr>
    <tr><td>Rows</td><td>{len(df_raw):,}</td><td>{len(df_clean):,}</td></tr>
    <tr><td>Columns</td><td>{len(df_raw.columns)}</td><td>{len(df_clean.columns)}</td></tr>
    <tr><td>Duplicate rows</td><td>{validation_result.duplicate_count}</td><td>0</td></tr>
    <tr><td>Invalid rows</td><td>{invalid_count} ({invalid_pct}%)</td><td>—</td></tr>
  </table>

  <h2>2. Missing Values {badge(not bool(validation_result.missing_summary))}</h2>
  <table>
    <tr><th>Column</th><th>Missing Count</th><th>Missing %</th></tr>
    {missing_rows}
  </table>
  {type_section}
  {missing_chart_tag}

  <h2>3. Column Profiles</h2>
  <table>
    <tr><th>Column</th><th>Dtype</th><th>Null Count (%)</th>
        <th>Unique</th><th>Min / Max / Mean / Median</th></tr>
    {profile_rows}
  </table>

  {schema_viol_html}

  {format_viol_html}

  {range_viol_html}

  <h2>{"7" if range_viol_html else "6"}. Cleaning Log</h2>
  <ul>{clean_log_items}</ul>

  <h2>{"8" if range_viol_html else "7"}. Anomaly Detection ({anomaly_report.method.upper()})</h2>
  <table>
    <tr><th>Column</th><th>Outlier Count</th><th>Outlier %</th></tr>
    {outlier_rows}
  </table>

  {drift_html}

  <h2>{"10" if drift_html else "9" if range_viol_html else "8"}. Distributions (Clean Data)</h2>
  <div class="charts">{dist_chart_tags}</div>
</body>
</html>"""
