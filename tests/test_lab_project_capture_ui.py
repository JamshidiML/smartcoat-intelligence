from __future__ import annotations

import re
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from smartcoat.api.routes import lab_project_capture_ui

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PAGE_PATH = PROJECT_ROOT / "src" / "smartcoat" / "api" / "static" / "lab_project_capture.html"
PAGE_TEXT = PAGE_PATH.read_text(encoding="utf-8")


def _temporary_client() -> TestClient:
    app = FastAPI()
    app.include_router(lab_project_capture_ui.router)
    return TestClient(app)


def test_lab_project_capture_page_is_served_from_temporary_app() -> None:
    client = _temporary_client()

    response = client.get("/lab-project-capture")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert response.headers["cache-control"] == "no-store"
    assert "SmartCoat Project Intake" in response.text
    assert "Laboratory project intake" in response.text
    assert "/lab-project-capture" not in client.app.openapi()["paths"]


def test_page_route_reports_missing_static_asset(
    monkeypatch: object,
    tmp_path: Path,
) -> None:
    missing_page = tmp_path / "missing.html"
    monkeypatch.setattr(lab_project_capture_ui, "STATIC_PAGE", missing_page)  # type: ignore[attr-defined]

    response = _temporary_client().get("/lab-project-capture")

    assert response.status_code == 500
    assert response.json() == {"detail": "Lab project capture page is unavailable"}


def test_page_contains_workspace_voice_review_and_save_controls() -> None:
    required_ids = (
        "workspace-section",
        "organization-id",
        "actor-id",
        "actor-role",
        "source-language",
        "capture-section",
        "start-recording",
        "stop-recording",
        "discard-recording",
        "recording-duration",
        "audio-playback",
        "process-audio",
        "transcript",
        "extract-text",
        "reextract-text",
        "review-section",
        "candidate-form",
        "candidate-sections",
        "completeness-score",
        "critical-missing-fields",
        "recommended-questions",
        "evidence-files",
        "evidence-list",
        "human-confirmed",
        "save-candidate",
        "created-object-id",
        "created-lifecycle",
        "recent-captures",
        "recent-captures-body",
    )

    for element_id in required_ids:
        if element_id == "critical-missing-fields":
            assert "Critical missing fields" in PAGE_TEXT
        else:
            assert f"id='{element_id}'" in PAGE_TEXT

    assert "value='smartcoat-startup'" in PAGE_TEXT
    assert "I reviewed the transcript" in PAGE_TEXT
    assert "Save confirmed draft" in PAGE_TEXT


def test_page_exposes_every_required_editable_review_section() -> None:
    required_titles = (
        "Project and customer",
        "Customer request",
        "Success criteria",
        "Substrate and reason selected",
        "Materials and formulation",
        "Experimental approaches",
        "Process parameters",
        "Tests and evaluations",
        "Samples, archive, shipment and follow-up",
        "Customer feedback",
        "Production feasibility",
        "Price optimization",
        "Reuse potential",
        "Innovation potential",
        "Business value and unresolved questions",
    )

    for title in required_titles:
        assert title in PAGE_TEXT

    for explicit_state in (
        '"unknown", "Unknown"',
        '"not_measured", "Not measured"',
        '"not_applicable", "Not applicable"',
        '"conflicting", "Conflicting"',
        '"missing", "Missing"',
    ):
        assert explicit_state in PAGE_TEXT

    assert 'item.outcome === "failed"' in PAGE_TEXT
    assert "item.follow_up_status" in PAGE_TEXT
    assert "card.dataset.attention = String(needsAttention)" in PAGE_TEXT


def test_page_uses_media_recorder_capability_detection_and_review() -> None:
    assert "navigator.mediaDevices.getUserMedia" in PAGE_TEXT
    assert "new MediaRecorder" in PAGE_TEXT
    assert "MediaRecorder.isTypeSupported" in PAGE_TEXT
    assert '"audio/webm;codecs=opus"' in PAGE_TEXT
    assert '"audio/webm"' in PAGE_TEXT
    assert '"audio/mp4"' in PAGE_TEXT
    assert "URL.createObjectURL" in PAGE_TEXT
    assert "URL.revokeObjectURL" in PAGE_TEXT
    assert "playback.src = audioUrl" in PAGE_TEXT
    assert "discardRecording" in PAGE_TEXT
    assert 'mediaRecorder.state === "recording"' in PAGE_TEXT
    assert 'getElement("process-audio").disabled = isRecording || !audioBlob' in PAGE_TEXT
    assert "NotAllowedError" in PAGE_TEXT
    assert "This browser does not support microphone recording." in PAGE_TEXT


