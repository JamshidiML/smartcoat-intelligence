from __future__ import annotations

import io
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from openpyxl import Workbook

from smartcoat.api.routes.lab_project_imports import (
    XLSX_MEDIA_TYPE,
    get_local_evidence_registry,
    router,
)
from smartcoat.services.local_evidence_registry import LocalEvidenceRegistry

PDF_CONTENT = b"%PDF-1.7\n% synthetic API evidence\n%%EOF\n"


def _xlsx_bytes() -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Projects"
    sheet.append(
        [
            "Project Number",
            "Project Name",
            "Customer",
            "Request",
            "Goal",
            "Approach",
            "Result",
            "Temperature",
            "Unknown Column",
        ]
    )
    sheet.append(
        [
            "P-SYN-API-01",
            "Synthetic API project",
            "Example Customer",
            "Synthetic request",
            "Synthetic success criterion",
            "Approach one",
            "successful",
            "210 degC",
            "preserve me",
        ]
    )
    stream = io.BytesIO()
    workbook.save(stream)
    workbook.close()
    return stream.getvalue()


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    app = FastAPI()
    app.include_router(router)
    registry = LocalEvidenceRegistry(tmp_path / "assets", max_upload_bytes=2 * 1024 * 1024)
    app.dependency_overrides[get_local_evidence_registry] = lambda: registry
    return TestClient(app)


def _headers(
    *, filename: str, media_type: str, organization: str = "synthetic-lab"
) -> dict[str, str]:
    return {
        "Content-Type": media_type,
        "X-SmartCoat-Filename": filename,
        "X-SmartCoat-Organization-ID": organization,
    }


def _contains_key(value: Any, key: str) -> bool:
    if isinstance(value, dict):
        return key in value or any(_contains_key(item, key) for item in value.values())
    if isinstance(value, list):
        return any(_contains_key(item, key) for item in value)
    return False


def test_raw_asset_endpoint_registers_pdf_and_hides_filesystem_path(client: TestClient) -> None:
    response = client.post(
        "/api/v2/lab-capture/assets",
        content=PDF_CONTENT,
        headers=_headers(filename="../../synthetic-report.pdf", media_type="application/pdf"),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["evidence_type"] == "pdf"
    assert body["original_filename"] == "../../synthetic-report.pdf"
    assert len(body["sha256"]) == 64
    assert body["source_reference"].startswith("smartcoat-asset://synthetic-lab/")
    assert body["duplicate"] is False
    assert not _contains_key(body, "path")

    duplicate = client.post(
        "/api/v2/lab-capture/assets",
        content=PDF_CONTENT,
        headers=_headers(filename="second-name.pdf", media_type="application/pdf"),
    )
    assert duplicate.status_code == 201
    assert duplicate.json()["duplicate"] is True
    assert duplicate.json()["evidence_id"] == body["evidence_id"]


def test_excel_import_returns_dry_run_candidates_and_no_canonical_write(client: TestClient) -> None:
    content = _xlsx_bytes()
    response = client.post(
        "/api/v2/lab-capture/import-excel",
        content=content,
        headers=_headers(filename="synthetic.xlsx", media_type=XLSX_MEDIA_TYPE),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["dry_run"] is True
    assert body["canonical_writes"] == 0
    assert body["organization_id"] == "synthetic-lab"
    assert body["sheet_names"] == ["Projects"]
    assert len(body["candidates"]) == 1
    candidate = body["candidates"][0]["candidate"]
    assert candidate["source_kind"] == "excel"
    assert candidate["human_confirmed"] is False
    assert candidate["project"]["project_id"] == "P-SYN-API-01"
    assert candidate["process_parameters"][0]["numeric_value"] == 210
    assert body["candidates"][0]["cell_provenance"][0]["cell_reference"] == "A2"
    assert body["candidates"][0]["unmapped_values"][0]["display_value"] == "preserve me"
    assert body["unmapped_columns"][0]["header"] == "Unknown Column"
    assert not _contains_key(body, "path")


def test_endpoints_require_headers_and_validate_media(client: TestClient) -> None:
    missing = client.post("/api/v2/lab-capture/assets", content=PDF_CONTENT)
    assert missing.status_code == 422

    unsupported = client.post(
        "/api/v2/lab-capture/assets",
        content=b"synthetic text",
        headers=_headers(filename="notes.txt", media_type="text/plain"),
    )
    assert unsupported.status_code == 415

    wrong_excel_media = client.post(
        "/api/v2/lab-capture/import-excel",
        content=_xlsx_bytes(),
        headers=_headers(filename="synthetic.xlsx", media_type="application/octet-stream"),
    )
    assert wrong_excel_media.status_code == 415

    invalid_xlsx = client.post(
        "/api/v2/lab-capture/import-excel",
        content=b"not an xlsx",
        headers=_headers(filename="invalid.xlsx", media_type=XLSX_MEDIA_TYPE),
    )
    assert invalid_xlsx.status_code == 422


def test_upload_limit_and_organization_validation_are_api_safe(tmp_path: Path) -> None:
    app = FastAPI()
    app.include_router(router)
    registry = LocalEvidenceRegistry(tmp_path / "assets", max_upload_bytes=16)
    app.dependency_overrides[get_local_evidence_registry] = lambda: registry
    client = TestClient(app)

    oversized = client.post(
        "/api/v2/lab-capture/assets",
        content=PDF_CONTENT,
        headers=_headers(filename="large.pdf", media_type="application/pdf"),
    )
    assert oversized.status_code == 413
    assert "/Users/" not in oversized.text

    unsafe_organization = client.post(
        "/api/v2/lab-capture/assets",
        content=b"%PDF-x",
        headers=_headers(
            filename="report.pdf",
            media_type="application/pdf",
            organization="../other",
        ),
    )
    assert unsafe_organization.status_code == 422
    assert "/Users/" not in unsafe_organization.text
