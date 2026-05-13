"""
conftest.py
Shared pytest fixtures for the pipeline test suite.

pytest discovers this file automatically and makes its fixtures available
to every test module without explicit imports.

sys.path note: pytest.ini adds src/ via the pythonpath option (pytest ≥ 7).
The manual insert below is a safety net for older pytest versions.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Safety-net: ensure src/ is importable regardless of pytest version
_src = Path(__file__).parent.parent / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))


# ── Shared DataFrames ────────────────────────────────────────────────────────

@pytest.fixture
def clean_df() -> pd.DataFrame:
    """100-row synthetic DataFrame with no quality issues."""
    rng = np.random.default_rng(42)
    return pd.DataFrame({
        "id":     range(1, 101),
        "age":    rng.integers(18, 75, 100).astype(float),
        "income": rng.normal(50_000, 10_000, 100).round(2),
        "score":  rng.uniform(0, 100, 100).round(1),
        "email":  [f"user{i}@example.com" for i in range(100)],
        "status": rng.choice(["active", "inactive"], 100).tolist(),
    })


@pytest.fixture
def dirty_df(clean_df: pd.DataFrame) -> pd.DataFrame:
    """
    DataFrame with injected quality issues used by multiple test modules.
    Issues present:
      - Missing values in age (3 rows) and income (2 rows)
      - Out-of-range value in income (row 0)
      - Invalid email format (rows 4, 5)
      - Invalid status (row 6)
      - 3 duplicate rows at the end
    """
    df = clean_df.copy()
    df.loc[[0, 1, 2], "age"] = float("nan")
    df.loc[[10, 11], "income"] = float("nan")
    df.loc[0, "income"] = 999_999.0          # outlier + out-of-range
    df.loc[[4, 5], "email"] = "not-an-email"
    df.loc[6, "status"] = "DELETED"
    df = pd.concat([df, df.iloc[:3]], ignore_index=True)
    return df
