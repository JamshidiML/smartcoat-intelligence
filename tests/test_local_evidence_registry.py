from __future__ import annotations

import hashlib
import io
import os
import stat
from datetime import UTC, datetime
from pathlib import Path

import pytest

from smartcoat.domain.lab_project_capture import EvidenceType
from smartcoat.services.local_evidence_registry import (
    EvidenceRegistryError,
    LocalEvidenceRegistry,
)

NOW = datetime(2026, 8, 6, 10, 0, tzinfo=UTC)
PDF_CONTENT = b"%PDF-1.7\n% synthetic pilot evidence\n%%EOF\n"
PNG_CONTENT = b"\x89PNG\r\n\x1a\n" + b"synthetic-image"
M4A_CONTENT = b"\x00\x00\x00\x18ftypM4A " + b"synthetic-audio"


def _registry(root: Path, max_upload_bytes: int = 1024) -> LocalEvidenceRegistry:
    return LocalEvidenceRegistry(root, max_upload_bytes, clock=lambda: NOW)


def test_streaming_sha256_content_addressing_and_descriptor_has_no_path(tmp_path: Path) -> None:
    registry = _registry(tmp_path / "assets")

    descriptor = registry.register_chunks(
        (PDF_CONTENT[:7], PDF_CONTENT[7:21], PDF_CONTENT[21:]),
        organization_id="  Synthetic-Lab  ",
        original_filename="report.pdf",
        media_type="application/pdf",
    )

    expected_sha = hashlib.sha256(PDF_CONTENT).hexdigest()
    assert descriptor.sha256 == expected_sha
    assert descriptor.evidence_type is EvidenceType.PDF
    assert descriptor.source_reference == f"smartcoat-asset://synthetic-lab/{expected_sha}"
    assert descriptor.captured_at == NOW
    assert descriptor.duplicate is False
    assert descriptor.size_bytes == len(PDF_CONTENT)
    assert "path" not in descriptor.model_dump()

    stored = tmp_path / "assets" / "synthetic-lab" / expected_sha[:2] / expected_sha
    assert stored.read_bytes() == PDF_CONTENT
    if os.name == "posix":
        assert stat.S_IMODE(stored.stat().st_mode) == 0o600
        assert stat.S_IMODE(stored.parent.stat().st_mode) == 0o700
        assert stat.S_IMODE(stored.parent.parent.stat().st_mode) == 0o700


def test_duplicate_is_safe_and_does_not_overwrite(tmp_path: Path) -> None:
    registry = _registry(tmp_path / "assets")
    first = registry.register_stream(
        io.BytesIO(PDF_CONTENT),
        organization_id="synthetic-lab",
        original_filename="first.pdf",
        media_type="application/pdf",
    )
    second = registry.register_stream(
        io.BytesIO(PDF_CONTENT),
        organization_id="synthetic-lab",
        original_filename="second.pdf",
        media_type="application/pdf",
    )

    assert first.evidence_id == second.evidence_id
    assert first.duplicate is False
    assert second.duplicate is True
    assert second.original_filename == "second.pdf"
    with registry.open_content(organization_id="synthetic-lab", sha256=first.sha256) as stream:
        assert stream.read() == PDF_CONTENT


def test_organization_partitioning_uses_distinct_assets(tmp_path: Path) -> None:
    registry = _registry(tmp_path / "assets")
    first = registry.register_stream(
        io.BytesIO(PNG_CONTENT),
        organization_id="org-one",
        original_filename="image.png",
        media_type="image/png",
    )
    second = registry.register_stream(
        io.BytesIO(PNG_CONTENT),
        organization_id="org-two",
        original_filename="image.png",
        media_type="image/png",
    )

    assert first.sha256 == second.sha256
    assert first.evidence_id != second.evidence_id
    assert (tmp_path / "assets" / "org-one" / first.sha256[:2] / first.sha256).is_file()
    assert (tmp_path / "assets" / "org-two" / first.sha256[:2] / first.sha256).is_file()


def test_pilot_m4a_media_type_is_registered_as_audio(tmp_path: Path) -> None:
    descriptor = _registry(tmp_path / "assets").register_stream(
        io.BytesIO(M4A_CONTENT),
        organization_id="synthetic-lab",
        original_filename="voice-note.m4a",
        media_type="audio/m4a",
    )

    assert descriptor.evidence_type is EvidenceType.AUDIO
    assert descriptor.media_type == "audio/m4a"


def test_unsafe_filename_is_metadata_only_and_cannot_escape(tmp_path: Path) -> None:
    root = tmp_path / "assets"
    descriptor = _registry(root).register_stream(
        io.BytesIO(PDF_CONTENT),
        organization_id="synthetic-lab",
        original_filename="../../outside.pdf",
        media_type="application/pdf",
    )

    assert descriptor.original_filename == "../../outside.pdf"
    assert not (tmp_path / "outside.pdf").exists()
    assert (root / "synthetic-lab" / descriptor.sha256[:2] / descriptor.sha256).is_file()


def test_oversized_empty_unsupported_and_signature_mismatch_are_rejected(tmp_path: Path) -> None:
    registry = _registry(tmp_path / "assets", max_upload_bytes=16)

    with pytest.raises(EvidenceRegistryError, match="maximum upload size") as oversized:
        registry.register_stream(
            io.BytesIO(PDF_CONTENT),
            organization_id="synthetic-lab",
            original_filename="large.pdf",
            media_type="application/pdf",
        )
    assert oversized.value.code == "asset_too_large"

    with pytest.raises(EvidenceRegistryError, match="must not be empty") as empty:
        registry.register_stream(
            io.BytesIO(b""),
            organization_id="synthetic-lab",
            original_filename="empty.pdf",
            media_type="application/pdf",
        )
    assert empty.value.code == "empty_asset"

    with pytest.raises(EvidenceRegistryError, match="not allowed") as unsupported:
        registry.register_stream(
            io.BytesIO(b"text"),
            organization_id="synthetic-lab",
            original_filename="notes.txt",
            media_type="text/plain",
        )
    assert unsupported.value.code == "unsupported_media_type"

    with pytest.raises(EvidenceRegistryError, match="does not match") as mismatch:
        _registry(tmp_path / "other").register_stream(
            io.BytesIO(b"not a pdf"),
            organization_id="synthetic-lab",
            original_filename="fake.pdf",
            media_type="application/pdf",
        )
    assert mismatch.value.code == "media_signature_mismatch"


@pytest.mark.parametrize(
    "organization_id",
    ["../other", "org/path", "org\\path", "", ".hidden", "two words"],
)
def test_invalid_organization_ids_are_rejected(tmp_path: Path, organization_id: str) -> None:
    with pytest.raises(EvidenceRegistryError) as captured:
        _registry(tmp_path / "assets").register_stream(
            io.BytesIO(PDF_CONTENT),
            organization_id=organization_id,
            original_filename="report.pdf",
            media_type="application/pdf",
        )
    assert captured.value.code == "invalid_organization_id"
