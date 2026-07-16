from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator, model_validator


class SourceType(StrEnum):
    SPREADSHEET = "spreadsheet"
    PDF = "pdf"
    IMAGE = "image"
    VOICE_TRANSCRIPT = "voice_transcript"
    ERP_EXPORT = "erp_export"
    OTHER = "other"


class SourceFormat(StrEnum):
    CSV = "csv"
    XLSX = "xlsx"
    PDF = "pdf"
    PNG = "png"
    JPG = "jpg"
    TXT = "txt"
    JSON = "json"
    OTHER = "other"


class ConfidentialityLevel(StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    HIGHLY_CONFIDENTIAL = "highly_confidential"
    RESTRICTED = "restricted"


class PermittedUse(StrEnum):
    INVENTORY_ONLY = "inventory_only"
    RETRIEVAL = "retrieval"
    ANALYTICS = "analytics"
    HUMAN_REVIEW = "human_review"
    MODEL_TRAINING = "model_training"


class IngestionStatus(StrEnum):
    RECEIVED = "received"
    VALIDATED = "validated"
    REJECTED = "rejected"
    DUPLICATE = "duplicate"
    CANDIDATE_CREATED = "candidate_created"
    BLOCKED = "blocked"


class SchemaTarget(BaseModel):
    """Declared canonical mapping target, without performing the mapping."""

    name: str = Field(min_length=1)
    version: str = Field(min_length=1)


class SourceManifest(BaseModel):
    """Metadata-only source manifest for controlled ingestion preparation."""

    manifest_id: UUID = Field(default_factory=uuid4)
    ingestion_job_id: UUID = Field(default_factory=uuid4)
    source_type: SourceType
    source_format: SourceFormat
    source_system: str = Field(min_length=1)
    source_reference: str = Field(min_length=1)
    organization_id: str = Field(min_length=1)
    site_id: str | None = None
    source_owner: str = Field(min_length=1)
    confidentiality_level: ConfidentialityLevel
    permitted_uses: list[PermittedUse]
    schema_target: SchemaTarget
    checksum_sha256: str | None = None
    content_fingerprint: str | None = None
    source_created_at: datetime | None = None
    manifest_created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    dry_run: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("checksum_sha256")
    @classmethod
    def checksum_must_be_sha256(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
            raise ValueError("checksum_sha256 must be a lowercase 64-character SHA-256 hex digest")
        return value

    @field_validator("permitted_uses")
    @classmethod
    def permitted_uses_must_not_be_empty(cls, value: list[PermittedUse]) -> list[PermittedUse]:
        if not value:
            raise ValueError("at least one permitted use is required")
        return value

    @model_validator(mode="after")
    def require_fingerprint_or_checksum(self) -> "SourceManifest":
        if not self.checksum_sha256 and not self.content_fingerprint:
            raise ValueError("checksum_sha256 or content_fingerprint is required")
        return self

    @property
    def duplicate_key(self) -> str:
        if self.checksum_sha256:
            return f"sha256:{self.checksum_sha256}"
        return f"fingerprint:{self.content_fingerprint}"


class ManifestValidationIssue(BaseModel):
    code: str
    message: str
    field: str | None = None


class ManifestValidationResult(BaseModel):
    manifest_id: UUID | None = None
    status: IngestionStatus
    errors: list[ManifestValidationIssue] = Field(default_factory=list)
    warnings: list[ManifestValidationIssue] = Field(default_factory=list)
    duplicate_key: str | None = None

    @property
    def accepted(self) -> bool:
        return self.status in {IngestionStatus.VALIDATED, IngestionStatus.CANDIDATE_CREATED}


class IngestionCandidate(BaseModel):
    """Deterministic dry-run candidate produced after manifest validation."""

    candidate_id: UUID = Field(default_factory=uuid4)
    manifest_id: UUID
    ingestion_job_id: UUID
    status: IngestionStatus = IngestionStatus.CANDIDATE_CREATED
    source_type: SourceType
    source_format: SourceFormat
    source_reference: str
    organization_id: str
    site_id: str | None = None
    confidentiality_level: ConfidentialityLevel
    permitted_uses: list[PermittedUse]
    schema_target: SchemaTarget
    duplicate_key: str
    dry_run: bool
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
