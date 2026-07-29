from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from smartcoat.api.main import app

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PAGE_PATH = PROJECT_ROOT / "src" / "smartcoat" / "api" / "static" / "lab_observations.html"
PAGE_TEXT = PAGE_PATH.read_text(encoding="utf-8")


def test_lab_observation_page_is_served() -> None:
    response = TestClient(app).get("/lab-observations")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert response.headers["cache-control"] == "no-store"
    assert "SmartCoat Lab Observations" in response.text
    assert "id='lab-observation-form'" in response.text


def test_page_contains_exact_required_controls() -> None:
    required_ids = (
        "connection-section",
        "organization-id",
        "connection-message",
        "create-section",
        "lab-observation-form",
        "project-id",
        "project-name",
        "title",
        "observation",
        "source-reference",
        "observed-at",
        "actor-id",
        "actor-role",
        "submit-observation",
        "form-message",
        "list-section",
        "refresh-observations",
        "previous-page",
        "next-page",
        "page-status",
        "observations-table",
        "observations-body",
        "empty-state",
        "list-message",
    )

    for element_id in required_ids:
        assert f"id='{element_id}'" in PAGE_TEXT

    assert "value='smartcoat-pilot'" in PAGE_TEXT
    assert "/api/v2/lab-observations" in PAGE_TEXT
    assert "/api/v2/lab-observations?limit=" in PAGE_TEXT
    assert "X-SmartCoat-Organization-ID" in PAGE_TEXT
    assert "const pageLimit = 20;" in PAGE_TEXT


def test_page_has_no_external_or_framework_dependencies() -> None:
    page_lower = PAGE_TEXT.lower()
    forbidden_terms = (
        "react",
        "vue",
        "angular",
        "svelte",
        "jquery",
        "bootstrap",
        "tailwind",
        "vite",
        "webpack",
        "npm",
    )

    assert "<script src=" not in page_lower
    assert "<link" not in page_lower
    assert "http://" not in page_lower
    assert "https://" not in page_lower
    for term in forbidden_terms:
        assert term not in page_lower


def test_page_uses_safe_dom_rendering() -> None:
    assert "textContent" in PAGE_TEXT
    assert "replaceChildren" in PAGE_TEXT
    assert "innerHTML" not in PAGE_TEXT
    assert "insertAdjacentHTML" not in PAGE_TEXT
    assert "document.write" not in PAGE_TEXT
    assert "eval(" not in PAGE_TEXT
    assert "localStorage" not in PAGE_TEXT
    assert "sessionStorage" not in PAGE_TEXT


def test_ui_registration_preserves_v2_import_isolation() -> None:
    script = """
import fastapi.testclient
import sys
from smartcoat.api.main import app
assert "smartcoat.domain.knowledge_objects_v2" not in sys.modules
response = __import__("fastapi").testclient.TestClient(app).get("/lab-observations")
assert response.status_code == 200
schema = app.openapi()
assert "smartcoat.domain.knowledge_objects_v2" not in sys.modules
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=PROJECT_ROOT,
        env={**os.environ, "PYTHONPATH": str(PROJECT_ROOT / "src")},
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr


def test_ui_route_is_not_added_to_openapi() -> None:
    paths = app.openapi()["paths"]

    assert "/lab-observations" not in paths
    assert "/knowledge" in paths
    assert "/events" in paths
    assert "/decisions" in paths
    assert set(paths["/api/v2/lab-observations"]) == {"get", "post"}
    assert set(paths["/api/v2/lab-observations/{object_id}"]) == {"get"}
