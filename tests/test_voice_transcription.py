from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from smartcoat.services import voice_transcription
from smartcoat.services.voice_transcription import (
    DeterministicFakeTranscriptionProvider,
    MlxWhisperTranscriptionProvider,
    TranscriptionProviderUnavailableError,
    TranscriptionResult,
)


def _result() -> TranscriptionResult:
    return TranscriptionResult(
        transcript="Synthetic local transcript.",
        detected_language="en",
        duration_seconds=2.5,
        provider="deterministic-fake",
        model="test-model",
    )


def test_deterministic_fake_transcription_provider() -> None:
    provider = DeterministicFakeTranscriptionProvider(_result())

    result = provider.transcribe(
        b"synthetic-audio",
        filename="capture.wav",
        media_type="audio/wav",
    )

    assert result == _result()
    assert provider.calls == [(b"synthetic-audio", "capture.wav", "audio/wav")]


def test_mlx_whisper_is_loaded_dynamically_and_temporary_audio_is_deleted(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    observed_path: Path | None = None

    def transcribe(filename: str, *, path_or_hf_repo: str) -> dict[str, object]:
        nonlocal observed_path
        observed_path = Path(filename)
        assert observed_path.is_file()
        assert observed_path.read_bytes() == b"synthetic-audio"
        assert path_or_hf_repo == "local-whisper-model"
        return {
            "text": "  Synthetic transcript.  ",
            "language": "en",
            "segments": [{"end": 3.75}],
        }

    monkeypatch.setattr(
        voice_transcription.importlib,
        "import_module",
        lambda name: SimpleNamespace(transcribe=transcribe),
    )
    provider = MlxWhisperTranscriptionProvider(
        "local-whisper-model",
        temporary_directory=tmp_path,
    )

    result = provider.transcribe(
        b"synthetic-audio",
        filename="capture.wav",
        media_type="audio/wav",
    )

    assert result.transcript == "Synthetic transcript."
    assert result.detected_language == "en"
    assert result.duration_seconds == 3.75
    assert result.metadata == {"temporary_audio_deleted": True}
    assert observed_path is not None
    assert not observed_path.exists()
    assert list(tmp_path.iterdir()) == []


def test_mlx_whisper_unavailable_is_clear_and_does_not_create_audio(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    def unavailable(name: str) -> object:
        raise ModuleNotFoundError(name)

    monkeypatch.setattr(voice_transcription.importlib, "import_module", unavailable)
    provider = MlxWhisperTranscriptionProvider("local-model", temporary_directory=tmp_path)

    with pytest.raises(TranscriptionProviderUnavailableError, match="not installed"):
        provider.transcribe(b"audio", filename="capture.wav", media_type="audio/wav")

    assert list(tmp_path.iterdir()) == []


def test_temporary_audio_is_deleted_when_mlx_transcription_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    observed_path: Path | None = None

    def fail(filename: str, *, path_or_hf_repo: str) -> object:
        nonlocal observed_path
        del path_or_hf_repo
        observed_path = Path(filename)
        raise RuntimeError("synthetic model failure")

    monkeypatch.setattr(
        voice_transcription.importlib,
        "import_module",
        lambda name: SimpleNamespace(transcribe=fail),
    )
    provider = MlxWhisperTranscriptionProvider("local-model", temporary_directory=tmp_path)

    with pytest.raises(TranscriptionProviderUnavailableError, match="could not load"):
        provider.transcribe(b"audio", filename="capture.wav", media_type="audio/wav")

    assert observed_path is not None
    assert not observed_path.exists()
    assert list(tmp_path.iterdir()) == []


def test_mlx_preflight_does_not_download_a_model(monkeypatch: pytest.MonkeyPatch) -> None:
    imported: list[str] = []

    def import_module(name: str) -> object:
        imported.append(name)
        return object()

    monkeypatch.setattr(voice_transcription.importlib, "import_module", import_module)

    ready, detail = voice_transcription.mlx_whisper_import_ready()

    assert ready is True
    assert detail == "MLX Whisper import succeeded"
    assert imported == ["mlx_whisper"]
