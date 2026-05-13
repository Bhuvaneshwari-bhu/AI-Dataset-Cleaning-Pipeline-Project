"""
test_loader.py
Tests for loader.py — CSV, JSON, Excel loading and get_basic_info.
"""

from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from loader import get_basic_info, load_csv, load_excel, load_json

# ══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def csv_file(tmp_path: Path) -> Path:
    df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    path = tmp_path / "test.csv"
    df.to_csv(path, index=False)
    return path


@pytest.fixture
def json_file(tmp_path: Path) -> Path:
    df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    path = tmp_path / "test.json"
    df.to_json(path, orient="records")
    return path


# ══════════════════════════════════════════════════════════════════════════════
# load_csv
# ══════════════════════════════════════════════════════════════════════════════


def test_load_csv_returns_dataframe(csv_file: Path) -> None:
    df = load_csv(csv_file)
    assert isinstance(df, pd.DataFrame)
    assert df.shape == (3, 2)


def test_load_csv_accepts_str_path(csv_file: Path) -> None:
    df = load_csv(str(csv_file))
    assert isinstance(df, pd.DataFrame)


def test_load_csv_file_not_found(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_csv(tmp_path / "missing.csv")


def test_load_csv_passes_kwargs(csv_file: Path) -> None:
    df = load_csv(csv_file, nrows=2)
    assert len(df) == 2


# ══════════════════════════════════════════════════════════════════════════════
# load_json
# ══════════════════════════════════════════════════════════════════════════════


def test_load_json_returns_dataframe(json_file: Path) -> None:
    df = load_json(json_file)
    assert isinstance(df, pd.DataFrame)
    assert df.shape == (3, 2)


def test_load_json_file_not_found(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_json(tmp_path / "missing.json")


# ══════════════════════════════════════════════════════════════════════════════
# load_excel
# ══════════════════════════════════════════════════════════════════════════════


def test_load_excel_file_not_found(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_excel(tmp_path / "missing.xlsx")


def test_load_excel_success(tmp_path: Path) -> None:
    pytest.importorskip("openpyxl")
    df_expected = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    path = tmp_path / "test.xlsx"
    df_expected.to_excel(path, index=False)
    df = load_excel(path)
    assert df.shape == (2, 2)


def test_load_excel_success_mocked(tmp_path: Path) -> None:
    """Covers lines 33-35: read_excel called and result returned (no openpyxl needed)."""
    dummy_path = tmp_path / "test.xlsx"
    dummy_path.write_bytes(b"dummy")  # file must exist to pass path.exists() guard

    expected = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    with patch("loader.pd.read_excel", return_value=expected) as mock_read:
        df = load_excel(dummy_path)

    mock_read.assert_called_once_with(dummy_path, sheet_name=0)
    assert df.shape == (2, 2)


# ══════════════════════════════════════════════════════════════════════════════
# get_basic_info
# ══════════════════════════════════════════════════════════════════════════════


def test_get_basic_info_has_expected_keys(csv_file: Path) -> None:
    df = load_csv(csv_file)
    info = get_basic_info(df)
    assert set(info.keys()) == {"rows", "columns", "column_names", "dtypes", "memory_usage_kb"}


def test_get_basic_info_correct_values(csv_file: Path) -> None:
    df = load_csv(csv_file)
    info = get_basic_info(df)
    assert info["rows"] == 3
    assert info["columns"] == 2
    assert info["column_names"] == ["a", "b"]
    assert isinstance(info["memory_usage_kb"], float)
    assert info["memory_usage_kb"] > 0
