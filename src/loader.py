"""
loader.py
Responsible for reading data from various file formats into a pandas DataFrame.
Keeping I/O logic here means the rest of the pipeline never has to care about
where the data came from.
"""

from pathlib import Path
from typing import Any

import pandas as pd

from logger import get_logger

logger = get_logger("loader")


def load_csv(filepath: str | Path, **kwargs: Any) -> pd.DataFrame:
    """Load a CSV file and return a DataFrame."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")
    df = pd.read_csv(path, **kwargs)
    logger.info("Loaded %s rows × %s columns from '%s'", len(df), len(df.columns), path.name)
    return df


def load_excel(filepath: str | Path, sheet_name: int | str = 0, **kwargs: Any) -> pd.DataFrame:
    """Load an Excel file and return a DataFrame."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")
    df = pd.read_excel(path, sheet_name=sheet_name, **kwargs)
    logger.info("Loaded %s rows × %s columns from '%s'", len(df), len(df.columns), path.name)
    return df


def load_json(filepath: str | Path, **kwargs: Any) -> pd.DataFrame:
    """Load a JSON file and return a DataFrame."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")
    df = pd.read_json(path, **kwargs)
    logger.info("Loaded %s rows × %s columns from '%s'", len(df), len(df.columns), path.name)
    return df


def get_basic_info(df: pd.DataFrame) -> dict[str, Any]:
    """Return a dict of basic dataset metadata."""
    return {
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": list(df.columns),
        "dtypes": df.dtypes.astype(str).to_dict(),
        "memory_usage_kb": round(df.memory_usage(deep=True).sum() / 1024, 2),
    }
