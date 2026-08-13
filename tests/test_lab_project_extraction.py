from __future__ import annotations

import json
from datetime import UTC, datetime
from types import TracebackType
from typing import Any

import pytest

from smartcoat.domain.lab_project_capture import (
    CaptureSourceKind,
    LabProjectCaptureCandidate,
    ProcessParameter,
    ProjectIdentity,
    evaluate_candidate_readiness,
)
from smartcoat.services import lab_project_extraction
from smartcoat.services.lab_project_extraction import (
    DEFAULT_OLLAMA_TIMEOUT_SECONDS,
    SYSTEM_INSTRUCTIONS,
    ActorMetadata,
    DeterministicFakeExtractionProvider,
    ExtractionRequest,
    OllamaStructuredExtractionProvider,
    ProjectHints,
    StructuredExtractionConfigurationError,
    StructuredExtractionOutputError,
    StructuredExtractionTimeoutError,
    assign_candidate_correlation_ids,
    build_ollama_grammar_schema,
    normalize_ai_process_parameters,
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


def _schema_values_for_key(value: Any, key: str) -> list[Any]:
    matches: list[Any] = []
    if isinstance(value, dict):
        if key in value:
            matches.append(value[key])
        for child in value.values():
            matches.extend(_schema_values_for_key(child, key))
    elif isinstance(value, list):
        for child in value:
            matches.extend(_schema_values_for_key(child, key))
    return matches


def _process_parameter(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "approach_id": "C-A-001",
        "process_stage": "curing",
        "parameter_name": "temperature",
        "measurement_state": "known",
    }
    payload.update(overrides)
    return payload


def _normalized_parameter(**overrides: Any) -> tuple[dict[str, Any], list[str]]:
    normalized = normalize_ai_process_parameters(
        {"process_parameters": [_process_parameter(**overrides)]}
    )
    return normalized["process_parameters"][0], normalized.get("extraction_warnings", [])


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


def test_ollama_grammar_schema_removes_only_max_length_without_mutation() -> None:
    full_schema = LabProjectCaptureCandidate.model_json_schema()

    compatible = build_ollama_grammar_schema()

    assert 4096 in _schema_values_for_key(full_schema, "maxLength")
    assert _schema_values_for_key(compatible, "maxLength") == []
    assert full_schema == LabProjectCaptureCandidate.model_json_schema()
    assert compatible["type"] == "object"
    assert "properties" in compatible
    assert compatible["required"] == ["capture_session_id", "source_kind", "project"]
    assert "$defs" in compatible
    assert compatible["additionalProperties"] is False
    assert (
        compatible["$defs"]["MaterialRecord"]["properties"]["material_id"]["pattern"]
        == "^C-M-[0-9]{3}$"
    )
    assert compatible["properties"]["materials"]["items"] == {"$ref": "#/$defs/MaterialRecord"}
    assert compatible["properties"]["materials"]["maxItems"] == 64


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
    assert captured["body"]["think"] is False
    assert captured["body"]["keep_alive"] == "30m"
    assert captured["body"]["options"] == {"temperature": 0}
    assert captured["body"]["system"] == SYSTEM_INSTRUCTIONS
    assert captured["body"]["format"] == build_ollama_grammar_schema()
    assert captured["body"]["format"] != LabProjectCaptureCandidate.model_json_schema()
    assert candidate.transcript == _request().transcript
    assert candidate.source_kind is CaptureSourceKind.TEXT
    assert candidate.extraction_model == "ollama:local-test-model"
    assert candidate.human_confirmed is False
    assert candidate.human_confirmed_by is None
    assert candidate.recommended_questions
    assert "Never invent domain facts or source\nidentifiers" in SYSTEM_INSTRUCTIONS
    assert "C-M/C-A/C-S" in SYSTEM_INSTRUCTIONS


def test_ollama_provider_default_timeout_is_pilot_safe() -> None:
    provider = OllamaStructuredExtractionProvider("http://localhost:11434", "local-model")

    assert DEFAULT_OLLAMA_TIMEOUT_SECONDS == 180.0
    assert provider.timeout_seconds == 180.0


def test_valid_known_numeric_process_parameter_is_unchanged() -> None:
    parameter, warnings = _normalized_parameter(numeric_value=210, unit="degC")

    assert parameter == _process_parameter(numeric_value=210, unit="degC")
    assert warnings == []


def test_valid_known_text_process_parameter_is_unchanged() -> None:
    parameter, warnings = _normalized_parameter(text_value="high")

    assert parameter == _process_parameter(text_value="high")
    assert warnings == []


def test_known_process_parameter_with_both_values_becomes_conflicting() -> None:
    parameter, warnings = _normalized_parameter(
        numeric_value=210,
        text_value="210 degrees Celsius",
        unit="degC",
        source_note="Synthetic source supplied both representations.",
    )

    assert parameter["measurement_state"] == "conflicting"
    assert parameter["numeric_value"] == 210
    assert parameter["text_value"] == "210 degrees Celsius"
    assert parameter["unit"] == "degC"
    assert parameter["source_note"] == "Synthetic source supplied both representations."
    assert warnings[0].startswith("process_parameter_normalized_conflicting_values:")


def test_known_process_parameter_without_value_becomes_unknown() -> None:
    parameter, warnings = _normalized_parameter()

    assert parameter["measurement_state"] == "unknown"
    assert "numeric_value" not in parameter
    assert "text_value" not in parameter
    assert warnings[0].startswith("process_parameter_normalized_missing_value:")


def test_known_numeric_process_parameter_without_unit_becomes_conflicting() -> None:
    parameter, warnings = _normalized_parameter(numeric_value=210)

    assert parameter["measurement_state"] == "conflicting"
    assert parameter["numeric_value"] == 210
    assert "unit" not in parameter
    assert warnings[0].startswith("process_parameter_normalized_missing_unit:")


@pytest.mark.parametrize(
    ("state", "value_field", "value"),
    [
        ("unknown", "numeric_value", 210),
        ("not_measured", "text_value", "not recorded"),
    ],
)
def test_non_known_process_parameter_with_value_becomes_conflicting(
    state: str,
    value_field: str,
    value: object,
) -> None:
    parameter, warnings = _normalized_parameter(**{"measurement_state": state, value_field: value})

    assert parameter["measurement_state"] == "conflicting"
    assert parameter[value_field] == value
    assert warnings[0].startswith("process_parameter_normalized_state_value_conflict:")


def test_empty_conflicting_process_parameter_becomes_unknown() -> None:
    parameter, warnings = _normalized_parameter(measurement_state="conflicting")

    assert parameter["measurement_state"] == "unknown"
    assert warnings[0].startswith("process_parameter_normalized_empty_conflict:")


def test_normalization_preserves_and_deduplicates_warnings_deterministically() -> None:
    raw = {
        "process_parameters": [_process_parameter()],
        "extraction_warnings": ["existing-warning", "existing-warning"],
    }

    normalized = normalize_ai_process_parameters(raw)

    assert normalized["extraction_warnings"][0] == "existing-warning"
    assert len(normalized["extraction_warnings"]) == 2
    assert normalized["extraction_warnings"][1].startswith(
        "process_parameter_normalized_missing_value:"
    )


def test_normalization_does_not_mutate_input_or_set_confirmation_or_create_unit() -> None:
    raw = {"process_parameters": [_process_parameter(numeric_value=210)]}

    normalized = normalize_ai_process_parameters(raw)

    assert raw == {"process_parameters": [_process_parameter(numeric_value=210)]}
    assert normalized is not raw
    assert normalized["process_parameters"] is not raw["process_parameters"]
    assert "human_confirmed" not in normalized
    assert "unit" not in normalized["process_parameters"][0]


def test_malformed_process_parameter_state_is_not_normalized_and_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    malformed = _process_parameter(measurement_state="definitely_invalid", numeric_value=210)
    assert (
        normalize_ai_process_parameters({"process_parameters": [malformed]})["process_parameters"][
            0
        ]
        == malformed
    )
    raw_candidate = json.dumps({"project": {}, "process_parameters": [malformed]})
    monkeypatch.setattr(
        lab_project_extraction,
        "_open_local_request",
        lambda request, timeout: FakeHTTPResponse({"response": raw_candidate}),
    )
    provider = OllamaStructuredExtractionProvider("http://localhost:11434", "local-model")

    with pytest.raises(StructuredExtractionOutputError, match="schema-invalid"):
        provider.extract(_request())


def test_process_parameter_semantics_move_to_readiness_boundary() -> None:
    parameter = ProcessParameter(**_process_parameter())
    candidate = _candidate().model_copy(update={"process_parameters": (parameter,)})

    report = evaluate_candidate_readiness(candidate)

    assert parameter.measurement_state.value == "known"
    assert report.confirmation_ready is False
    assert report.issues[0].code == "process_parameter_unknown_approach"
    assert report.issues[1].code == "process_parameter_known_without_value"


def test_provider_applies_process_parameter_normalization_before_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw_candidate = json.dumps(
        {
            "project": {},
            "approaches": [{"approach_id": "model-approach", "outcome": "failed"}],
            "process_parameters": [
                {
                    "approach_id": "model-approach",
                    "process_stage": "curing",
                    "parameter_name": "temperature",
                    "numeric_value": 210,
                    "text_value": "210 degrees Celsius",
                    "unit": "degC",
                    "measurement_state": "known",
                }
            ],
        }
    )
    monkeypatch.setattr(
        lab_project_extraction,
        "_open_local_request",
        lambda request, timeout: FakeHTTPResponse({"response": raw_candidate}),
    )
    provider = OllamaStructuredExtractionProvider("http://localhost:11434", "local-model")

    candidate = provider.extract(_request())

    assert candidate.process_parameters[0].measurement_state.value == "conflicting"
    assert candidate.process_parameters[0].numeric_value == 210
    assert candidate.process_parameters[0].text_value == "210 degrees Celsius"
    assert candidate.extraction_warnings[0].startswith(
        "process_parameter_normalized_conflicting_values:"
    )


def test_qwen3_4b_orphan_process_references_return_reviewable_candidate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw_candidate = json.dumps(
        {
            "project": {"request_summary": "Synthetic flame-protection request."},
            "approaches": [
                {"approach_id": f"C-A-{index:03d}", "outcome": "inconclusive"}
                for index in range(1, 4)
            ],
            "process_parameters": [
                {
                    "approach_id": "C-A-004",
                    "process_stage": "curing",
                    "parameter_name": "curing temperature",
                    "measurement_state": "unknown",
                }
            ],
        }
    )
    monkeypatch.setattr(
        lab_project_extraction,
        "_open_local_request",
        lambda request, timeout: FakeHTTPResponse({"response": raw_candidate}),
    )

    candidate = OllamaStructuredExtractionProvider("http://localhost:11434", "qwen3:4b").extract(
        _request()
    )
    readiness = evaluate_candidate_readiness(candidate)

    assert candidate.process_parameters[0].approach_id == "C-A-004"
    assert readiness.confirmation_ready is False
    assert readiness.issues[0].code == "process_parameter_unknown_approach"


def test_qwen3_1_7b_amount_without_unit_returns_reviewable_candidate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw_candidate = json.dumps(
        {
            "project": {"request_summary": "Synthetic flame-protection request."},
            "materials": [
                {"material_id": f"raw-{index}", "amount": amount}
                for index, amount in enumerate((5, 10, 15), start=1)
            ],
        }
    )
    monkeypatch.setattr(
        lab_project_extraction,
        "_open_local_request",
        lambda request, timeout: FakeHTTPResponse({"response": raw_candidate}),
    )

    candidate = OllamaStructuredExtractionProvider("http://localhost:11434", "qwen3:1.7b").extract(
        _request()
    )
    readiness = evaluate_candidate_readiness(candidate)

    assert [material.amount for material in candidate.materials] == [5, 10, 15]
    assert [material.unit for material in candidate.materials] == [None, None, None]
    assert readiness.confirmation_ready is False
    assert [issue.code for issue in readiness.issues] == [
        "material_amount_missing_unit",
        "material_amount_missing_unit",
        "material_amount_missing_unit",
    ]


def test_candidate_correlation_ids_are_positional_and_source_ids_are_not_inferred() -> None:
    normalized = assign_candidate_correlation_ids(
        {
            "materials": [{"material_id": "model-material", "material_name": "Synthetic"}],
            "approaches": [
                {
                    "approach_id": "model-approach",
                    "source_approach_id": "SRC-A-7",
                    "outcome": "planned",
                }
            ],
            "process_parameters": [
                {
                    "approach_id": "model-approach",
                    "process_stage": "curing",
                    "parameter_name": "temperature",
                    "measurement_state": "unknown",
                }
            ],
            "samples": [
                {
                    "sample_id": "model-sample",
                    "approach_id": "model-approach",
                    "physical_archive_status": "unknown",
                }
            ],
            "tests": [],
            "customer_feedback": [],
            "evidence": [],
        }
    )

    assert normalized["materials"][0]["material_id"] == "C-M-001"
    assert "source_material_id" not in normalized["materials"][0]
    assert normalized["approaches"][0]["approach_id"] == "C-A-001"
    assert normalized["approaches"][0]["source_approach_id"] == "SRC-A-7"
    assert normalized["process_parameters"][0]["approach_id"] == "C-A-001"
    assert normalized["samples"][0]["sample_id"] == "C-S-001"
    assert normalized["samples"][0]["approach_id"] == "C-A-001"


def test_prompt_separates_immutable_transcript_from_review_supplement() -> None:
    provider = OllamaStructuredExtractionProvider("http://localhost:11434", "local-model")
    request = _request().model_copy(
        update={
            "source_kind": CaptureSourceKind.VOICE,
            "supplemental_context": "Synthetic reviewer answer.",
        }
    )

    prompt = provider._build_prompt(request)

    assert "source_transcript" in prompt
    assert "human_review_supplement" in prompt
    assert "Synthetic reviewer answer." in prompt
    assert "immutable source text" in prompt


@pytest.mark.parametrize(
    ("raw_candidate", "message"),
    [
        ("not-json", "invalid Candidate JSON"),
        (json.dumps({"project": {"invented": "value"}}), "schema-invalid"),
        (json.dumps({"project": {}, "human_confirmed": True}), "human confirmation"),
        (
            json.dumps({"project": {}, "human_confirmed_by": "synthetic-reviewer"}),
            "human confirmation",
        ),
        (
            json.dumps({"project": {}, "human_confirmed_at": "2026-08-10T10:00:00Z"}),
            "human confirmation",
        ),
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


def test_full_candidate_validation_rejects_overlength_ollama_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert _schema_values_for_key(build_ollama_grammar_schema(), "maxLength") == []
    raw_candidate = json.dumps({"project": {"request_summary": "x" * 4097}})
    monkeypatch.setattr(
        lab_project_extraction,
        "_open_local_request",
        lambda request, timeout: FakeHTTPResponse({"response": raw_candidate}),
    )
    provider = OllamaStructuredExtractionProvider("http://localhost:11434", "local-model")

    with pytest.raises(StructuredExtractionOutputError, match="schema-invalid"):
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
