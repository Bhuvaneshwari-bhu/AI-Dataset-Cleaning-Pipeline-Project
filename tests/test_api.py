"""
test_api.py
Integration tests for the FastAPI backend using TestClient.

Each test group covers one endpoint.  The `client` fixture overrides the
`get_storage` dependency to use an isolated temporary directory, so tests
never touch the real storage/ tree and run independently of one another.
"""

from __future__ import annotations

import io
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from api.services.storage import StorageManager, get_storage

# main_api bootstraps sys.path so all pipeline imports resolve
from main_api import app

# ══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def test_storage(tmp_path: Path) -> StorageManager:
    """Isolated StorageManager backed by a pytest tmp_path."""
    manager = StorageManager(root=tmp_path / "storage")
    manager.ensure_dirs()
    return manager


@pytest.fixture
def client(test_storage: StorageManager) -> TestClient:  # type: ignore[misc]
    """TestClient with storage dependency overridden to use the test storage."""
    app.dependency_overrides[get_storage] = lambda: test_storage
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def csv_bytes() -> bytes:
    """Minimal valid CSV for upload tests."""
    return (
        b"id,age,income,label\n"
        b"1,25,50000.0,A\n"
        b"2,30,60000.0,B\n"
        b"3,35,70000.0,A\n"
        b"4,40,80000.0,B\n"
        b"5,45,90000.0,A\n"
    )


@pytest.fixture
def upload_id(client: TestClient, csv_bytes: bytes) -> str:
    """Upload a file and return its upload_id for downstream fixtures."""
    resp = client.post(
        "/upload",
        files={"file": ("dataset.csv", io.BytesIO(csv_bytes), "text/csv")},
    )
    assert resp.status_code == 201
    return resp.json()["upload_id"]


@pytest.fixture
def analyzed_id(client: TestClient, upload_id: str) -> str:
    """Upload + analyze; return upload_id for report/download tests."""
    resp = client.post(f"/analyze/{upload_id}", json={})
    assert resp.status_code == 200
    return upload_id


# ══════════════════════════════════════════════════════════════════════════════
# GET /health
# ══════════════════════════════════════════════════════════════════════════════


