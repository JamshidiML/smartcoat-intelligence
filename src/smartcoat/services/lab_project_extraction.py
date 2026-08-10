"""Local structured extraction providers for lab-project capture candidates."""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import UTC, datetime
from http.client import HTTPMessage
from ipaddress import ip_address
from typing import IO, Any, Protocol
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

SYSTEM_INSTRUCTIONS = """You extract an unapproved SmartCoat lab-project intake Candidate.
Return only JSON matching the supplied schema. Never invent domain facts or source
identifiers. Candidate-local correlation IDs may be assigned using the deterministic
C-M/C-A/C-S convention solely to connect Candidate sections. If the source provides an
identifier, preserve it separately as the source identifier. Use explicit missing,
unknown, not_measured, not_applicable, or conflicting states. Preserve technical units.
Keep measured facts separate from interpretations. Include source excerpts or transcript
anchors when possible. Add focused questions for material missing information. Never set
human_confirmed to true and never add human confirmation metadata."""

MAX_OLLAMA_RESPONSE_BYTES = 2 * 1024 * 1024


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

    def extract(self, request: ExtractionRequest) -> LabProjectCaptureCandidate: ...


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


class OllamaStructuredExtractionProvider:
    """Extract Candidates through Ollama's local standard-library HTTP API."""

    provider_name = "ollama"

    def __init__(self, base_url: str, model: str, *, timeout_seconds: float = 60.0) -> None:
        self.base_url = validate_loopback_base_url(base_url)
        normalized_model = model.strip()
        if not normalized_model:
            raise StructuredExtractionConfigurationError("Ollama model must not be blank")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self.model = normalized_model
        self.timeout_seconds = timeout_seconds

    def extract(self, request: ExtractionRequest) -> LabProjectCaptureCandidate:
        started_at = datetime.now(UTC)
        payload = {
            "model": self.model,
            "system": SYSTEM_INSTRUCTIONS,
            "prompt": self._build_prompt(request),
            "format": LabProjectCaptureCandidate.model_json_schema(),
            "stream": False,
            "options": {"temperature": 0},
        }
        response = self._request_json("/api/generate", payload)
        raw_candidate = response.get("response")
        if not isinstance(raw_candidate, str):
            raise StructuredExtractionOutputError("Ollama response did not contain Candidate JSON")
        try:
            candidate_payload = json.loads(raw_candidate)
        except json.JSONDecodeError as error:
            raise StructuredExtractionOutputError(
                "Ollama returned invalid Candidate JSON"
            ) from error
        if not isinstance(candidate_payload, dict):
            raise StructuredExtractionOutputError("Ollama Candidate JSON must be an object")
        if candidate_payload.get("human_confirmed") is True:
            raise StructuredExtractionOutputError("AI output attempted to claim human confirmation")
        if candidate_payload.get("human_confirmed_by") is not None:
            raise StructuredExtractionOutputError("AI output included human confirmation metadata")
        if candidate_payload.get("human_confirmed_at") is not None:
            raise StructuredExtractionOutputError("AI output included human confirmation metadata")

        completed_at = datetime.now(UTC)
        candidate_payload = assign_candidate_correlation_ids(candidate_payload)
        candidate_payload.update(
            {
                "capture_session_id": str(request.capture_session_id),
                "source_kind": request.source_kind.value,
                "source_language": request.source_language,
                "transcript": request.transcript,
                "extraction_model": f"{self.provider_name}:{self.model}",
                "extraction_started_at": started_at.isoformat(),
                "extraction_completed_at": completed_at.isoformat(),
                "human_confirmed": False,
                "human_confirmed_by": None,
                "human_confirmed_at": None,
            }
        )
        try:
            candidate = LabProjectCaptureCandidate.model_validate(candidate_payload)
        except ValidationError as error:
            raise StructuredExtractionOutputError(
                "Ollama returned schema-invalid Candidate JSON"
            ) from error
        return apply_candidate_completeness(candidate)

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

    def _build_prompt(self, request: ExtractionRequest) -> str:
        context = {
            "capture_session_id": str(request.capture_session_id),
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
            "source_transcript": request.transcript,
            "human_review_supplement": request.supplemental_context,
        }
        return (
            "Extract one LabProjectCaptureCandidate from this JSON context. SOURCE TRANSCRIPT is "
            "immutable source text. HUMAN REVIEW SUPPLEMENT is reviewer context and must not be "
            "copied into Candidate.transcript. Actor metadata is context only and must never be "
            "treated as human confirmation.\n"
            + json.dumps(context, ensure_ascii=False, separators=(",", ":"))
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
    ) -> None:
        self.candidate = candidate
        self.error = error
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


__all__ = [
    "ActorMetadata",
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
    "validate_loopback_base_url",
]
