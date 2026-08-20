"""Local-only transcription providers for the voice intake pilot."""

from __future__ import annotations

import importlib
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field


class TranscriptionError(RuntimeError):
    """Base error for expected transcription failures."""


class TranscriptionProviderUnavailableError(TranscriptionError):
    """Raised when the configured local provider cannot run."""


class TranscriptionResult(BaseModel):
    """Normalized output from a local transcription provider."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    transcript: str = Field(min_length=1, max_length=4096)
    detected_language: str | None = Field(default=None, min_length=2, max_length=35)
    duration_seconds: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    provider: str = Field(min_length=1, max_length=128)
    model: str = Field(min_length=1, max_length=512)
    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


class TranscriptionProvider(Protocol):
    """Contract for audio-to-text providers used by the pilot."""

    def transcribe(
        self,
        audio: bytes,
        *,
        filename: str,
        media_type: str,
    ) -> TranscriptionResult: ...


def _optional_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _optional_duration(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    duration = float(value)
    return duration if duration >= 0 else None


class MlxWhisperTranscriptionProvider:
    """Dynamically load MLX Whisper and transcribe through a temporary file."""

    provider_name = "mlx_whisper"

    def __init__(self, model: str, *, temporary_directory: Path | None = None) -> None:
        normalized_model = model.strip()
        if not normalized_model:
            raise ValueError("Whisper model must not be blank")
        self.model = normalized_model
        self.temporary_directory = temporary_directory

    def transcribe(
        self,
        audio: bytes,
        *,
        filename: str,
        media_type: str,
    ) -> TranscriptionResult:
        del media_type
        if not audio:
            raise TranscriptionError("Audio body must not be empty")

        suffix = Path(filename).suffix[:16]
        temporary_path: Path | None = None
        try:
            try:
                mlx_whisper = importlib.import_module("mlx_whisper")
            except (ImportError, ModuleNotFoundError) as error:
                raise TranscriptionProviderUnavailableError(
                    "MLX Whisper is not installed in the local pilot environment"
                ) from error

            with tempfile.NamedTemporaryFile(
                mode="wb",
                suffix=suffix,
                prefix="smartcoat-voice-",
                dir=self.temporary_directory,
                delete=False,
            ) as temporary_file:
                temporary_file.write(audio)
                temporary_path = Path(temporary_file.name)

            try:
                raw_result = mlx_whisper.transcribe(
                    str(temporary_path),
                    path_or_hf_repo=self.model,
                )
            except Exception as error:
                raise TranscriptionProviderUnavailableError(
                    "MLX Whisper could not load the configured local model or transcribe audio"
                ) from error

            if not isinstance(raw_result, Mapping):
                raise TranscriptionError("MLX Whisper returned an invalid response")
            transcript = _optional_text(raw_result.get("text"))
            if transcript is None:
                raise TranscriptionError("MLX Whisper returned an empty transcript")

            language = _optional_text(raw_result.get("language"))
            duration = _optional_duration(raw_result.get("duration"))
            if duration is None:
                segments = raw_result.get("segments")
                if isinstance(segments, list) and segments:
                    last_segment = segments[-1]
                    if isinstance(last_segment, Mapping):
                        duration = _optional_duration(last_segment.get("end"))

            return TranscriptionResult(
                transcript=transcript,
                detected_language=language,
                duration_seconds=duration,
                provider=self.provider_name,
                model=self.model,
                metadata={"temporary_audio_deleted": True},
            )
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)


class DeterministicFakeTranscriptionProvider:
    """Configurable fake that never loads a model or reads the network."""

    def __init__(
        self,
        result: TranscriptionResult,
        *,
        error: TranscriptionError | None = None,
    ) -> None:
        self.result = result
        self.error = error
        self.calls: list[tuple[bytes, str, str]] = []

    def transcribe(
        self,
        audio: bytes,
        *,
        filename: str,
        media_type: str,
    ) -> TranscriptionResult:
        self.calls.append((audio, filename, media_type))
        if self.error is not None:
            raise self.error
        return self.result


def mlx_whisper_import_ready() -> tuple[bool, str]:
    """Check the optional package without loading or downloading a speech model."""

    try:
        importlib.import_module("mlx_whisper")
    except (ImportError, ModuleNotFoundError):
        return False, "MLX Whisper is not installed"
    except Exception:
        return False, "MLX Whisper could not be imported"
    return True, "MLX Whisper import succeeded"


__all__ = [
    "DeterministicFakeTranscriptionProvider",
    "MlxWhisperTranscriptionProvider",
    "TranscriptionError",
    "TranscriptionProvider",
    "TranscriptionProviderUnavailableError",
    "TranscriptionResult",
    "mlx_whisper_import_ready",
]
