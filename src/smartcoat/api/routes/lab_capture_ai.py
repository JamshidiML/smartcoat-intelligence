"""Local-only AI endpoints for unconfirmed lab-project intake Candidates."""

from __future__ import annotations

import os
import re
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, model_validator
from starlette.concurrency import run_in_threadpool

from smartcoat.core.config import Settings, get_settings
from smartcoat.domain.lab_project_capture import (
    CaptureSourceKind,
    LabProjectCaptureCandidate,
)
from smartcoat.services.lab_project_extraction import (
    ActorMetadata,
    ExtractionRequest,
    OllamaStructuredExtractionProvider,
    ProjectHints,
    StructuredExtractionConfigurationError,
    StructuredExtractionOutputError,
    StructuredExtractionProvider,
    StructuredExtractionProviderUnavailableError,
    StructuredExtractionTimeoutError,
)
from smartcoat.services.voice_transcription import (
    MlxWhisperTranscriptionProvider,
    TranscriptionError,
    TranscriptionProvider,
    TranscriptionProviderUnavailableError,
    TranscriptionResult,
    mlx_whisper_import_ready,
)

PILOT_ORGANIZATION_ID = "smartcoat-startup"
APPROVED_AUDIO_MEDIA_TYPES = frozenset(
    {
        "audio/aac",
        "audio/flac",
        "audio/m4a",
        "audio/mp4",
        "audio/mpeg",
        "audio/ogg",
        "audio/wav",
        "audio/webm",
        "audio/x-m4a",
        "audio/x-wav",
    }
)


