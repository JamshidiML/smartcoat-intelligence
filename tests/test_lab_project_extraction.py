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
from smartcoat.services.lab_project_grounding import (
    ExperimentalClaimProposalBatch,
    ProjectMaterialClaimProposalBatch,
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
    captured: list[dict[str, Any]] = []

    def fake_urlopen(request: Any, *, timeout: float) -> FakeHTTPResponse:
        captured.append(
            {
                "url": request.full_url,
                "body": json.loads(request.data),
                "timeout": timeout,
            }
        )
        return FakeHTTPResponse({"response": json.dumps({"claims": []})})

    monkeypatch.setattr(lab_project_extraction, "_open_local_request", fake_urlopen)
    provider = OllamaStructuredExtractionProvider(
        "http://127.0.0.1:11434",
        "local-test-model",
        timeout_seconds=3,
    )

    candidate = provider.extract(_request())

    assert len(captured) == 2
    assert all(item["url"] == "http://127.0.0.1:11434/api/generate" for item in captured)
    assert all(item["timeout"] == 3 for item in captured)
    assert all(item["body"]["stream"] is False for item in captured)
    assert all(item["body"]["think"] is False for item in captured)
    assert all(item["body"]["keep_alive"] == "30m" for item in captured)
    assert all(
        item["body"]["options"] == {"temperature": 0, "num_predict": 128} for item in captured
    )
    assert all(SYSTEM_INSTRUCTIONS in item["body"]["system"] for item in captured)
    assert any(
        item["body"]["format"] == build_ollama_grammar_schema(ProjectMaterialClaimProposalBatch)
        for item in captured
    )
    assert any(
        item["body"]["format"] == build_ollama_grammar_schema(ExperimentalClaimProposalBatch)
        for item in captured
    )
    assert all(item["body"]["format"] != build_ollama_grammar_schema() for item in captured)
    assert candidate.transcript == _request().transcript
    assert candidate.source_kind is CaptureSourceKind.TEXT
    assert candidate.extraction_model == "ollama:local-test-model:grounded-v1"
    assert candidate.human_confirmed is False
    assert candidate.human_confirmed_by is None
    assert candidate.recommended_questions
    assert "Do not create a Candidate" in SYSTEM_INSTRUCTIONS
    assert "Do not generate C-M, C-A, or C-S identifiers" in SYSTEM_INSTRUCTIONS


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
    raw_claims = json.dumps({"claims": ["material|Synthetic material|0|unexpected"]})
    monkeypatch.setattr(
        lab_project_extraction,
        "_open_local_request",
        lambda request, timeout: FakeHTTPResponse({"response": raw_claims}),
    )
    provider = OllamaStructuredExtractionProvider("http://localhost:11434", "local-model")

    with pytest.raises(StructuredExtractionOutputError, match="schema-invalid Pass A"):
        provider.extract(_request())


def test_process_parameter_semantics_move_to_readiness_boundary() -> None:
    parameter = ProcessParameter(**_process_parameter())
    candidate = _candidate().model_copy(update={"process_parameters": (parameter,)})

    report = evaluate_candidate_readiness(candidate)

    assert parameter.measurement_state.value == "known"
    assert report.confirmation_ready is False
    assert report.issues[0].code == "process_parameter_unknown_approach"
    assert report.issues[1].code == "process_parameter_known_without_value"


def test_provider_verifies_claims_before_deterministic_assembly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transcript = "The curing temperature was 210 degrees Celsius."
    pass_b_response = {
        "response": json.dumps({"claims": ["process_parameter|curing temperature|0"]})
    }

    def grounded_response(request: Any, timeout: float) -> FakeHTTPResponse:
        del timeout
        body = json.loads(request.data)
        payload = {"response": json.dumps({"claims": []})}
        if "PASS B" in body["system"]:
            payload = pass_b_response
        return FakeHTTPResponse(payload)

    monkeypatch.setattr(
        lab_project_extraction,
        "_open_local_request",
        grounded_response,
    )
    provider = OllamaStructuredExtractionProvider("http://localhost:11434", "qwen3:4b")

    result = provider.extract_grounded(_request().model_copy(update={"transcript": transcript}))

    assert result.verified_claim_count == 1
    assert result.unsupported_claim_count == 0
    assert result.candidate.process_parameters[0].numeric_value == 210
    assert result.candidate.process_parameters[0].unit == "degrees Celsius"
    assert result.candidate.process_parameters[0].approach_id == "C-A-000"
    assert result.candidate.human_confirmed is False


def test_provider_derives_target_and_relationship_subject_from_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transcript = (
        "We need a one-sided coating for glass fabric for high-temperature flame protection. "
        "The first approach failed after the Bunsen test."
    )

    def grounded_response(request: Any, timeout: float) -> FakeHTTPResponse:
        del timeout
        body = json.loads(request.data)
        claims = ["target_application|project|0"]
        if "PASS B" in body["system"]:
            claims = ["approach_outcome|failed|1"]
        return FakeHTTPResponse({"response": json.dumps({"claims": claims})})

    monkeypatch.setattr(lab_project_extraction, "_open_local_request", grounded_response)

    result = OllamaStructuredExtractionProvider(
        "http://localhost:11434", "qwen3:4b"
    ).extract_grounded(_request().model_copy(update={"transcript": transcript}))

    assert result.unsupported_claim_count == 0
    assert result.candidate.project.target_application == "high-temperature flame protection"
    assert result.candidate.approaches[0].title == "first approach"
    assert result.candidate.approaches[0].outcome.value == "failed"


def test_provider_preserves_source_negative_feasibility_without_assessed_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transcript = "Production feasibility has not yet been evaluated."
    pass_b_response = {"response": json.dumps({"claims": ["production_feasibility|project|0"]})}

    def unsupported_response(request: Any, timeout: float) -> FakeHTTPResponse:
        del timeout
        body = json.loads(request.data)
        payload = {"response": json.dumps({"claims": []})}
        if "PASS B" in body["system"]:
            payload = pass_b_response
        return FakeHTTPResponse(payload)

    monkeypatch.setattr(
        lab_project_extraction,
        "_open_local_request",
        unsupported_response,
    )

    result = OllamaStructuredExtractionProvider(
        "http://localhost:11434", "qwen3:4b"
    ).extract_grounded(_request().model_copy(update={"transcript": transcript}))

    assert result.verified_claim_count == 1
    assert result.unsupported_claim_count == 0
    assert result.candidate.approaches == ()
    assert result.candidate.human_confirmed is False
    assert result.candidate.extraction_warnings[0].startswith("unresolved_approach_relationship:")


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


def test_prompt_uses_immutable_transcript_and_excludes_review_supplement_as_evidence() -> None:
    provider = OllamaStructuredExtractionProvider("http://localhost:11434", "local-model")
    request = _request().model_copy(
        update={
            "source_kind": CaptureSourceKind.VOICE,
            "supplemental_context": "Synthetic reviewer answer.",
        }
    )

    prompt = provider._build_prompt(request, pass_name="Pass A")

    assert "source_transcript" in prompt
    assert "source_segments" in prompt
    assert '"0":"Synthetic project request with incomplete test details."' in prompt
    assert "Synthetic reviewer answer." not in prompt
    assert '"pass":"Pass A"' in prompt
    assert "immutable evidence source" in prompt


@pytest.mark.parametrize(
    "raw_claims",
    [
        "not-json",
        json.dumps({"project": {"invented": "value"}}),
        json.dumps({"claims": [], "human_confirmed": True}),
    ],
)
def test_invalid_or_candidate_shaped_ollama_claim_output_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    raw_claims: str,
) -> None:
    monkeypatch.setattr(
        lab_project_extraction,
        "_open_local_request",
        lambda request, timeout: FakeHTTPResponse({"response": raw_claims}),
    )
    provider = OllamaStructuredExtractionProvider("http://localhost:11434", "local-model")

    with pytest.raises(StructuredExtractionOutputError, match="schema-invalid Pass A"):
        provider.extract(_request())


def test_canonical_claim_validation_rejects_overlength_ollama_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert (
        _schema_values_for_key(
            build_ollama_grammar_schema(ProjectMaterialClaimProposalBatch),
            "maxLength",
        )
        == []
    )
    raw_claims = json.dumps({"claims": [f"project_request|{'x' * 513}|0"]})
    monkeypatch.setattr(
        lab_project_extraction,
        "_open_local_request",
        lambda request, timeout: FakeHTTPResponse({"response": raw_claims}),
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
