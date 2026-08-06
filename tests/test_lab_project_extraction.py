from __future__ import annotations

import json
from datetime import UTC, datetime
from types import TracebackType
from typing import Any

import pytest

from smartcoat.domain.lab_project_capture import (
    CaptureSourceKind,
    LabProjectCaptureCandidate,
    ProjectIdentity,
)
from smartcoat.services import lab_project_extraction
from smartcoat.services.lab_project_extraction import (
    SYSTEM_INSTRUCTIONS,
    ActorMetadata,
    DeterministicFakeExtractionProvider,
    ExtractionRequest,
    OllamaStructuredExtractionProvider,
    ProjectHints,
    StructuredExtractionConfigurationError,
    StructuredExtractionOutputError,
    StructuredExtractionTimeoutError,
    validate_loopback_base_url,
)


class FakeHTTPResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def __enter__(self) -> FakeHTTPResponse:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        del exc_type, exc_value, traceback

    def read(self, maximum_bytes: int = -1) -> bytes:
        del maximum_bytes
        return json.dumps(self.payload).encode()


def _request() -> ExtractionRequest:
    return ExtractionRequest(
        transcript="Synthetic project request with incomplete test details.",
        source_kind=CaptureSourceKind.TEXT,
        source_language="en",
        project_hints=ProjectHints(
            project_id="P-SYN-001",
            project_name="Synthetic project",
        ),
        actor_metadata=ActorMetadata(
            actor_id="synthetic-engineer",
            actor_role="lab_engineer",
        ),
    )


def _candidate() -> LabProjectCaptureCandidate:
    now = datetime(2026, 8, 6, 8, 0, tzinfo=UTC)
    return LabProjectCaptureCandidate(
        capture_session_id=_request().capture_session_id,
        source_kind=CaptureSourceKind.TEXT,
        source_language="en",
        transcript="Synthetic project request with incomplete test details.",
        extraction_model="deterministic-fake",
        extraction_started_at=now,
        extraction_completed_at=now,
        project=ProjectIdentity(
            project_id="P-SYN-001",
            project_name="Synthetic project",
            request_summary="Generalized synthetic project request.",
        ),
    )


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost:11434",
        "http://127.0.0.1:11434/",
        "http://[::1]:11434",
        "https://127.0.0.2:11434",
    ],
)
def test_loopback_ollama_urls_are_accepted(url: str) -> None:
    assert validate_loopback_base_url(url).startswith(("http://", "https://"))


@pytest.mark.parametrize(
    "url",
    [
        "http://ollama.internal:11434",
        "https://example.com",
        "http://192.168.1.20:11434",
        "http://127.0.0.1:11434/api",
        "http://user:password@127.0.0.1:11434",
    ],
)
def test_non_loopback_or_unsafe_ollama_urls_are_rejected(url: str) -> None:
    with pytest.raises(StructuredExtractionConfigurationError):
        validate_loopback_base_url(url)


def test_ollama_uses_schema_deterministic_options_and_validates_candidate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def fake_urlopen(request: Any, *, timeout: float) -> FakeHTTPResponse:
        captured["url"] = request.full_url
        captured["body"] = json.loads(request.data)
        captured["timeout"] = timeout
        return FakeHTTPResponse({"response": json.dumps({"project": {}})})

    monkeypatch.setattr(lab_project_extraction, "_open_local_request", fake_urlopen)
    provider = OllamaStructuredExtractionProvider(
        "http://127.0.0.1:11434",
        "local-test-model",
        timeout_seconds=3,
    )

    candidate = provider.extract(_request())

    assert captured["url"] == "http://127.0.0.1:11434/api/generate"
    assert captured["timeout"] == 3
    assert captured["body"]["stream"] is False
    assert captured["body"]["options"] == {"temperature": 0}
    assert captured["body"]["system"] == SYSTEM_INSTRUCTIONS
    assert captured["body"]["format"] == LabProjectCaptureCandidate.model_json_schema()
    assert candidate.transcript == _request().transcript
    assert candidate.source_kind is CaptureSourceKind.TEXT
    assert candidate.extraction_model == "ollama:local-test-model"
    assert candidate.human_confirmed is False
    assert candidate.human_confirmed_by is None
    assert candidate.recommended_questions


@pytest.mark.parametrize(
    ("raw_candidate", "message"),
    [
        ("not-json", "invalid Candidate JSON"),
        (json.dumps({"project": {"invented": "value"}}), "schema-invalid"),
        (json.dumps({"project": {}, "human_confirmed": True}), "human confirmation"),
    ],
)
def test_invalid_or_unsafe_ollama_candidate_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    raw_candidate: str,
    message: str,
) -> None:
    monkeypatch.setattr(
        lab_project_extraction,
        "_open_local_request",
        lambda request, timeout: FakeHTTPResponse({"response": raw_candidate}),
    )
    provider = OllamaStructuredExtractionProvider("http://localhost:11434", "local-model")

    with pytest.raises(StructuredExtractionOutputError, match=message):
        provider.extract(_request())


def test_ollama_timeout_is_safe(monkeypatch: pytest.MonkeyPatch) -> None:
    def timeout(request: Any, *, timeout: float) -> Any:
        del request, timeout
        raise TimeoutError("synthetic timeout")

    monkeypatch.setattr(lab_project_extraction, "_open_local_request", timeout)
    provider = OllamaStructuredExtractionProvider("http://localhost:11434", "local-model")

    with pytest.raises(StructuredExtractionTimeoutError, match="timed out"):
        provider.extract(_request())


def test_fake_extraction_is_unconfirmed_and_applies_shared_completeness() -> None:
    request = _request()
    provider = DeterministicFakeExtractionProvider(_candidate())

    candidate = provider.extract(request)

    assert provider.calls == [request]
    assert candidate.capture_session_id == request.capture_session_id
    assert candidate.human_confirmed is False
    assert candidate.completeness_score < 100
    assert "project.target_application" in candidate.critical_missing_fields


def test_ollama_preflight_checks_configured_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        lab_project_extraction,
        "_open_local_request",
        lambda request, timeout: FakeHTTPResponse(
            {"models": [{"name": "other-model"}, {"model": "local-model"}]}
        ),
    )
    provider = OllamaStructuredExtractionProvider("http://localhost:11434", "local-model")

    reachable, available, detail = provider.preflight()

    assert reachable is True
    assert available is True
    assert detail == "Configured Ollama model is available"