class ReadinessCheck(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    ready: bool
    detail: str = Field(min_length=1, max_length=512)


class LocalAIPreflightResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    ready: bool
    mlx_whisper_import: ReadinessCheck
    whisper_model: ReadinessCheck
    ollama_reachability: ReadinessCheck
    ollama_model: ReadinessCheck
    asset_directory: ReadinessCheck


class ExtractTextRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    transcript: str | None = Field(default=None, min_length=1, max_length=4096)
    free_text: str | None = Field(default=None, min_length=1, max_length=4096)
    project_hints: ProjectHints | None = None
    actor_metadata: ActorMetadata
    source_language: str | None = Field(default=None, min_length=2, max_length=35)

    @model_validator(mode="after")
    def require_one_text_source(self) -> ExtractTextRequest:
        if (self.transcript is None) == (self.free_text is None):
            raise ValueError("Provide exactly one of transcript or free_text")
        return self

    @property
    def source_text(self) -> str:
        return self.transcript if self.transcript is not None else self.free_text or ""


class CandidateExtractionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    candidate: LabProjectCaptureCandidate
    completeness_score: int = Field(ge=0, le=100)
    missing_fields: tuple[str, ...]
    follow_up_questions: tuple[str, ...]
    extraction_warnings: tuple[str, ...]
    transcription: TranscriptionResult | None = None


def get_transcription_provider() -> TranscriptionProvider:
    settings = get_settings()
    if settings.voice_transcription_backend != "mlx_whisper":
        raise HTTPException(status_code=503, detail="Local transcription backend is unavailable")
    try:
        return MlxWhisperTranscriptionProvider(settings.whisper_model)
    except ValueError as error:
        raise HTTPException(
            status_code=503,
            detail="Local transcription backend is not safely configured",
        ) from error


def get_structured_extraction_provider() -> StructuredExtractionProvider:
    settings = get_settings()
    try:
        return OllamaStructuredExtractionProvider(
            settings.ollama_base_url,
            settings.ollama_model,
        )
    except StructuredExtractionConfigurationError as error:
        raise HTTPException(
            status_code=503,
            detail="Local extraction provider is not safely configured",
        ) from error


def build_preflight_response(settings: Settings | None = None) -> LocalAIPreflightResponse:
    """Inspect local dependencies without downloading models or retaining content."""

    current_settings = settings or get_settings()
    whisper_import_ready, whisper_import_detail = mlx_whisper_import_ready()
    whisper_model_ready = bool(current_settings.whisper_model.strip())
    whisper_backend_ready = current_settings.voice_transcription_backend == "mlx_whisper"
    whisper_model_detail = (
        "Whisper model is configured"
        if whisper_model_ready and whisper_backend_ready
        else "Whisper model or local backend is not configured"
    )

    ollama_reachable = False
    ollama_model_ready = False
    try:
        ollama = OllamaStructuredExtractionProvider(
            current_settings.ollama_base_url,
            current_settings.ollama_model,
            timeout_seconds=2.0,
        )
        ollama_reachable, ollama_model_ready, ollama_detail = ollama.preflight()
    except StructuredExtractionConfigurationError:
        ollama_detail = "Ollama is not safely configured for loopback-only access"

    asset_root = current_settings.asset_root.expanduser()
    asset_ready = asset_root.is_dir() and os.access(asset_root, os.R_OK | os.W_OK | os.X_OK)
    asset_detail = (
        "Asset directory exists and is accessible"
        if asset_ready
        else "Asset directory is missing or inaccessible"
    )
    checks = (
        whisper_import_ready,
        whisper_model_ready and whisper_backend_ready,
        ollama_reachable,
        ollama_model_ready,
        asset_ready,
    )
    return LocalAIPreflightResponse(
        ready=all(checks),
        mlx_whisper_import=ReadinessCheck(
            ready=whisper_import_ready,
            detail=whisper_import_detail,
        ),
        whisper_model=ReadinessCheck(
            ready=whisper_model_ready and whisper_backend_ready,
            detail=whisper_model_detail,
        ),
        ollama_reachability=ReadinessCheck(
            ready=ollama_reachable,
            detail=("Local Ollama is reachable" if ollama_reachable else ollama_detail),
        ),
        ollama_model=ReadinessCheck(
            ready=ollama_model_ready,
            detail=(
                "Configured Ollama model is available"
                if ollama_model_ready
                else "Configured Ollama model is unavailable"
            ),
        ),
        asset_directory=ReadinessCheck(ready=asset_ready, detail=asset_detail),
    )


def _candidate_response(
    candidate: LabProjectCaptureCandidate,
    *,
    transcription: TranscriptionResult | None = None,
) -> CandidateExtractionResponse:
    if candidate.human_confirmed:
        raise HTTPException(status_code=502, detail="AI Candidate must remain unconfirmed")
    return CandidateExtractionResponse(
        candidate=candidate,
        completeness_score=candidate.completeness_score,
        missing_fields=candidate.critical_missing_fields,
        follow_up_questions=candidate.recommended_questions,
        extraction_warnings=candidate.extraction_warnings,
        transcription=transcription,
    )


def _extract_candidate(
    provider: StructuredExtractionProvider,
    extraction_request: ExtractionRequest,
) -> LabProjectCaptureCandidate:
    try:
        return provider.extract(extraction_request)
    except StructuredExtractionTimeoutError as error:
        raise HTTPException(
            status_code=504, detail="Local extraction provider timed out"
        ) from error
    except StructuredExtractionProviderUnavailableError as error:
        raise HTTPException(
            status_code=503, detail="Local extraction provider is unavailable"
        ) from error
    except StructuredExtractionOutputError as error:
        raise HTTPException(
            status_code=502, detail="Local extraction provider returned invalid output"
        ) from error


def _sanitize_filename(filename: str) -> str:
    leaf_name = filename.replace("\\", "/").split("/")[-1].strip()
    if not leaf_name or "\x00" in leaf_name:
        raise HTTPException(status_code=422, detail="X-SmartCoat-Filename is invalid")
    sanitized = re.sub(r"[^A-Za-z0-9._-]", "_", leaf_name).strip("._")
    if not sanitized:
        raise HTTPException(status_code=422, detail="X-SmartCoat-Filename is invalid")
    return sanitized[:255]


async def _read_limited_body(request: Request, maximum_bytes: int) -> bytes:
    if maximum_bytes <= 0:
        raise HTTPException(status_code=503, detail="Audio upload limit is not safely configured")
    content_length = request.headers.get("content-length")
    if content_length is not None:
        try:
            declared_length = int(content_length)
        except ValueError as error:
            raise HTTPException(status_code=400, detail="Content-Length is invalid") from error
        if declared_length < 0:
            raise HTTPException(status_code=400, detail="Content-Length is invalid")
        if declared_length > maximum_bytes:
            raise HTTPException(status_code=413, detail="Audio upload exceeds configured limit")

    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > maximum_bytes:
            raise HTTPException(status_code=413, detail="Audio upload exceeds configured limit")
    if not body:
        raise HTTPException(status_code=422, detail="Audio body must not be empty")
    return bytes(body)


router = APIRouter(prefix="/api/v2/lab-capture", tags=["lab-capture-ai"])


@router.get("/preflight", response_model=LocalAIPreflightResponse)
def local_ai_preflight() -> LocalAIPreflightResponse:
    return build_preflight_response()


@router.post("/extract-text", response_model=CandidateExtractionResponse)
def extract_text(
    payload: ExtractTextRequest,
    provider: Annotated[StructuredExtractionProvider, Depends(get_structured_extraction_provider)],
) -> CandidateExtractionResponse:
    candidate = _extract_candidate(
        provider,
        ExtractionRequest(
            transcript=payload.source_text,
            source_kind=CaptureSourceKind.TEXT,
            source_language=payload.source_language,
            project_hints=payload.project_hints,
            actor_metadata=payload.actor_metadata,
        ),
    )
    return _candidate_response(candidate)


@router.post("/process-audio", response_model=CandidateExtractionResponse)
async def process_audio(
    request: Request,
    content_type: Annotated[str, Header(alias="Content-Type")],
    filename: Annotated[
        str,
        Header(alias="X-SmartCoat-Filename", min_length=1, max_length=512),
    ],
    organization_id: Annotated[
        str,
        Header(alias="X-SmartCoat-Organization-ID", min_length=1, max_length=512),
    ],
    transcription_provider: Annotated[
        TranscriptionProvider,
        Depends(get_transcription_provider),
    ],
    extraction_provider: Annotated[
        StructuredExtractionProvider,
        Depends(get_structured_extraction_provider),
    ],
) -> CandidateExtractionResponse:
    normalized_media_type = content_type.partition(";")[0].strip().casefold()
    if normalized_media_type not in APPROVED_AUDIO_MEDIA_TYPES:
        raise HTTPException(status_code=415, detail="Unsupported audio media type")
    if organization_id.strip() != PILOT_ORGANIZATION_ID:
        raise HTTPException(status_code=403, detail="Pilot organization is not authorized")

    safe_filename = _sanitize_filename(filename)
    settings = get_settings()
    audio = await _read_limited_body(request, settings.max_upload_bytes)
    try:
        transcription = await run_in_threadpool(
            transcription_provider.transcribe,
            audio,
            filename=safe_filename,
            media_type=normalized_media_type,
        )
    except TranscriptionProviderUnavailableError as error:
        raise HTTPException(
            status_code=503, detail="Local transcription provider is unavailable"
        ) from error
    except TranscriptionError as error:
        raise HTTPException(status_code=502, detail="Local transcription failed") from error

    candidate = await run_in_threadpool(
        _extract_candidate,
        extraction_provider,
        ExtractionRequest(
            transcript=transcription.transcript,
            source_kind=CaptureSourceKind.VOICE,
            source_language=transcription.detected_language,
        ),
    )
    return _candidate_response(candidate, transcription=transcription)


__all__ = [
    "APPROVED_AUDIO_MEDIA_TYPES",
    "CandidateExtractionResponse",
    "ExtractTextRequest",
    "LocalAIPreflightResponse",
    "PILOT_ORGANIZATION_ID",
    "ReadinessCheck",
    "build_preflight_response",
    "get_structured_extraction_provider",
    "get_transcription_provider",
    "router",
]
