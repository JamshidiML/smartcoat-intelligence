from __future__ import annotations

import inspect
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from smartcoat.api.routes import lab_capture_ai
from smartcoat.api.routes.lab_capture_ai import (
    LocalAIPreflightResponse,
    ReadinessCheck,
    get_structured_extraction_provider,
    get_transcription_provider,
    router,
)
from smartcoat.core.config import Settings
from smartcoat.domain.lab_project_capture import (
    CaptureSourceKind,
    LabProjectCaptureCandidate,
    ProjectIdentity,
)
from smartcoat.services.lab_project_extraction import (
    DeterministicFakeExtractionProvider,
    StructuredExtractionOutputError,
    StructuredExtractionProviderUnavailableError,
    StructuredExtractionTimeoutError,
)
from smartcoat.services.voice_transcription import (
    DeterministicFakeTranscriptionProvider,
    TranscriptionProviderUnavailableError,
    TranscriptionResult,
)

NOW = datetime(2026, 8, 6, 8, 0, tzinfo=UTC)


def _candidate(*, human_confirmed: bool = False) -> LabProjectCaptureCandidate:
    return LabProjectCaptureCandidate(
        capture_session_id="72d399c6-5fdf-4897-a4ab-126739220028",
        source_kind=CaptureSourceKind.TEXT,
        source_language="en",
        transcript="Synthetic local transcript.",
        extraction_model="deterministic-fake",
        extraction_started_at=NOW,
        extraction_completed_at=NOW,
        project=ProjectIdentity(
            project_id="P-SYN-001",
            project_name="Synthetic project",
            request_summary="Generalized synthetic intake.",
        ),
        human_confirmed=human_confirmed,
        human_confirmed_by="synthetic-reviewer" if human_confirmed else None,
        human_confirmed_at=NOW if human_confirmed else None,
    )


def _transcription() -> TranscriptionResult:
    return TranscriptionResult(
        transcript="Synthetic local transcript.",
        detected_language="en",
        duration_seconds=1.25,
        provider="deterministic-fake",
        model="fake-speech-model",
    )


def _client(
    extraction_provider: DeterministicFakeExtractionProvider,
    transcription_provider: DeterministicFakeTranscriptionProvider | None = None,
) -> TestClient:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_structured_extraction_provider] = lambda: extraction_provider
    if transcription_provider is not None:
        app.dependency_overrides[get_transcription_provider] = lambda: transcription_provider
    return TestClient(app)


def _audio_headers(
    *,
    media_type: str = "audio/wav",
    filename: str = "capture.wav",
    organization_id: str = "smartcoat-startup",
) -> dict[str, str]:
    return {
        "Content-Type": media_type,
        "X-SmartCoat-Filename": filename,
        "X-SmartCoat-Organization-ID": organization_id,
    }


def _text_headers(organization_id: str = "smartcoat-startup") -> dict[str, str]:
    return {"X-SmartCoat-Organization-ID": organization_id}