def test_page_integrates_extract_reextract_save_and_recent_capture_endpoints() -> None:
    assert 'extractText: "/api/v2/lab-capture/extract-text"' in PAGE_TEXT
    assert 'processAudio: "/api/v2/lab-capture/process-audio"' in PAGE_TEXT
    assert 'captures: "/api/v2/lab-project-captures"' in PAGE_TEXT
    assert "transcript: extractionText(transcript, useAnswers)" in PAGE_TEXT
    assert "Follow-up answers supplied by the human reviewer:" in PAGE_TEXT
    assert "project_hints: currentProjectHints()" in PAGE_TEXT
    assert "organization_id: organization" not in PAGE_TEXT
    assert "candidate.human_confirmed = true" in PAGE_TEXT
    assert "candidate.human_confirmed_by = actorId()" in PAGE_TEXT
    assert "candidate.human_confirmed_at = new Date().toISOString()" in PAGE_TEXT
    assert 'getElement("human-confirmed").checked = false' in PAGE_TEXT
    assert "invalidateConfirmation()" in PAGE_TEXT
    assert "candidateSaved = true" in PAGE_TEXT
    assert 'method: "POST"' in PAGE_TEXT
    assert 'method: "GET"' in PAGE_TEXT
    assert '"X-SmartCoat-Organization-ID"' in PAGE_TEXT


def test_human_confirmation_gates_canonical_save() -> None:
    assert 'const confirmed = getElement("human-confirmed").checked;' in PAGE_TEXT
    assert "const hasCandidate = Boolean(candidate);" in PAGE_TEXT
    assert 'getElement("save-candidate").disabled = !(' in PAGE_TEXT
    assert 'if (!candidate || !getElement("human-confirmed").checked)' in PAGE_TEXT
    assert "Human confirmation and an actor ID are required." in PAGE_TEXT
    assert "confirmed && hasCandidate && hasActor && !candidateSaved" in PAGE_TEXT


def test_page_has_evidence_upload_and_integrity_hooks() -> None:
    assert "accept='.xlsx,.pdf,image/png,image/jpeg,image/webp'" in PAGE_TEXT
    assert 'assets: "/api/v2/lab-capture/assets"' in PAGE_TEXT
    assert 'crypto.subtle.digest("SHA-256"' in PAGE_TEXT
    assert '"X-SmartCoat-Filename"' in PAGE_TEXT
    assert "source_reference" in PAGE_TEXT
    assert "descriptor.sha256 !== browserHash" in PAGE_TEXT
    assert "Files are hashed in the browser" in PAGE_TEXT


def test_missing_fields_and_questions_are_rendered_with_safe_dom_apis() -> None:
    assert 'replaceList("missing-fields"' in PAGE_TEXT or '"missing-fields",' in PAGE_TEXT
    assert "renderQuestions(candidate.recommended_questions)" in PAGE_TEXT
    assert "followUpAnswers.set" in PAGE_TEXT
    assert "textContent" in PAGE_TEXT
    assert "replaceChildren" in PAGE_TEXT
    assert "innerHTML" not in PAGE_TEXT
    assert "insertAdjacentHTML" not in PAGE_TEXT
    assert "document.write" not in PAGE_TEXT
    assert "eval(" not in PAGE_TEXT


def test_page_uses_no_external_assets_or_browser_persistence() -> None:
    page_lower = PAGE_TEXT.lower()

    assert re.search(r"<script(?![^>]*\bsrc=)", page_lower)
    assert not re.search(r"<script[^>]*\bsrc=", page_lower)
    assert not re.search(r"<link[^>]*\bhref=", page_lower)
    assert "http://" not in page_lower
    assert "https://" not in page_lower
    assert "localstorage" not in page_lower
    assert "sessionstorage" not in page_lower
    assert "indexeddb" not in page_lower


def test_page_has_mobile_viewport_and_accessibility_contracts() -> None:
    assert "<meta name='viewport' content='width=device-width, initial-scale=1'>" in PAGE_TEXT
    assert "@media (max-width: 720px)" in PAGE_TEXT
    assert "min-width: 320px" in PAGE_TEXT
    assert "aria-live='polite'" in PAGE_TEXT
    assert "aria-labelledby=" in PAGE_TEXT
    assert "aria-label='Capture progress'" in PAGE_TEXT
    assert "<label for='organization-id'>" in PAGE_TEXT
    assert "<label for='actor-id'>" in PAGE_TEXT
    assert "<label for='evidence-files'>" in PAGE_TEXT
