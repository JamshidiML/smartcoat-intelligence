"""Private, organization-partitioned evidence storage for the local pilot."""

from __future__ import annotations

import codecs
import hashlib
import os
import re
import tempfile
import zipfile
from collections.abc import AsyncIterable, Callable, Iterable, Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import BinaryIO
from uuid import NAMESPACE_URL, uuid5

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from smartcoat.domain.lab_project_capture import EvidenceDescriptor, EvidenceType

CHUNK_SIZE = 64 * 1024
ORGANIZATION_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9._-]{0,126}[a-z0-9])?$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
EVIDENCE_NAMESPACE = uuid5(NAMESPACE_URL, "urn:smartcoat:local-evidence:v1")

MEDIA_TYPES: dict[str, EvidenceType] = {
    "text/plain": EvidenceType.TRANSCRIPT,
    "application/pdf": EvidenceType.PDF,
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": EvidenceType.EXCEL,
    "image/png": EvidenceType.IMAGE,
    "image/jpeg": EvidenceType.IMAGE,
    "image/webp": EvidenceType.IMAGE,
    "audio/aac": EvidenceType.AUDIO,
    "audio/flac": EvidenceType.AUDIO,
    "audio/m4a": EvidenceType.AUDIO,
    "audio/mp4": EvidenceType.AUDIO,
    "audio/mpeg": EvidenceType.AUDIO,
    "audio/ogg": EvidenceType.AUDIO,
    "audio/wav": EvidenceType.AUDIO,
    "audio/webm": EvidenceType.AUDIO,
    "audio/x-m4a": EvidenceType.AUDIO,
    "audio/x-wav": EvidenceType.AUDIO,
    "video/webm": EvidenceType.AUDIO,
}


class EvidenceRegistryError(ValueError):
    """A bounded validation or storage failure with an API-safe code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class LocalEvidenceDescriptor(BaseModel):
    """Public evidence metadata; deliberately contains no filesystem path."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    evidence_id: str = Field(min_length=1, max_length=256)
    evidence_type: EvidenceType
    original_filename: str = Field(min_length=1, max_length=512)
    media_type: str = Field(min_length=1, max_length=256)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_reference: str = Field(min_length=1, max_length=512)
    captured_at: AwareDatetime
    duplicate: bool
    size_bytes: int = Field(ge=1)

    def as_candidate_evidence(self) -> EvidenceDescriptor:
        return EvidenceDescriptor(
            evidence_id=self.evidence_id,
            evidence_type=self.evidence_type,
            filename=self.original_filename,
            media_type=self.media_type,
            source_reference=self.source_reference,
            sha256=self.sha256,
            captured_at=self.captured_at,
        )


def normalize_organization_id(value: str) -> str:
    """Normalize a tenant boundary without permitting path syntax."""

    normalized = value.strip().casefold()
    if not ORGANIZATION_PATTERN.fullmatch(normalized):
        raise EvidenceRegistryError(
            "invalid_organization_id",
            (
                "Organization ID must use 1-128 lowercase letters, digits, dots, "
                "underscores, or hyphens"
            ),
        )
    return normalized


def normalize_media_type(value: str) -> str:
    normalized = value.partition(";")[0].strip().casefold()
    if normalized not in MEDIA_TYPES:
        raise EvidenceRegistryError("unsupported_media_type", "Media type is not allowed")
    return normalized


def validate_original_filename(value: str) -> str:
    """Retain the supplied name as metadata, never as a path component."""

    normalized = value.strip()
    if not normalized or len(normalized) > 512:
        raise EvidenceRegistryError("invalid_filename", "Filename must contain 1-512 characters")
    if any(ord(character) < 32 or ord(character) == 127 for character in normalized):
        raise EvidenceRegistryError("invalid_filename", "Filename contains control characters")
    return normalized


