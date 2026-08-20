"""Local structured extraction providers for lab-project capture candidates."""

from __future__ import annotations

import json
import math
import re
from collections.abc import Mapping
from copy import deepcopy
from datetime import UTC, datetime
from http.client import HTTPMessage
from ipaddress import ip_address
from time import perf_counter
from typing import IO, Any, Protocol, cast
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from smartcoat.domain.lab_project_capture import (
    CaptureSourceKind,
    LabProjectCaptureCandidate,
    ProjectIdentity,
    apply_candidate_completeness,
)
from smartcoat.services.lab_project_grounding import (
    ExperimentalClaimProposalBatch,
    GroundedClaim,
    GroundedClaimState,
    GroundedClaimStatus,
    GroundedClaimType,
    GroundedExtractionResult,
    ProjectMaterialClaimProposalBatch,
    assemble_candidate_from_grounded_claims,
    normalize_transcript_line_endings,
    verify_grounded_claims,
)

SYSTEM_INSTRUCTIONS = """You extract atomic evidence-grounded claims from one immutable
SmartCoat source transcript. Return only JSON matching the supplied claim-batch schema.
Do not create a Candidate. Do not generate C-M, C-A, or C-S identifiers. Every claim must
select the zero-based `segment_index` of one supplied source segment. Python will copy the
exact quote and offsets from that segment and derive values from its literal text. Never
invent dates, timestamps, measurements, units, feedback, assessments,
relationships, or missing entities. Use subject_label='unresolved' when the quote does not
identify the related approach or sample. Negative statements must use unknown,
not_measured, or not_assessed as appropriate, never known. Omit facts that lack direct
source evidence. A count of unnamed approaches does not authorize invented approaches.
Each compact claim string is `claim_type|subject_label|segment_index`. Do not add spaces
around `|`. Do not emit placeholder claims for absent facts. Use subject label `project`
for project claims and `unresolved` only when the selected segment contains no stable
subject label. Python expands the wire string and derives exact values, field names,
states, numeric values, units, quotes, and offsets deterministically. The final wire value
must be the exact `segment_index` printed beside the supporting sentence. Read every
numbered segment before selecting it. A segment may support more than one atomic claim."""

PASS_A_INSTRUCTIONS = """PASS A extracts only project_request, target_application,
industrial_function, customer_requirement, success_criterion, substrate_name,
substrate_type, substrate_reason, material, material_amount, and material_function claims.
Return no more than five claims. Scan the whole transcript and use this priority order:
(1) one project_request, (2) one target_application, (3) one substrate_name, then (4) one
material claim for EACH explicitly named material. Do not duplicate the target as an
industrial_function when both would use the same words, but always emit target_application
separately from project_request when the target is explicit. Omit lower-priority claims
when needed to retain named materials. Project subjects must be `project`; a substrate
subject must be the exact substrate phrase; every material subject must be that exact
material name, never `project`. Example wire forms are `project_request|project|0`,
`substrate_name|glass fabric|0`, and `material|calcium carbonate|4`."""

PASS_B_INSTRUCTIONS = """PASS B extracts only approach, approach_outcome,
approach_failure_reason, approach_lesson, process_parameter, test, test_result, sample,
shipment, archive, customer_feedback, next_action, production_feasibility,
price_optimization, and reuse_potential claims. Return no more than eight claims. Scan the
whole transcript and prioritize, in order: every explicit approach outcome; every explicitly
unmeasured parameter; every numeric process parameter; every shipment; customer-feedback
status; production-feasibility status. Do not spend a slot on an approach lesson unless the
source explicitly says what was learned. Do not duplicate an outcome as a test result.
For process parameters, use an explicit approach label when the sentence contains one;
otherwise use `unresolved`, never the numeric value. For shipments use the exact sample
label. For feedback use `unresolved`; for feasibility use `project`. Use the exact
segment_index beside the supporting sentence, including later segments. Example wire forms
are `process_parameter|unresolved|4`, `shipment|S-02|4`, and
`customer_feedback|unresolved|5`."""

MAX_OLLAMA_RESPONSE_BYTES = 2 * 1024 * 1024
MAX_OLLAMA_PREDICT_TOKENS = 128
DEFAULT_OLLAMA_TIMEOUT_SECONDS = 180.0


class _NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(
        self,
        req: Request,
        fp: IO[bytes],
        code: int,
        msg: str,
        headers: HTTPMessage,
        newurl: str,
    ) -> None:
        del req, fp, code, msg, headers, newurl
        return None


def _open_local_request(request: Request, *, timeout: float) -> Any:
    return build_opener(_NoRedirectHandler()).open(request, timeout=timeout)