def test_successful_text_extraction_returns_unconfirmed_candidate() -> None:
    provider = DeterministicFakeExtractionProvider(_candidate())
    client = _client(provider)

    response = client.post(
        "/api/v2/lab-capture/extract-text",
        headers=_text_headers(),
        json={
            "free_text": "Synthetic local transcript.",
            "project_hints": {"project_id": "P-SYN-001"},
            "actor_metadata": {
                "actor_id": "synthetic-engineer",
                "actor_role": "lab_engineer",
            },
            "source_language": "en",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["candidate"]["human_confirmed"] is False
    assert body["candidate"]["source_kind"] == "text"
    assert body["completeness_score"] == body["candidate"]["completeness_score"]
    assert body["missing_fields"]
    assert body["follow_up_questions"]
    assert body["transcription"] is None
    assert provider.calls[0].actor_metadata is not None
    assert provider.calls[0].actor_metadata.actor_id == "synthetic-engineer"


def test_text_extraction_requires_exactly_one_text_source() -> None:
    provider = DeterministicFakeExtractionProvider(_candidate())
    client = _client(provider)
    actor = {"actor_id": "synthetic-engineer", "actor_role": "lab_engineer"}

    missing = client.post(
        "/api/v2/lab-capture/extract-text",
        headers=_text_headers(),
        json={"actor_metadata": actor},
    )
    duplicate = client.post(
        "/api/v2/lab-capture/extract-text",
        headers=_text_headers(),
        json={
            "transcript": "Synthetic transcript.",
            "free_text": "Synthetic free text.",
            "actor_metadata": actor,
        },
    )

    assert missing.status_code == 422
    assert duplicate.status_code == 422
    assert provider.calls == []


def test_successful_audio_pipeline_uses_fakes_and_sanitizes_filename(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    extraction = DeterministicFakeExtractionProvider(_candidate())
    transcription = DeterministicFakeTranscriptionProvider(_transcription())
    monkeypatch.setattr(
        lab_capture_ai,
        "get_settings",
        lambda: Settings(asset_root=tmp_path, max_upload_bytes=1024),
    )
    client = _client(extraction, transcription)

    response = client.post(
        "/api/v2/lab-capture/process-audio",
        content=b"synthetic-audio",
        headers=_audio_headers(filename="../../capture test.wav"),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["candidate"]["source_kind"] == "voice"
    assert body["candidate"]["human_confirmed"] is False
    assert body["transcription"]["transcript"] == "Synthetic local transcript."
    assert transcription.calls == [(b"synthetic-audio", "capture_test.wav", "audio/wav")]
    assert extraction.calls[0].source_kind is CaptureSourceKind.VOICE
    assert extraction.calls[0].transcript == "Synthetic local transcript."


def test_audio_rejects_unsupported_media_oversize_empty_and_wrong_organization(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    extraction = DeterministicFakeExtractionProvider(_candidate())
    transcription = DeterministicFakeTranscriptionProvider(_transcription())
    monkeypatch.setattr(
        lab_capture_ai,
        "get_settings",
        lambda: Settings(asset_root=tmp_path, max_upload_bytes=4),
    )
    client = _client(extraction, transcription)

    unsupported = client.post(
        "/api/v2/lab-capture/process-audio",
        content=b"1234",
        headers=_audio_headers(media_type="application/octet-stream"),
    )
    oversized = client.post(
        "/api/v2/lab-capture/process-audio",
        content=b"12345",
        headers=_audio_headers(),
    )
    empty = client.post(
        "/api/v2/lab-capture/process-audio",
        content=b"",
        headers=_audio_headers(),
    )
    wrong_organization = client.post(
        "/api/v2/lab-capture/process-audio",
        content=b"1234",
        headers=_audio_headers(organization_id="other-organization"),
    )

    assert unsupported.status_code == 415
    assert oversized.status_code == 413
    assert empty.status_code == 422
    assert wrong_organization.status_code == 403
    assert transcription.calls == []
    assert extraction.calls == []


@pytest.mark.parametrize(
    ("error", "expected_status"),
    [
        (StructuredExtractionTimeoutError("timeout"), 504),
        (StructuredExtractionProviderUnavailableError("unavailable"), 503),
        (StructuredExtractionOutputError("invalid"), 502),
    ],
)
def test_extraction_provider_failures_map_to_safe_api_errors(
    error: Exception,
    expected_status: int,
) -> None:
    provider = DeterministicFakeExtractionProvider(error=error)  # type: ignore[arg-type]
    client = _client(provider)

    response = client.post(
        "/api/v2/lab-capture/extract-text",
        headers=_text_headers(),
        json={
            "transcript": "Synthetic transcript.",
            "actor_metadata": {
                "actor_id": "synthetic-engineer",
                "actor_role": "lab_engineer",
            },
        },
    )

    assert response.status_code == expected_status
    assert "synthetic" not in response.text


def test_voice_reextraction_preserves_source_kind_and_original_transcript() -> None:
    provider = DeterministicFakeExtractionProvider(_candidate())
    client = _client(provider)
    original = "Immutable synthetic voice transcript."
    supplement = "Question: What was missing?\nAnswer: Synthetic review answer."

    response = client.post(
        "/api/v2/lab-capture/extract-text",
        headers=_text_headers(),
        json={
            "transcript": original,
            "source_kind": "voice",
            "supplemental_context": supplement,
            "actor_metadata": {
                "actor_id": "synthetic-engineer",
                "actor_role": "lab_engineer",
            },
        },
    )

    assert response.status_code == 200
    assert response.json()["candidate"]["source_kind"] == "voice"
    assert response.json()["candidate"]["transcript"] == original
    assert provider.calls[0].supplemental_context == supplement
    assert supplement not in response.json()["candidate"]["transcript"]


def test_text_extraction_rejects_wrong_pilot_organization() -> None:
    provider = DeterministicFakeExtractionProvider(_candidate())
    response = _client(provider).post(
        "/api/v2/lab-capture/extract-text",
        headers=_text_headers("other-organization"),
        json={
            "transcript": "Synthetic transcript.",
            "actor_metadata": {
                "actor_id": "synthetic-engineer",
                "actor_role": "lab_engineer",
            },
        },
    )

    assert response.status_code == 403
    assert provider.calls == []


def test_unavailable_transcription_maps_to_503(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    extraction = DeterministicFakeExtractionProvider(_candidate())
    transcription = DeterministicFakeTranscriptionProvider(
        _transcription(),
        error=TranscriptionProviderUnavailableError("synthetic details"),
    )
    monkeypatch.setattr(
        lab_capture_ai,
        "get_settings",
        lambda: Settings(asset_root=tmp_path, max_upload_bytes=1024),
    )
    client = _client(extraction, transcription)

    response = client.post(
        "/api/v2/lab-capture/process-audio",
        content=b"audio",
        headers=_audio_headers(),
    )

    assert response.status_code == 503
    assert "synthetic details" not in response.text
    assert extraction.calls == []


def test_preflight_endpoint_returns_all_local_readiness_checks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    check = ReadinessCheck(ready=True, detail="Synthetic readiness check passed")
    expected = LocalAIPreflightResponse(
        ready=True,
        mlx_whisper_import=check,
        whisper_model=check,
        ollama_reachability=check,
        ollama_model=check,
        asset_directory=check,
    )
    monkeypatch.setattr(lab_capture_ai, "build_preflight_response", lambda: expected)
    client = _client(DeterministicFakeExtractionProvider(_candidate()))

    response = client.get("/api/v2/lab-capture/preflight")

    assert response.status_code == 200
    assert response.json() == expected.model_dump(mode="json")


def test_ai_route_has_no_canonical_persistence_path() -> None:
    source = inspect.getsource(lab_capture_ai)

    assert "smartcoat.storage" not in source
    assert "KnowledgeAuditService" not in source
    assert "KnowledgeObjectV2Repository" not in source
