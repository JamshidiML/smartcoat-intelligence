from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal
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
    RESTRICTED = "restricted"
    STRATEGIC = "strategic"


class GovernancePurpose(StrEnum):
    INVENTORY = "inventory"
    RETRIEVAL = "retrieval"
    ANALYTICS = "analytics"
    HUMAN_REVIEW = "human_review"
    MODEL_TRAINING = "model_training"
    EXTERNAL_SHARING = "external_sharing"


class PurposeDecisionStatus(StrEnum):
    NOT_REQUESTED = "not_requested"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"
    REVOKED = "revoked"


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

    @field_validator("name", "version")
    @classmethod
    def normalize_non_empty_value(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("schema target values must not be blank")
        return normalized


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
    governance_schema_version: Literal["smartcoat-governance-v1.1-draft"]
    purpose_decisions: dict[GovernancePurpose, PurposeDecisionStatus]
    schema_target: SchemaTarget
    checksum_sha256: str | None = None
    content_fingerprint: str | None = None
    source_created_at: datetime | None = None
    manifest_created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    dry_run: Literal[True] = True
    model_training_approval_reference: str | None = Field(
        default=None,
        description=(
            "Opaque declared metadata only; it is not verified authorization or an IAM control."
        ),
    )
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator(
        "source_system",
        "source_reference",
        "organization_id",
        "site_id",
        "source_owner",
        "model_training_approval_reference",
    )
    @classmethod
    def normalize_boundary_value(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("boundary and provenance values must not be blank")
        return normalized

    @field_validator("checksum_sha256")
    @classmethod
    def checksum_must_be_sha256(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
            raise ValueError("checksum_sha256 must be a lowercase 64-character SHA-256 hex digest")
        return value

    @field_validator("content_fingerprint")
    @classmethod
    def fingerprint_must_be_meaningful(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        allowed = set("abcdefghijklmnopqrstuvwxyz0123456789._:-")
        if not 16 <= len(normalized) <= 256:
            raise ValueError("content_fingerprint must contain between 16 and 256 characters")
        if any(character not in allowed for character in normalized):
            raise ValueError("content_fingerprint contains unsupported characters")
        alphanumeric_characters = {character for character in normalized if character.isalnum()}
        if len(alphanumeric_characters) < 4:
            raise ValueError("content_fingerprint must contain at least four distinct characters")
        return normalized

    @field_validator("purpose_decisions")
    @classmethod
    def require_all_governance_purposes(
        cls,
        value: dict[GovernancePurpose, PurposeDecisionStatus],
    ) -> dict[GovernancePurpose, PurposeDecisionStatus]:
        expected = set(GovernancePurpose)
        actual = set(value)
        if actual != expected:
            missing = sorted(purpose.value for purpose in expected - actual)
            extra = sorted(str(purpose) for purpose in actual - expected)
            raise ValueError(
                f"purpose_decisions must contain every canonical purpose; "
                f"missing={missing}, extra={extra}"
            )
        return value

    @model_validator(mode="after")
    def require_fingerprint_or_checksum(self) -> "SourceManifest":
        if not self.checksum_sha256 and not self.content_fingerprint:
            raise ValueError("checksum_sha256 or content_fingerprint is required")
        return self

    @property
    def duplicate_source_field(self) -> str:
        return "checksum_sha256" if self.checksum_sha256 else "content_fingerprint"

    @property
    def duplicate_source_value(self) -> str:
        value = self.checksum_sha256 or self.content_fingerprint
        if value is None:
            raise ValueError("validated manifests require a duplicate source value")
        return value

    @property
    def duplicate_key(self) -> str:
        organization = self.organization_id
        return (
            f"organization:{len(organization)}:{organization}|"
            f"{self.duplicate_source_field}:{self.duplicate_source_value}"
        )

    @property
    def candidate_identity(self) -> str:
        schema_name = self.schema_target.name
        schema_version = self.schema_target.version
        return (
            f"{self.duplicate_key}|schema:{len(schema_name)}:{schema_name}|"
            f"version:{len(schema_version)}:{schema_version}"
        )


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
        return self.status == IngestionStatus.VALIDATED


class IngestionCandidate(BaseModel):
    """Governed dry-run candidate produced only by the validated workflow."""

    candidate_id: UUID
    manifest_id: UUID
    ingestion_job_id: UUID
    status: Literal[IngestionStatus.CANDIDATE_CREATED] = IngestionStatus.CANDIDATE_CREATED
    source_type: SourceType
    source_format: SourceFormat
    source_system: str
    source_reference: str
    source_owner: str
    source_created_at: datetime | None
    manifest_created_at: datetime
    organization_id: str
    site_id: str | None = None
    confidentiality_level: ConfidentialityLevel
    governance_schema_version: Literal["smartcoat-governance-v1.1-draft"]
    purpose_decisions: dict[GovernancePurpose, PurposeDecisionStatus]
    model_training_approval_reference: str | None = None
    schema_target: SchemaTarget
    checksum_sha256: str | None = None
    content_fingerprint: str | None = None
    duplicate_key: str
    dry_run: Literal[True] = True
    created_at: datetime


class IngestionWorkflowResult(BaseModel):
    """Structured outcome from the only approved candidate workflow."""

    validation: ManifestValidationResult
    candidate: IngestionCandidate | None = None

    @property
    def accepted(self) -> bool:
        return self.candidate is not None