def test_health_returns_200(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200


def test_health_response_shape(client: TestClient) -> None:
    data = client.get("/health").json()
    assert data["status"] == "ok"
    assert "version" in data
    assert isinstance(data["pipeline_modules"], list)
    assert len(data["pipeline_modules"]) > 0


# ══════════════════════════════════════════════════════════════════════════════
# POST /upload
# ══════════════════════════════════════════════════════════════════════════════


def test_upload_csv_returns_201(client: TestClient, csv_bytes: bytes) -> None:
    resp = client.post(
        "/upload",
        files={"file": ("data.csv", io.BytesIO(csv_bytes), "text/csv")},
    )
    assert resp.status_code == 201


def test_upload_response_contains_upload_id(client: TestClient, csv_bytes: bytes) -> None:
    data = client.post(
        "/upload",
        files={"file": ("data.csv", io.BytesIO(csv_bytes), "text/csv")},
    ).json()
    assert "upload_id" in data
    assert len(data["upload_id"]) == 36  # UUID4


def test_upload_response_contains_filename_and_size(client: TestClient, csv_bytes: bytes) -> None:
    data = client.post(
        "/upload",
        files={"file": ("my_data.csv", io.BytesIO(csv_bytes), "text/csv")},
    ).json()
    assert data["filename"] == "my_data.csv"
    assert data["size_bytes"] == len(csv_bytes)


def test_upload_stores_file_on_disk(
    client: TestClient, csv_bytes: bytes, test_storage: StorageManager
) -> None:
    uid = client.post(
        "/upload",
        files={"file": ("data.csv", io.BytesIO(csv_bytes), "text/csv")},
    ).json()["upload_id"]
    assert test_storage.upload_path(uid).exists()


def test_upload_non_csv_rejected(client: TestClient) -> None:
    resp = client.post(
        "/upload",
        files={"file": ("report.txt", io.BytesIO(b"not,csv"), "text/plain")},
    )
    assert resp.status_code == 422


def test_upload_empty_file_rejected(client: TestClient) -> None:
    resp = client.post(
        "/upload",
        files={"file": ("empty.csv", io.BytesIO(b""), "text/csv")},
    )
    assert resp.status_code == 422


def test_upload_each_call_gets_unique_id(client: TestClient, csv_bytes: bytes) -> None:
    ids = {
        client.post(
            "/upload",
            files={"file": ("data.csv", io.BytesIO(csv_bytes), "text/csv")},
        ).json()["upload_id"]
        for _ in range(3)
    }
    assert len(ids) == 3  # all distinct


# ══════════════════════════════════════════════════════════════════════════════
# POST /analyze/{upload_id}
# ══════════════════════════════════════════════════════════════════════════════


def test_analyze_unknown_id_returns_404(client: TestClient) -> None:
    resp = client.post("/analyze/does-not-exist", json={})
    assert resp.status_code == 404


def test_analyze_returns_200(client: TestClient, upload_id: str) -> None:
    resp = client.post(f"/analyze/{upload_id}", json={})
    assert resp.status_code == 200


def test_analyze_response_has_required_fields(client: TestClient, upload_id: str) -> None:
    data = client.post(f"/analyze/{upload_id}", json={}).json()
    required = {
        "upload_id",
        "quality_score",
        "passed",
        "row_count_raw",
        "row_count_clean",
        "column_count",
        "duplicate_count",
        "missing_summary",
        "type_issues",
        "schema_violations",
        "format_violations",
        "out_of_range",
        "profiles",
        "total_outliers",
        "outlier_summary",
        "clean_log",
        "report_url",
        "download_url",
    }
    assert required.issubset(data.keys())


def test_analyze_upload_id_echoed(client: TestClient, upload_id: str) -> None:
    data = client.post(f"/analyze/{upload_id}", json={}).json()
    assert data["upload_id"] == upload_id


def test_analyze_row_counts_correct(client: TestClient, upload_id: str) -> None:
    data = client.post(f"/analyze/{upload_id}", json={}).json()
    assert data["row_count_raw"] == 5
    assert data["column_count"] == 4


def test_analyze_quality_score_in_range(client: TestClient, upload_id: str) -> None:
    data = client.post(f"/analyze/{upload_id}", json={}).json()
    assert 0.0 <= data["quality_score"] <= 100.0


def test_analyze_urls_point_to_correct_endpoints(client: TestClient, upload_id: str) -> None:
    data = client.post(f"/analyze/{upload_id}", json={}).json()
    assert data["report_url"] == f"/report/{upload_id}"
    assert data["download_url"] == f"/download-cleaned/{upload_id}"


def test_analyze_profiles_contain_all_columns(client: TestClient, upload_id: str) -> None:
    data = client.post(f"/analyze/{upload_id}", json={}).json()
    assert set(data["profiles"].keys()) == {"id", "age", "income", "label"}


def test_analyze_no_request_body_uses_defaults(client: TestClient, upload_id: str) -> None:
    # Sending no JSON body should still succeed (all options have defaults)
    resp = client.post(f"/analyze/{upload_id}")
    assert resp.status_code == 200


def test_analyze_zscore_method(client: TestClient, upload_id: str) -> None:
    data = client.post(
        f"/analyze/{upload_id}",
        json={"anomaly_method": "zscore", "anomaly_threshold": 2.5},
    ).json()
    assert data["upload_id"] == upload_id


def test_analyze_mean_fill_strategy(client: TestClient, upload_id: str) -> None:
    data = client.post(
        f"/analyze/{upload_id}",
        json={"fill_strategy": "mean"},
    ).json()
    assert data["upload_id"] == upload_id


def test_analyze_creates_cleaned_and_report_files(
    client: TestClient, upload_id: str, test_storage: StorageManager
) -> None:
    client.post(f"/analyze/{upload_id}", json={})
    assert test_storage.cleaned_exists(upload_id)
    assert test_storage.report_exists(upload_id)


def test_analyze_cleaned_csv_is_valid(
    client: TestClient, upload_id: str, test_storage: StorageManager
) -> None:
    client.post(f"/analyze/{upload_id}", json={})
    df = pd.read_csv(test_storage.cleaned_path(upload_id))
    assert len(df) == 5
    assert set(df.columns) == {"id", "age", "income", "label"}


def test_analyze_with_missing_values(client: TestClient, test_storage: StorageManager) -> None:
    csv = b"id,age,income\n1,,50000\n2,30,\n3,35,70000\n"
    uid = client.post(
        "/upload",
        files={"file": ("missing.csv", io.BytesIO(csv), "text/csv")},
    ).json()["upload_id"]

    data = client.post(f"/analyze/{uid}", json={}).json()
    assert len(data["missing_summary"]) > 0


def test_analyze_with_duplicate_rows(client: TestClient, test_storage: StorageManager) -> None:
    csv = b"id,age\n1,25\n1,25\n2,30\n"
    uid = client.post(
        "/upload",
        files={"file": ("dupes.csv", io.BytesIO(csv), "text/csv")},
    ).json()["upload_id"]

    data = client.post(f"/analyze/{uid}", json={}).json()
    assert data["duplicate_count"] >= 1


# ══════════════════════════════════════════════════════════════════════════════
# GET /report/{upload_id}
# ══════════════════════════════════════════════════════════════════════════════


def test_report_unknown_id_returns_404(client: TestClient) -> None:
    assert client.get("/report/unknown-id").status_code == 404


def test_report_before_analyze_returns_404(client: TestClient, upload_id: str) -> None:
    assert client.get(f"/report/{upload_id}").status_code == 404


def test_report_after_analyze_returns_200(client: TestClient, analyzed_id: str) -> None:
    assert client.get(f"/report/{analyzed_id}").status_code == 200


def test_report_content_type_is_html(client: TestClient, analyzed_id: str) -> None:
    resp = client.get(f"/report/{analyzed_id}")
    assert "text/html" in resp.headers["content-type"]


def test_report_html_contains_expected_sections(client: TestClient, analyzed_id: str) -> None:
    html = client.get(f"/report/{analyzed_id}").text
    assert "<html" in html
    assert "Quality Score" in html
    assert "Dataset Overview" in html
    assert "Column Profiles" in html


def test_report_html_images_rewritten_to_url_paths(client: TestClient, analyzed_id: str) -> None:
    html = client.get(f"/report/{analyzed_id}").text
    # Absolute filesystem paths must have been replaced with /files/ URL paths
    assert "/home/" not in html or 'src="/files/' in html


# ══════════════════════════════════════════════════════════════════════════════
# GET /download-cleaned/{upload_id}
# ══════════════════════════════════════════════════════════════════════════════


def test_download_unknown_id_returns_404(client: TestClient) -> None:
    assert client.get("/download-cleaned/unknown-id").status_code == 404


def test_download_before_analyze_returns_404(client: TestClient, upload_id: str) -> None:
    assert client.get(f"/download-cleaned/{upload_id}").status_code == 404


def test_download_after_analyze_returns_200(client: TestClient, analyzed_id: str) -> None:
    assert client.get(f"/download-cleaned/{analyzed_id}").status_code == 200


def test_download_content_type_is_csv(client: TestClient, analyzed_id: str) -> None:
    resp = client.get(f"/download-cleaned/{analyzed_id}")
    assert "text/csv" in resp.headers["content-type"]


def test_download_content_is_valid_csv(client: TestClient, analyzed_id: str) -> None:
    resp = client.get(f"/download-cleaned/{analyzed_id}")
    import csv
    import io as _io

    reader = csv.reader(_io.StringIO(resp.text))
    rows = list(reader)
    assert len(rows) > 1  # header + at least one data row


def test_download_filename_header_contains_short_id(client: TestClient, analyzed_id: str) -> None:
    resp = client.get(f"/download-cleaned/{analyzed_id}")
    disposition = resp.headers.get("content-disposition", "")
    assert analyzed_id[:8] in disposition