class StructuredExtractionError(RuntimeError):
    """Base error for expected local structured-extraction failures."""


class StructuredExtractionConfigurationError(StructuredExtractionError):
    """Raised when a provider is not safely configured for local-only use."""


class StructuredExtractionProviderUnavailableError(StructuredExtractionError):
    """Raised when the configured local provider is unavailable."""


class StructuredExtractionTimeoutError(StructuredExtractionError):
    """Raised when the configured local provider exceeds its timeout."""


class StructuredExtractionOutputError(StructuredExtractionError):
    """Raised when the provider returns invalid or unsafe Candidate JSON."""


class ActorMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    actor_id: str = Field(min_length=1, max_length=512)
    actor_role: str = Field(min_length=1, max_length=128)


class ProjectHints(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    project_id: str | None = Field(default=None, min_length=1, max_length=256)
    project_name: str | None = Field(default=None, min_length=1, max_length=512)
    customer_company: str | None = Field(default=None, min_length=1, max_length=512)
    request_summary: str | None = Field(default=None, min_length=1, max_length=4096)
    target_application: str | None = Field(default=None, min_length=1, max_length=512)


class ExtractionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    transcript: str = Field(min_length=1, max_length=4096)
    source_kind: CaptureSourceKind
    source_language: str | None = Field(default=None, min_length=2, max_length=35)
    project_hints: ProjectHints | None = None
    actor_metadata: ActorMetadata | None = None
    supplemental_context: str | None = Field(default=None, min_length=1, max_length=4096)
    capture_session_id: UUID = Field(default_factory=uuid4)


class StructuredExtractionProvider(Protocol):
    """Contract for transcript-to-Candidate providers used by the pilot."""

    def extract_grounded(self, request: ExtractionRequest) -> GroundedExtractionResult: ...


def build_ollama_grammar_schema(
    model: type[BaseModel] = LabProjectCaptureCandidate,
) -> dict[str, Any]:
    """Return a maxLength-free copy for Ollama's structured-output grammar."""

    schema = deepcopy(model.model_json_schema())

    def remove_max_length(value: Any) -> None:
        if isinstance(value, dict):
            value.pop("maxLength", None)
            for child in value.values():
                remove_max_length(child)
        elif isinstance(value, list):
            for child in value:
                remove_max_length(child)

    # This adapts only the Ollama/llama.cpp grammar; canonical Pydantic validation
    # remains authoritative after generation.
    remove_max_length(schema)
    return schema


def normalize_ai_process_parameters(payload: dict[str, Any]) -> dict[str, Any]:
    """Conservatively normalize unapproved AI process-parameter payloads."""

    normalized = deepcopy(payload)
    raw_parameters = normalized.get("process_parameters")
    if not isinstance(raw_parameters, list):
        return normalized

    existing_warnings = normalized.get("extraction_warnings", [])
    if not isinstance(existing_warnings, list) or not all(
        isinstance(warning, str) for warning in existing_warnings
    ):
        return normalized

    normalization_warnings: list[str] = []
    for index, raw_parameter in enumerate(raw_parameters, start=1):
        if not isinstance(raw_parameter, Mapping):
            continue
        parameter = dict(raw_parameter)
        raw_parameters[index - 1] = parameter

        approach_id = parameter.get("approach_id")
        process_stage = parameter.get("process_stage")
        parameter_name = parameter.get("parameter_name")
        if (
            not isinstance(approach_id, str)
            or re.fullmatch(r"C-A-[0-9]{3}", approach_id) is None
            or not isinstance(process_stage, str)
            or not process_stage.strip()
            or len(process_stage.strip()) > 512
            or not isinstance(parameter_name, str)
            or not parameter_name.strip()
            or len(parameter_name.strip()) > 512
        ):
            continue

        numeric_value = parameter.get("numeric_value")
        text_value = parameter.get("text_value")
        unit = parameter.get("unit")
        source_note = parameter.get("source_note")
        has_numeric = numeric_value is not None
        has_text = text_value is not None
        has_source_note = source_note is not None
        if has_numeric and (
            isinstance(numeric_value, bool)
            or not isinstance(numeric_value, int | float)
            or not math.isfinite(numeric_value)
        ):
            continue
        if has_text and (
            not isinstance(text_value, str)
            or not text_value.strip()
            or len(text_value.strip()) > 512
        ):
            continue
        if unit is not None and (
            not isinstance(unit, str) or not unit.strip() or len(unit.strip()) > 512
        ):
            continue
        if has_source_note and (
            not isinstance(source_note, str)
            or not source_note.strip()
            or len(source_note.strip()) > 4096
        ):
            continue

        state = parameter.get("measurement_state")
        warning_prefix: str | None = None
        if state == "known":
            if has_numeric and has_text:
                parameter["measurement_state"] = "conflicting"
                warning_prefix = "process_parameter_normalized_conflicting_values:"
            elif not has_numeric and not has_text:
                parameter["measurement_state"] = "unknown"
                warning_prefix = "process_parameter_normalized_missing_value:"
            elif has_numeric and unit is None:
                parameter["measurement_state"] = "conflicting"
                warning_prefix = "process_parameter_normalized_missing_unit:"
        elif state in {"unknown", "not_measured", "not_applicable"}:
            if has_numeric or has_text:
                parameter["measurement_state"] = "conflicting"
                warning_prefix = "process_parameter_normalized_state_value_conflict:"
        elif state == "conflicting" and not (has_numeric or has_text or has_source_note):
            parameter["measurement_state"] = "unknown"
            warning_prefix = "process_parameter_normalized_empty_conflict:"

        if warning_prefix is not None:
            normalization_warnings.append(
                f"{warning_prefix} approach_id={approach_id} "
                f"parameter_name={parameter_name.strip()}"
            )

    if normalization_warnings:
        deduplicated: list[str] = []
        for warning in [*existing_warnings, *normalization_warnings]:
            if warning not in deduplicated:
                deduplicated.append(warning)
        normalized["extraction_warnings"] = deduplicated
    return normalized


def assign_candidate_correlation_ids(payload: dict[str, Any]) -> dict[str, Any]:
    """Assign positional Candidate-only IDs and remap cross-section references."""

    normalized = dict(payload)

    materials: list[dict[str, Any]] = []
    for index, raw_item in enumerate(payload.get("materials") or (), start=1):
        if not isinstance(raw_item, Mapping):
            materials.append(raw_item)
            continue
        item = dict(raw_item)
        item["material_id"] = f"C-M-{index:03d}"
        materials.append(item)
    normalized["materials"] = materials

    approach_id_map: dict[str, str] = {}
    approaches: list[dict[str, Any]] = []
    for index, raw_item in enumerate(payload.get("approaches") or (), start=1):
        if not isinstance(raw_item, Mapping):
            approaches.append(raw_item)
            continue
        item = dict(raw_item)
        old_id = item.get("approach_id")
        new_id = f"C-A-{index:03d}"
        if isinstance(old_id, str):
            if old_id in approach_id_map:
                raise StructuredExtractionOutputError(
                    "AI output contained duplicate approach correlation IDs"
                )
            approach_id_map[old_id] = new_id
        item["approach_id"] = new_id
        approaches.append(item)
    normalized["approaches"] = approaches

    sample_id_map: dict[str, str] = {}
    samples: list[dict[str, Any]] = []
    for index, raw_item in enumerate(payload.get("samples") or (), start=1):
        if not isinstance(raw_item, Mapping):
            samples.append(raw_item)
            continue
        item = dict(raw_item)
        old_id = item.get("sample_id")
        new_id = f"C-S-{index:03d}"
        if isinstance(old_id, str):
            if old_id in sample_id_map:
                raise StructuredExtractionOutputError(
                    "AI output contained duplicate sample correlation IDs"
                )
            sample_id_map[old_id] = new_id
        item["sample_id"] = new_id
        samples.append(item)

    def remap_records(
        records: Any,
        *,
        remap_approach: bool = False,
        remap_sample: bool = False,
    ) -> list[Any]:
        remapped: list[Any] = []
        for raw_item in records or ():
            if not isinstance(raw_item, Mapping):
                remapped.append(raw_item)
                continue
            item = dict(raw_item)
            if remap_approach and isinstance(item.get("approach_id"), str):
                item["approach_id"] = approach_id_map.get(item["approach_id"], item["approach_id"])
            if remap_sample and isinstance(item.get("sample_id"), str):
                item["sample_id"] = sample_id_map.get(item["sample_id"], item["sample_id"])
            remapped.append(item)
        return remapped

    normalized["process_parameters"] = remap_records(
        payload.get("process_parameters"), remap_approach=True
    )
    normalized["tests"] = remap_records(
        payload.get("tests"), remap_approach=True, remap_sample=True
    )
    normalized["samples"] = remap_records(samples, remap_approach=True)
    normalized["customer_feedback"] = remap_records(
        payload.get("customer_feedback"), remap_sample=True
    )
    normalized["evidence"] = remap_records(
        payload.get("evidence"), remap_approach=True, remap_sample=True
    )
    return normalized


def validate_loopback_base_url(base_url: str) -> str:
    """Return a normalized Ollama URL only when it targets a literal loopback host."""

    normalized = base_url.strip().rstrip("/")
    parsed = urlsplit(normalized)
    if (
        parsed.scheme not in {"http", "https"}
        or parsed.hostname is None
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
    ):
        raise StructuredExtractionConfigurationError(
            "Ollama base URL must be an HTTP(S) loopback origin without credentials or a path"
        )

    host = parsed.hostname.casefold()
    if host != "localhost":
        try:
            if not ip_address(host).is_loopback:
                raise StructuredExtractionConfigurationError(
                    "Ollama base URL must use a loopback host"
                )
        except ValueError as error:
            raise StructuredExtractionConfigurationError(
                "Ollama base URL must use localhost or a literal loopback address"
            ) from error
    return normalized


def _source_segments(transcript: str) -> list[dict[str, object]]:
    """Expose exact, bounded transcript spans so small models can copy safe offsets."""

    segments: list[dict[str, object]] = []
    for sentence_match in re.finditer(r"[^.!?\n]+[.!?]?", transcript):
        raw = sentence_match.group(0)
        leading = len(raw) - len(raw.lstrip())
        trailing = len(raw) - len(raw.rstrip())
        start = sentence_match.start() + leading
        end = sentence_match.end() - trailing
        while end - start > 300:
            split_at = transcript.rfind(" ", start, start + 301)
            if split_at <= start:
                split_at = start + 300
            segments.append(
                {
                    "source_start": start,
                    "source_end": split_at,
                    "source_quote": transcript[start:split_at],
                }
            )
            start = split_at
            while start < end and transcript[start].isspace():
                start += 1
        if start < end:
            segments.append(
                {
                    "source_start": start,
                    "source_end": end,
                    "source_quote": transcript[start:end],
                }
            )
    return segments


def _claim_state_from_source(
    claim_type: GroundedClaimType,
    source_quote: str,
) -> GroundedClaimState:
    normalized = " ".join(source_quote.casefold().replace("-", " ").split())
    if "not applicable" in normalized:
        return GroundedClaimState.NOT_APPLICABLE
    if any(term in normalized for term in ("conflicting", "contradictory", "inconsistent")):
        return GroundedClaimState.CONFLICTING
    is_negative = bool(
        re.search(
            r"\b(?:no|not|never|without|did not|has not|have not|was not|were not)\b",
            normalized,
        )
    )
    if not is_negative:
        return GroundedClaimState.KNOWN
    if claim_type is GroundedClaimType.PROCESS_PARAMETER and any(
        term in normalized for term in ("not measured", "did not record", "not recorded")
    ):
        return GroundedClaimState.NOT_MEASURED
    if claim_type in {
        GroundedClaimType.CUSTOMER_FEEDBACK,
        GroundedClaimType.PRODUCTION_FEASIBILITY,
        GroundedClaimType.PRICE_OPTIMIZATION,
    }:
        return GroundedClaimState.NOT_ASSESSED
    return GroundedClaimState.KNOWN


def _numeric_value_and_unit(
    claim_type: GroundedClaimType,
    source_value: str | None,
) -> tuple[float | None, str | None]:
    if source_value is None or claim_type not in {
        GroundedClaimType.MATERIAL_AMOUNT,
        GroundedClaimType.PROCESS_PARAMETER,
        GroundedClaimType.TEST_RESULT,
    }:
        return None, None
    match = re.search(r"(?<![\w.])([-+]?\d+(?:[.,]\d+)?)(?![\w.])", source_value)
    if match is None:
        return None, None
    numeric_value = float(match.group(1).replace(",", "."))
    unit = source_value[match.end() :].strip(" ,.;:()") or None
    return numeric_value, unit


def _parameter_name_from_source(source_value: str) -> str:
    normalized = source_value.casefold().replace("_", " ").replace("-", " ")
    if "cured" in normalized and ("degrees" in normalized or "°" in source_value):
        return "curing temperature"
    terms = (
        "curing temperature",
        "coating weight",
        "curing time",
        "line speed",
        "mixing time",
        "mixer speed",
        "dryer temperature",
        "padder pressure",
        "foulard pressure",
        "knife gap",
        "viscosity",
        "pressure",
        "temperature",
    )
    return next((term for term in terms if term in normalized), "source parameter")


def _test_name_from_source(source_value: str) -> str:
    normalized = source_value.casefold()
    for term in ("laboratory flame test", "bunsen test", "flame test"):
        if term in normalized:
            return term
    return "source test"


def _source_match(quote: str, pattern: str) -> str | None:
    match = re.search(pattern, quote, flags=re.IGNORECASE)
    return match.group(1).strip(" ,.;:") if match is not None else None


def _subject_label_from_source(
    claim_type: GroundedClaimType,
    proposed_subject: str,
    source_quote: str,
) -> str:
    if claim_type is GroundedClaimType.MATERIAL:
        return proposed_subject
    if claim_type in {
        GroundedClaimType.APPROACH_OUTCOME,
        GroundedClaimType.APPROACH_FAILURE_REASON,
        GroundedClaimType.APPROACH_LESSON,
        GroundedClaimType.PROCESS_PARAMETER,
        GroundedClaimType.TEST_RESULT,
    }:
        approach = _source_match(source_quote, r"\b((?:first|second|third) approach)\b")
        if approach is not None:
            return approach
        if claim_type is GroundedClaimType.PROCESS_PARAMETER:
            return "unresolved"
    if claim_type is GroundedClaimType.CUSTOMER_FEEDBACK:
        return "unresolved"
    if claim_type in {
        GroundedClaimType.PRODUCTION_FEASIBILITY,
        GroundedClaimType.PRICE_OPTIMIZATION,
    }:
        return "project"
    if claim_type is GroundedClaimType.SHIPMENT:
        sample = _source_match(source_quote, r"\bsample\s+([A-Za-z0-9._-]+)")
        if sample is not None:
            return sample
    if proposed_subject != "unresolved":
        return proposed_subject
    return proposed_subject


def _source_value_from_source(
    claim_type: GroundedClaimType,
    subject_label: str,
    source_quote: str,
) -> str | None:
    if claim_type is GroundedClaimType.PROJECT_REQUEST:
        return source_quote
    if claim_type in {
        GroundedClaimType.TARGET_APPLICATION,
        GroundedClaimType.INDUSTRIAL_FUNCTION,
    }:
        clauses = re.split(r"\bfor\s+", source_quote, flags=re.IGNORECASE)
        return clauses[-1].strip(" ,.;:") if len(clauses) > 1 else None
    if claim_type is GroundedClaimType.SUBSTRATE_NAME:
        return _source_match(
            source_quote,
            r"\b((?:one-sided\s+)?(?:[A-Za-z]+-coated\s+)?[A-Za-z]+\s+fabric)\b",
        )
    if claim_type is GroundedClaimType.SUBSTRATE_TYPE:
        return _source_match(source_quote, r"\b([A-Za-z]+\s+fabric)\b")
    if claim_type in {
        GroundedClaimType.MATERIAL,
        GroundedClaimType.MATERIAL_AMOUNT,
        GroundedClaimType.MATERIAL_FUNCTION,
    }:
        return subject_label
    if claim_type in {GroundedClaimType.APPROACH_OUTCOME, GroundedClaimType.TEST_RESULT}:
        return _source_match(
            source_quote,
            r"\b(failed|passed|successful|partially successful|inconclusive)\b",
        )
    if claim_type is GroundedClaimType.APPROACH_FAILURE_REASON:
        return _source_match(source_quote, r"\bfailed\s+([^,.;]+)")
    if claim_type is GroundedClaimType.PROCESS_PARAMETER:
        if "coating weight" in source_quote.casefold():
            return "coating weight"
        numeric_parameter = _source_match(
            source_quote,
            r"\b(?:cured|temperature(?:\s+was)?)\s+(?:at\s+)?"
            r"([-+]?\d+(?:[.,]\d+)?\s+(?:degrees\s+)?[A-Za-z°]+)",
        )
        return numeric_parameter
    if claim_type is GroundedClaimType.SHIPMENT:
        return _source_match(source_quote, r"\bto\s+(?:the\s+)?([^,.;]+)")
    if claim_type in {
        GroundedClaimType.CUSTOMER_FEEDBACK,
        GroundedClaimType.PRODUCTION_FEASIBILITY,
        GroundedClaimType.PRICE_OPTIMIZATION,
    }:
        return None
    return source_quote


class OllamaStructuredExtractionProvider:
    """Extract Candidates through Ollama's local standard-library HTTP API."""

    provider_name = "ollama"

    def __init__(
        self,
        base_url: str,
        model: str,
        *,
        timeout_seconds: float = DEFAULT_OLLAMA_TIMEOUT_SECONDS,
    ) -> None:
        self.base_url = validate_loopback_base_url(base_url)
        normalized_model = model.strip()
        if not normalized_model:
            raise StructuredExtractionConfigurationError("Ollama model must not be blank")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self.model = normalized_model
        self.timeout_seconds = timeout_seconds

    def extract(self, request: ExtractionRequest) -> LabProjectCaptureCandidate:
        """Compatibility entrypoint returning only the assembled Candidate."""

        return self.extract_grounded(request).candidate

    def extract_grounded(self, request: ExtractionRequest) -> GroundedExtractionResult:
        """Extract, verify, and assemble two independent bounded claim batches."""

        started_at = datetime.now(UTC)
        total_started = perf_counter()

        pass_started = perf_counter()
        pass_a = cast(
            ProjectMaterialClaimProposalBatch,
            self._extract_claim_batch(
                request,
                batch_model=ProjectMaterialClaimProposalBatch,
                pass_name="Pass A: project and material context",
                pass_instructions=PASS_A_INSTRUCTIONS,
            ),
        )
        pass_a_runtime = perf_counter() - pass_started

        pass_started = perf_counter()
        pass_b = cast(
            ExperimentalClaimProposalBatch,
            self._extract_claim_batch(
                request,
                batch_model=ExperimentalClaimProposalBatch,
                pass_name="Pass B: experimental history",
                pass_instructions=PASS_B_INSTRUCTIONS,
            ),
        )
        pass_b_runtime = perf_counter() - pass_started
        total_runtime = perf_counter() - total_started
        completed_at = datetime.now(UTC)

        segments = _source_segments(normalize_transcript_line_endings(request.transcript))
        raw_claims = tuple(
            self._expand_claim_proposal(proposal, "A", index, segments)
            for index, proposal in enumerate(pass_a.claims, start=1)
        ) + tuple(
            self._expand_claim_proposal(proposal, "B", index, segments)
            for index, proposal in enumerate(pass_b.claims, start=1)
        )
        verifications = verify_grounded_claims(raw_claims, request.transcript)
        verified_claims = tuple(
            item.claim for item in verifications if item.status is GroundedClaimStatus.VERIFIED
        )
        review_warnings = tuple(
            f"ai_claim_requires_review:{item.claim.claim_id}:{item.reason_code.value}"
            for item in verifications
            if item.status is not GroundedClaimStatus.VERIFIED
        )
        try:
            candidate = assemble_candidate_from_grounded_claims(
                verified_claims,
                capture_session_id=request.capture_session_id,
                source_kind=request.source_kind,
                source_language=request.source_language,
                transcript=request.transcript,
                extraction_model=f"{self.provider_name}:{self.model}:grounded-v1",
                extraction_started_at=started_at,
                extraction_completed_at=completed_at,
                initial_warnings=review_warnings,
            )
        except ValidationError as error:
            raise StructuredExtractionOutputError(
                "Verified claims could not be assembled into a valid Candidate"
            ) from error
        return GroundedExtractionResult(
            candidate=apply_candidate_completeness(candidate),
            claim_verifications=verifications,
            pass_a_runtime_seconds=pass_a_runtime,
            pass_b_runtime_seconds=pass_b_runtime,
            total_runtime_seconds=total_runtime,
        )

    def _extract_claim_batch(
        self,
        request: ExtractionRequest,
        *,
        batch_model: type[ProjectMaterialClaimProposalBatch] | type[ExperimentalClaimProposalBatch],
        pass_name: str,
        pass_instructions: str,
    ) -> ProjectMaterialClaimProposalBatch | ExperimentalClaimProposalBatch:
        payload = {
            "model": self.model,
            "system": SYSTEM_INSTRUCTIONS + "\n\n" + pass_instructions,
            "prompt": self._build_prompt(request, pass_name=pass_name),
            "format": build_ollama_grammar_schema(batch_model),
            "stream": False,
            "think": False,
            "keep_alive": "30m",
            "options": {
                "temperature": 0,
                "num_predict": MAX_OLLAMA_PREDICT_TOKENS,
            },
        }
        response = self._request_json("/api/generate", payload)
        raw_claims = response.get("response")
        if not isinstance(raw_claims, str):
            raise StructuredExtractionOutputError(
                f"Ollama response did not contain {pass_name} claim JSON"
            )
        try:
            return batch_model.model_validate_json(raw_claims)
        except ValidationError as error:
            raise StructuredExtractionOutputError(
                f"Ollama returned schema-invalid {pass_name} claim JSON"
            ) from error

    def preflight(self) -> tuple[bool, bool, str]:
        """Return Ollama reachability, configured-model presence, and a safe detail."""

        try:
            response = self._request_json("/api/tags", None, method="GET")
        except StructuredExtractionError as error:
            return False, False, str(error)
        raw_models = response.get("models", [])
        if not isinstance(raw_models, list):
            return True, False, "Ollama returned an invalid model inventory"
        names: set[str] = set()
        for raw_model in raw_models:
            if not isinstance(raw_model, Mapping):
                continue
            for key in ("name", "model"):
                value = raw_model.get(key)
                if isinstance(value, str):
                    names.add(value)
        available = self.model in names
        detail = (
            "Configured Ollama model is available"
            if available
            else "Configured Ollama model is not installed"
        )
        return True, available, detail

    def _build_prompt(self, request: ExtractionRequest, *, pass_name: str) -> str:
        normalized_transcript = normalize_transcript_line_endings(request.transcript)
        context = {
            "pass": pass_name,
            "source_kind": request.source_kind.value,
            "source_language": request.source_language,
            "project_hints": (
                request.project_hints.model_dump(mode="json", exclude_none=True)
                if request.project_hints
                else None
            ),
            "actor_metadata": (
                request.actor_metadata.model_dump(mode="json") if request.actor_metadata else None
            ),
            "source_transcript": normalized_transcript,
            "source_segments": {
                str(index): segment["source_quote"]
                for index, segment in enumerate(_source_segments(normalized_transcript))
            },
        }
        return (
            "Extract only the claim types authorized for this pass. SOURCE TRANSCRIPT is the "
            "immutable evidence source. PROJECT HINTS and ACTOR METADATA are orientation only and "
            "must never be claimed unless the same fact appears in a supplied SOURCE SEGMENT. "
            "Select one source segment index for every claim. The other pass and its output are "
            "unavailable. Return only directly stated facts, with no placeholders.\n"
            + json.dumps(context, ensure_ascii=False, separators=(",", ":"))
        )

    @staticmethod
    def _expand_claim_proposal(
        proposal: str,
        pass_name: str,
        index: int,
        segments: list[dict[str, object]],
    ) -> GroundedClaim:
        field_names = {
            GroundedClaimType.PROJECT_REQUEST: "request_summary",
            GroundedClaimType.TARGET_APPLICATION: "target_application",
            GroundedClaimType.INDUSTRIAL_FUNCTION: "intended_industrial_function",
            GroundedClaimType.CUSTOMER_REQUIREMENT: "customer_requirements",
            GroundedClaimType.SUCCESS_CRITERION: "success_criteria",
            GroundedClaimType.SUBSTRATE_NAME: "substrate_name",
            GroundedClaimType.SUBSTRATE_TYPE: "substrate_type",
            GroundedClaimType.SUBSTRATE_REASON: "reason_selected",
            GroundedClaimType.MATERIAL: "material_name",
            GroundedClaimType.MATERIAL_AMOUNT: "amount",
            GroundedClaimType.MATERIAL_FUNCTION: "function_in_formulation",
            GroundedClaimType.APPROACH: "title",
            GroundedClaimType.APPROACH_OUTCOME: "outcome",
            GroundedClaimType.APPROACH_FAILURE_REASON: "failure_reason",
            GroundedClaimType.APPROACH_LESSON: "lesson_learned",
            GroundedClaimType.SAMPLE: "sample_description",
            GroundedClaimType.SHIPMENT: "shipment",
            GroundedClaimType.ARCHIVE: "physical_archive_status",
            GroundedClaimType.CUSTOMER_FEEDBACK: "feedback_summary",
            GroundedClaimType.NEXT_ACTION: "current_next_action",
            GroundedClaimType.PRODUCTION_FEASIBILITY: "production_feasibility_status",
            GroundedClaimType.PRICE_OPTIMIZATION: "price_optimization_status",
            GroundedClaimType.REUSE_POTENTIAL: "reuse_potential",
        }
        proposal_type, subject_label, raw_source_segment = proposal.split("|", 2)
        claim_type = GroundedClaimType(proposal_type)
        source_segment = int(raw_source_segment)
        if 0 <= source_segment < len(segments):
            segment = segments[source_segment]
            source_quote = str(segment["source_quote"])
            source_start = cast(int, segment["source_start"])
            source_end = cast(int, segment["source_end"])
        else:
            source_quote = str(segments[0]["source_quote"])
            source_start = -1
            source_end = -1 + len(source_quote)
        subject_label = _subject_label_from_source(claim_type, subject_label, source_quote)
        source_value = _source_value_from_source(claim_type, subject_label, source_quote)
        state = _claim_state_from_source(claim_type, source_quote)
        field_name = field_names.get(claim_type, claim_type.value)
        if claim_type is GroundedClaimType.PROCESS_PARAMETER:
            field_name = _parameter_name_from_source(source_quote)
        elif claim_type in {GroundedClaimType.TEST, GroundedClaimType.TEST_RESULT}:
            field_name = _test_name_from_source(source_value or source_quote)
        numeric_value, unit = _numeric_value_and_unit(claim_type, source_value)
        text_value = source_value if numeric_value is None else None
        return GroundedClaim(
            claim_id=f"{pass_name}-{index:03d}",
            claim_type=claim_type,
            subject_label=subject_label,
            field_name=field_name,
            text_value=text_value,
            numeric_value=numeric_value,
            unit=unit,
            state=state,
            source_quote=source_quote,
            source_start=source_start,
            source_end=source_end,
            model_confidence=0.5,
        )

    def _request_json(
        self,
        path: str,
        payload: dict[str, object] | None,
        *,
        method: str = "POST",
    ) -> dict[str, object]:
        body = None
        headers = {"Accept": "application/json"}
        if payload is not None:
            body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = Request(self.base_url + path, data=body, headers=headers, method=method)
        try:
            with _open_local_request(request, timeout=self.timeout_seconds) as response:
                raw_body = response.read(MAX_OLLAMA_RESPONSE_BYTES + 1)
        except TimeoutError as error:
            raise StructuredExtractionTimeoutError("Local Ollama request timed out") from error
        except HTTPError as error:
            raise StructuredExtractionProviderUnavailableError(
                f"Local Ollama returned HTTP {error.code}"
            ) from error
        except URLError as error:
            if isinstance(error.reason, TimeoutError):
                raise StructuredExtractionTimeoutError("Local Ollama request timed out") from error
            raise StructuredExtractionProviderUnavailableError(
                "Local Ollama is unavailable"
            ) from error
        except OSError as error:
            raise StructuredExtractionProviderUnavailableError(
                "Local Ollama is unavailable"
            ) from error

        if len(raw_body) > MAX_OLLAMA_RESPONSE_BYTES:
            raise StructuredExtractionOutputError("Local Ollama response exceeded the size limit")
        try:
            decoded = json.loads(raw_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise StructuredExtractionOutputError("Local Ollama returned invalid JSON") from error
        if not isinstance(decoded, dict):
            raise StructuredExtractionOutputError("Local Ollama response must be a JSON object")
        return decoded


class DeterministicFakeExtractionProvider:
    """Configurable extraction fake for network-free tests."""

    def __init__(
        self,
        candidate: LabProjectCaptureCandidate | None = None,
        *,
        error: StructuredExtractionError | None = None,
        claim_verifications: tuple[Any, ...] = (),
    ) -> None:
        self.candidate = candidate
        self.error = error
        self.claim_verifications = claim_verifications
        self.calls: list[ExtractionRequest] = []

    def extract(self, request: ExtractionRequest) -> LabProjectCaptureCandidate:
        self.calls.append(request)
        if self.error is not None:
            raise self.error
        candidate = self.candidate or LabProjectCaptureCandidate(
            capture_session_id=request.capture_session_id,
            source_kind=request.source_kind,
            source_language=request.source_language,
            transcript=request.transcript,
            extraction_model="deterministic-fake",
            extraction_started_at=datetime(2026, 8, 6, 8, 0, tzinfo=UTC),
            extraction_completed_at=datetime(2026, 8, 6, 8, 0, tzinfo=UTC),
            project=ProjectIdentity(
                **(
                    request.project_hints.model_dump(exclude_none=True)
                    if request.project_hints
                    else {}
                )
            ),
        )
        if candidate.human_confirmed:
            raise StructuredExtractionOutputError("AI output must remain unconfirmed")
        candidate_payload = candidate.model_dump(mode="json")
        candidate_payload.update(
            {
                "capture_session_id": request.capture_session_id,
                "source_kind": request.source_kind,
                "source_language": request.source_language,
                "transcript": request.transcript,
                "human_confirmed": False,
                "human_confirmed_by": None,
                "human_confirmed_at": None,
            }
        )
        candidate = LabProjectCaptureCandidate.model_validate(candidate_payload)
        return apply_candidate_completeness(candidate)

    def extract_grounded(self, request: ExtractionRequest) -> GroundedExtractionResult:
        return GroundedExtractionResult(
            candidate=self.extract(request),
            claim_verifications=self.claim_verifications,
        )


__all__ = [
    "ActorMetadata",
    "DEFAULT_OLLAMA_TIMEOUT_SECONDS",
    "DeterministicFakeExtractionProvider",
    "ExtractionRequest",
    "MAX_OLLAMA_RESPONSE_BYTES",
    "OllamaStructuredExtractionProvider",
    "ProjectHints",
    "StructuredExtractionConfigurationError",
    "StructuredExtractionError",
    "StructuredExtractionOutputError",
    "StructuredExtractionProvider",
    "StructuredExtractionProviderUnavailableError",
    "StructuredExtractionTimeoutError",
    "SYSTEM_INSTRUCTIONS",
    "assign_candidate_correlation_ids",
    "build_ollama_grammar_schema",
    "normalize_ai_process_parameters",
    "validate_loopback_base_url",
]