class LocalEvidenceRegistry:
    """Stream assets into private content-addressed storage.

    Asset locations are derived only from a validated organization ID and the
    computed digest. Original filenames never participate in path construction.
    """

    def __init__(
        self,
        asset_root: Path,
        max_upload_bytes: int,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if max_upload_bytes < 1:
            raise ValueError("max_upload_bytes must be positive")
        self.asset_root = asset_root.expanduser().resolve(strict=False)
        self.max_upload_bytes = max_upload_bytes
        self._clock = clock or (lambda: datetime.now(UTC))
        self._secure_directory(self.asset_root)

    def register_stream(
        self,
        stream: BinaryIO,
        *,
        organization_id: str,
        original_filename: str,
        media_type: str,
    ) -> LocalEvidenceDescriptor:
        def chunks() -> Iterator[bytes]:
            while chunk := stream.read(CHUNK_SIZE):
                yield chunk

        return self.register_chunks(
            chunks(),
            organization_id=organization_id,
            original_filename=original_filename,
            media_type=media_type,
        )

    def register_chunks(
        self,
        chunks: Iterable[bytes],
        *,
        organization_id: str,
        original_filename: str,
        media_type: str,
    ) -> LocalEvidenceDescriptor:
        organization = normalize_organization_id(organization_id)
        filename = validate_original_filename(original_filename)
        normalized_media_type = normalize_media_type(media_type)
        temporary_path = self._new_staging_path(organization)
        try:
            digest, size_bytes = self._write_chunks(temporary_path, chunks)
            return self._finalize(
                temporary_path,
                organization=organization,
                original_filename=filename,
                media_type=normalized_media_type,
                digest=digest,
                size_bytes=size_bytes,
            )
        finally:
            temporary_path.unlink(missing_ok=True)

    async def register_async(
        self,
        chunks: AsyncIterable[bytes],
        *,
        organization_id: str,
        original_filename: str,
        media_type: str,
    ) -> LocalEvidenceDescriptor:
        organization = normalize_organization_id(organization_id)
        filename = validate_original_filename(original_filename)
        normalized_media_type = normalize_media_type(media_type)
        temporary_path = self._new_staging_path(organization)
        digest = hashlib.sha256()
        size_bytes = 0
        try:
            with temporary_path.open("wb") as destination:
                os.chmod(temporary_path, 0o600)
                async for chunk in chunks:
                    size_bytes = self._consume_chunk(destination, digest, size_bytes, chunk)
                destination.flush()
                os.fsync(destination.fileno())
            if size_bytes == 0:
                raise EvidenceRegistryError("empty_asset", "Asset body must not be empty")
            return self._finalize(
                temporary_path,
                organization=organization,
                original_filename=filename,
                media_type=normalized_media_type,
                digest=digest.hexdigest(),
                size_bytes=size_bytes,
            )
        finally:
            temporary_path.unlink(missing_ok=True)

    @contextmanager
    def open_content(self, *, organization_id: str, sha256: str) -> Iterator[BinaryIO]:
        """Open a known digest within one organization without exposing its path."""

        organization = normalize_organization_id(organization_id)
        if not SHA256_PATTERN.fullmatch(sha256):
            raise EvidenceRegistryError("invalid_sha256", "SHA-256 must be lowercase hexadecimal")
        asset_path = self._asset_path(organization, sha256)
        if not asset_path.is_file() or asset_path.is_symlink():
            raise EvidenceRegistryError("asset_not_found", "Evidence asset was not found")
        actual_digest, _ = self._hash_file(asset_path)
        if actual_digest != sha256:
            raise EvidenceRegistryError(
                "asset_integrity_conflict",
                "Evidence asset failed integrity verification",
            )
        with asset_path.open("rb") as stream:
            yield stream

    def _new_staging_path(self, organization: str) -> Path:
        organization_directory = self._secure_directory(self.asset_root / organization)
        staging_directory = self._secure_directory(organization_directory / ".staging")
        descriptor, path = tempfile.mkstemp(prefix="upload-", dir=staging_directory)
        os.close(descriptor)
        temporary_path = Path(path)
        os.chmod(temporary_path, 0o600)
        return temporary_path

    def _secure_directory(self, path: Path) -> Path:
        path.mkdir(mode=0o700, parents=True, exist_ok=True)
        if path.is_symlink() or not path.is_dir():
            raise EvidenceRegistryError("unsafe_asset_directory", "Asset directory is unsafe")
        os.chmod(path, 0o700)
        return path

    def _write_chunks(self, path: Path, chunks: Iterable[bytes]) -> tuple[str, int]:
        digest = hashlib.sha256()
        size_bytes = 0
        with path.open("wb") as destination:
            os.chmod(path, 0o600)
            for chunk in chunks:
                size_bytes = self._consume_chunk(destination, digest, size_bytes, chunk)
            destination.flush()
            os.fsync(destination.fileno())
        if size_bytes == 0:
            raise EvidenceRegistryError("empty_asset", "Asset body must not be empty")
        return digest.hexdigest(), size_bytes

    def _consume_chunk(
        self,
        destination: BinaryIO,
        digest: hashlib._Hash,
        size_bytes: int,
        chunk: bytes,
    ) -> int:
        if not isinstance(chunk, bytes):
            raise EvidenceRegistryError("invalid_stream", "Asset stream yielded non-byte content")
        new_size = size_bytes + len(chunk)
        if new_size > self.max_upload_bytes:
            raise EvidenceRegistryError("asset_too_large", "Asset exceeds maximum upload size")
        if chunk:
            destination.write(chunk)
            digest.update(chunk)
        return new_size

    def _finalize(
        self,
        temporary_path: Path,
        *,
        organization: str,
        original_filename: str,
        media_type: str,
        digest: str,
        size_bytes: int,
    ) -> LocalEvidenceDescriptor:
        self._validate_signature(temporary_path, media_type)
        destination = self._asset_path(organization, digest)
        self._secure_directory(destination.parent)
        duplicate = False
        try:
            os.link(temporary_path, destination)
            os.chmod(destination, 0o600)
        except FileExistsError:
            duplicate = True
            existing_digest, existing_size = self._hash_file(destination)
            if existing_digest != digest or existing_size != size_bytes:
                raise EvidenceRegistryError(
                    "asset_integrity_conflict",
                    "Existing content-addressed asset failed integrity verification",
                ) from None

        evidence_id = f"asset:{uuid5(EVIDENCE_NAMESPACE, f'{organization}:{digest}')}"
        return LocalEvidenceDescriptor(
            evidence_id=evidence_id,
            evidence_type=MEDIA_TYPES[media_type],
            original_filename=original_filename,
            media_type=media_type,
            sha256=digest,
            source_reference=f"smartcoat-asset://{organization}/{digest}",
            captured_at=self._clock(),
            duplicate=duplicate,
            size_bytes=size_bytes,
        )

    def _asset_path(self, organization: str, digest: str) -> Path:
        return self.asset_root / organization / digest[:2] / digest

    @staticmethod
    def _hash_file(path: Path) -> tuple[str, int]:
        if path.is_symlink() or not path.is_file():
            raise EvidenceRegistryError("asset_integrity_conflict", "Existing asset is unsafe")
        digest = hashlib.sha256()
        size_bytes = 0
        with path.open("rb") as stream:
            while chunk := stream.read(CHUNK_SIZE):
                size_bytes += len(chunk)
                digest.update(chunk)
        return digest.hexdigest(), size_bytes

    @staticmethod
    def _validate_signature(path: Path, media_type: str) -> None:
        with path.open("rb") as stream:
            prefix = stream.read(16)
        valid = False
        if media_type == "text/plain":
            decoder = codecs.getincrementaldecoder("utf-8")("strict")
            try:
                with path.open("rb") as stream:
                    while chunk := stream.read(CHUNK_SIZE):
                        if b"\x00" in chunk:
                            raise UnicodeDecodeError("utf-8", chunk, 0, 1, "embedded NUL")
                        decoder.decode(chunk)
                    decoder.decode(b"", final=True)
                valid = True
            except UnicodeDecodeError:
                valid = False
        elif media_type == "application/pdf":
            valid = prefix.startswith(b"%PDF-")
        elif media_type == "image/png":
            valid = prefix.startswith(b"\x89PNG\r\n\x1a\n")
        elif media_type == "image/jpeg":
            valid = prefix.startswith(b"\xff\xd8\xff")
        elif media_type == "image/webp":
            valid = prefix.startswith(b"RIFF") and prefix[8:12] == b"WEBP"
        elif media_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
            try:
                with zipfile.ZipFile(path) as archive:
                    names = set(archive.namelist())
                    valid = "[Content_Types].xml" in names and "xl/workbook.xml" in names
            except (OSError, zipfile.BadZipFile):
                valid = False
        elif media_type in {"audio/webm", "video/webm"}:
            valid = prefix.startswith(b"\x1a\x45\xdf\xa3")
        elif media_type in {"audio/wav", "audio/x-wav"}:
            valid = prefix.startswith(b"RIFF") and prefix[8:12] == b"WAVE"
        elif media_type == "audio/ogg":
            valid = prefix.startswith(b"OggS")
        elif media_type == "audio/flac":
            valid = prefix.startswith(b"fLaC")
        elif media_type == "audio/mpeg":
            valid = prefix.startswith(b"ID3") or prefix[:2] in {
                b"\xff\xfb",
                b"\xff\xf3",
                b"\xff\xf2",
            }
        elif media_type in {"audio/m4a", "audio/mp4", "audio/x-m4a"}:
            valid = len(prefix) >= 12 and prefix[4:8] == b"ftyp"
        elif media_type == "audio/aac":
            valid = len(prefix) >= 2 and prefix[0] == 0xFF and prefix[1] & 0xF6 == 0xF0
        if not valid:
            raise EvidenceRegistryError(
                "media_signature_mismatch",
                "Asset content does not match the declared media type",
            )


__all__ = [
    "EvidenceRegistryError",
    "LocalEvidenceDescriptor",
    "LocalEvidenceRegistry",
    "normalize_media_type",
    "normalize_organization_id",
]
