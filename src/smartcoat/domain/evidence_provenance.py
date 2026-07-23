"""Structured evidence and provenance contracts governed by ADR-0025.

The models in this module describe metadata and references only. They do not
read files, retain raw content, verify supplied fingerprints, authorize actors,
or imply that an external source exists.
"""

from __future__ import annotations

import json
import re
from collections.abc import Sequence
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID, uuid5

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SerializationInfo,
    ValidationInfo,
    field_validator,
    model_serializer,
    model_validator,
)
from pydantic_core import PydanticCustomError

from smartcoat.domain.base import Provenance
from smartcoat.domain.context_references import ContextReference
from smartcoat.domain.knowledge_objects_v2 import (
    ConfidentialityLevel,
    KnowledgeObjectV2CoreRecord,
)

MAX_EVIDENCE_ID_LENGTH = 512
MAX_SOURCE_REFERENCE_LENGTH = 2048
MAX_TITLE_LENGTH = 256
MAX_DESCRIPTION_LENGTH = 4096
MAX_ACTOR_LENGTH = 512
MAX_SOURCE_SYSTEM_LENGTH = 256
MAX_MEDIA_TYPE_LENGTH = 127
MAX_TRANSFORMATION_TYPE_LENGTH = 128
MAX_TRANSFORMATION_NOTE_LENGTH = 2048
MAX_TRANSFORMATIONS = 64
MAX_EVIDENCE_REFERENCES = 128

# T03 supports the full 64-byte BLAKE2b digest only. A later contract may add
# shorter digest sizes with an explicit algorithm-and-length representation.
BLAKE2B_SUPPORTED_HEX_LENGTH = 128

LEGACY_EVIDENCE_NAMESPACE = UUID("6f475458-0b30-5e40-a4f0-25119d876f38")

_HEX_PATTERN = re.compile(r"^[0-9a-f]+$")
_MEDIA_TYPE_PATTERN = re.compile(
    r"^[a-z0-9][a-z0-9!#$&^_.+-]{0,62}/[a-z0-9][a-z0-9!#$&^_.+-]{0,62}$"
)
_EMBEDDED_BASE64_PATTERN = re.compile(r"^[A-Za-z0-9+/]{256,}={0,2}$")


def _custom_error(code: str, message: str) -> PydanticCustomError:
    return PydanticCustomError(code, message)


def _normalize_required_text(
    value: Any,
    *,
    field_name: str,
    max_length: int,
) -> str:
    if not isinstance(value, str):
        raise _custom_error(
            "evidence_provenance_invalid_text",
            f"{field_name} must be a string",
        )
    normalized = value.strip()
    if not normalized:
        raise _custom_error(
            "evidence_provenance_blank_text",
            f"{field_name} must not be blank",
        )
    if len(normalized) > max_length:
        raise _custom_error(
            "evidence_provenance_text_too_long",
            f"{field_name} must contain at most {max_length} characters",
        )
    return normalized


def _normalize_optional_text(
    value: Any,
    *,
    field_name: str,
    max_length: int,
) -> str | None:
    if value is None:
        return None
    return _normalize_required_text(
        value,
        field_name=field_name,
        max_length=max_length,
    )


def _normalize_aware_datetime(value: datetime, *, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise _custom_error(
            "evidence_provenance_naive_timestamp",
            f"{field_name} must be timezone-aware",
        )
    return value.astimezone(UTC)


class EvidenceType(StrEnum):
    LEGACY_REFERENCE = "legacy_reference"
    DOCUMENT = "document"
    IMAGE = "image"
    MEASUREMENT = "measurement"
    TEST_RESULT = "test_result"
    DATASET = "dataset"
    OBSERVATION = "observation"
    EXTERNAL_RECORD = "external_record"
    OTHER = "other"


class EvidenceCompleteness(StrEnum):
    COMPLETE = "complete"
    LEGACY_INCOMPLETE = "legacy_incomplete"


class CreationMethod(StrEnum):
    MANUAL = "manual"
    IMPORTED = "imported"
    SYSTEM_GENERATED = "system_generated"
    DERIVED = "derived"
    LEGACY_ADAPTER = "legacy_adapter"


class ProvenanceCompleteness(StrEnum):
    COMPLETE = "complete"
    LEGACY_INCOMPLETE = "legacy_incomplete"


class IntegrityAlgorithm(StrEnum):
    SHA256 = "sha256"
    SHA512 = "sha512"
    BLAKE2B = "blake2b"


class EvidenceIntegrity(BaseModel):
    """A supplied digest declaration, not proof of independent verification."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    algorithm: IntegrityAlgorithm
    value: str

    @field_validator("value", mode="before")
    @classmethod
    def normalize_value(cls, value: Any) -> str:
        return _normalize_required_text(
            value,
            field_name="integrity value",
            max_length=BLAKE2B_SUPPORTED_HEX_LENGTH,
        ).lower()

    @model_validator(mode="after")
    def validate_digest(self) -> EvidenceIntegrity:
        expected_length = {
            IntegrityAlgorithm.SHA256: 64,
            IntegrityAlgorithm.SHA512: 128,
            IntegrityAlgorithm.BLAKE2B: BLAKE2B_SUPPORTED_HEX_LENGTH,
        }[self.algorithm]
        if len(self.value) != expected_length:
            raise _custom_error(
                "evidence_integrity_invalid_length",
                f"{self.algorithm.value} requires exactly {expected_length} hexadecimal characters",
            )
        if _HEX_PATTERN.fullmatch(self.value) is None:
            raise _custom_error(
                "evidence_integrity_invalid_hex",
                "integrity value must contain hexadecimal characters only",
            )
        return self


class _EvidenceReferenceInput(BaseModel):
    """Validated command-side shape used to build canonical evidence."""

    model_config = ConfigDict(extra="forbid", validate_default=True)

    evidence_id: str = Field(min_length=1, max_length=MAX_EVIDENCE_ID_LENGTH)
    evidence_type: EvidenceType
    completeness: EvidenceCompleteness
    title: str | None = Field(default=None, max_length=MAX_TITLE_LENGTH)
    description: str | None = Field(default=None, max_length=MAX_DESCRIPTION_LENGTH)
    source_reference: str = Field(min_length=1, max_length=MAX_SOURCE_REFERENCE_LENGTH)
    source_system: str | None = Field(default=None, max_length=MAX_SOURCE_SYSTEM_LENGTH)
    captured_by: str | None = Field(default=None, max_length=MAX_ACTOR_LENGTH)
    captured_at: datetime | None = None
    source_created_at: datetime | None = None
    integrity: EvidenceIntegrity | None = None
    media_type: str | None = Field(default=None, max_length=MAX_MEDIA_TYPE_LENGTH)
    confidentiality: ConfidentialityLevel | None = None
    context_reference: ContextReference | None = None

    @field_validator("evidence_id", "source_reference", mode="before")
    @classmethod
    def normalize_required_fields(cls, value: Any, info: ValidationInfo) -> str:
        field_name = info.field_name or "evidence field"
        max_length = (
            MAX_EVIDENCE_ID_LENGTH if field_name == "evidence_id" else MAX_SOURCE_REFERENCE_LENGTH
        )
        normalized = _normalize_required_text(
            value,
            field_name=field_name,
            max_length=max_length,
        )
        if field_name == "source_reference" and (
            normalized.casefold().startswith("data:")
            or "base64," in normalized.casefold()
            or _EMBEDDED_BASE64_PATTERN.fullmatch(normalized) is not None
        ):
            raise _custom_error(
                "evidence_embedded_payload_forbidden",
                "source_reference must identify a source and must not embed a payload",
            )
        return normalized

    @field_validator("title", "description", "source_system", "captured_by", mode="before")
    @classmethod
    def normalize_optional_fields(cls, value: Any, info: ValidationInfo) -> str | None:
        field_name = info.field_name or "evidence field"
        max_lengths = {
            "title": MAX_TITLE_LENGTH,
            "description": MAX_DESCRIPTION_LENGTH,
            "source_system": MAX_SOURCE_SYSTEM_LENGTH,
            "captured_by": MAX_ACTOR_LENGTH,
        }
        return _normalize_optional_text(
            value,
            field_name=field_name,
            max_length=max_lengths[field_name],
        )

    @field_validator("captured_at", "source_created_at")
    @classmethod
    def normalize_timestamps(
        cls,
        value: datetime | None,
        info: ValidationInfo,
    ) -> datetime | None:
        if value is None:
            return None
        return _normalize_aware_datetime(
            value,
            field_name=info.field_name or "evidence timestamp",
        )

    @field_validator("media_type", mode="before")
    @classmethod
    def normalize_media_type(cls, value: Any) -> str | None:
        normalized = _normalize_optional_text(
            value,
            field_name="media_type",
            max_length=MAX_MEDIA_TYPE_LENGTH,
        )
        if normalized is None:
            return None
        normalized = normalized.casefold()
        if _MEDIA_TYPE_PATTERN.fullmatch(normalized) is None:
            raise _custom_error(
                "evidence_invalid_media_type",
                "media_type must use a bounded type/subtype form",
            )
        return normalized

    @model_validator(mode="after")
    def validate_completeness(self) -> _EvidenceReferenceInput:
        if self.title is None and self.description is None:
            raise _custom_error(
                "evidence_title_or_description_required",
                "at least one of title or description is required",
            )
        if self.completeness is EvidenceCompleteness.COMPLETE:
            if self.evidence_type is EvidenceType.LEGACY_REFERENCE:
                raise _custom_error(
                    "evidence_complete_legacy_type_forbidden",
                    "complete evidence must not use legacy_reference",
                )
            if self.captured_by is None:
                raise _custom_error(
                    "evidence_complete_actor_required",
                    "complete evidence requires captured_by",
                )
            if self.captured_at is None:
                raise _custom_error(
                    "evidence_complete_captured_at_required",
                    "complete evidence requires captured_at",
                )
        elif self.evidence_type is not EvidenceType.LEGACY_REFERENCE:
            raise _custom_error(
                "evidence_legacy_incomplete_type_required",
                "legacy_incomplete evidence must use legacy_reference",
            )
        return self


def _canonical_evidence_metadata_json(reference: _EvidenceReferenceInput) -> str:
    """Return deterministic JSON that preserves scalar types and list order."""

    return json.dumps(
        reference.model_dump(mode="json"),
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


class EvidenceReference(BaseModel):
    """Alias-free canonical evidence with detached T08 context views.

    Input is validated through ``_EvidenceReferenceInput`` and immediately
    reduced to deterministic canonical JSON. No supplied T08 model, attributes
    dictionary, or nested list is retained. Every property reconstructs a new
    detached view, so changing that view cannot alter canonical evidence.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    canonical_metadata_json: str = Field(repr=False, exclude=True)

    @model_validator(mode="before")
    @classmethod
    def build_canonical_reference(cls, value: Any) -> dict[str, str] | Any:
        if isinstance(value, cls):
            return value
        if isinstance(value, _EvidenceReferenceInput):
            reference = value
        elif isinstance(value, dict) and set(value) == {"canonical_metadata_json"}:
            serialized = value["canonical_metadata_json"]
            if not isinstance(serialized, str):
                return value
            try:
                payload = json.loads(serialized)
            except json.JSONDecodeError as error:
                raise ValueError("canonical_metadata_json must contain valid JSON") from error
            reference = _EvidenceReferenceInput.model_validate(payload)
        else:
            reference = _EvidenceReferenceInput.model_validate(value)
        return {"canonical_metadata_json": _canonical_evidence_metadata_json(reference)}

    @model_serializer(mode="plain")
    def serialize_metadata(self, info: SerializationInfo) -> dict[str, Any]:
        return self._validated_metadata().model_dump(mode=info.mode)

    def _validated_metadata(self) -> _EvidenceReferenceInput:
        return _EvidenceReferenceInput.model_validate_json(self.canonical_metadata_json)

    @property
    def evidence_id(self) -> str:
        return self._validated_metadata().evidence_id

    @property
    def evidence_type(self) -> EvidenceType:
        return self._validated_metadata().evidence_type

    @property
    def completeness(self) -> EvidenceCompleteness:
        return self._validated_metadata().completeness

    @property
    def title(self) -> str | None:
        return self._validated_metadata().title

    @property
    def description(self) -> str | None:
        return self._validated_metadata().description

    @property
    def source_reference(self) -> str:
        return self._validated_metadata().source_reference

    @property
    def source_system(self) -> str | None:
        return self._validated_metadata().source_system

    @property
    def captured_by(self) -> str | None:
        return self._validated_metadata().captured_by

    @property
    def captured_at(self) -> datetime | None:
        return self._validated_metadata().captured_at

    @property
    def source_created_at(self) -> datetime | None:
        return self._validated_metadata().source_created_at

    @property
    def integrity(self) -> EvidenceIntegrity | None:
        return self._validated_metadata().integrity

    @property
    def media_type(self) -> str | None:
        return self._validated_metadata().media_type

    @property
    def confidentiality(self) -> ConfidentialityLevel | None:
        return self._validated_metadata().confidentiality

    @property
    def context_reference(self) -> ContextReference | None:
        return self._validated_metadata().context_reference


class EvidenceReferenceCollectionError(ValueError):
    """Typed deterministic duplicate or identity-conflict failure."""

    def __init__(
        self,
        code: str,
        *,
        evidence_id: str,
        first_index: int,
        second_index: int,
    ) -> None:
        self.code = code
        self.evidence_id = evidence_id
        self.first_index = first_index
        self.second_index = second_index
        super().__init__(
            f"{code}: evidence[{second_index}] conflicts with evidence[{first_index}] "
            f"for evidence_id={evidence_id!r}"
        )


def validate_evidence_references(
    references: Sequence[EvidenceReference],
) -> tuple[EvidenceReference, ...]:
    """Validate an ordered collection without overwriting, merging, or sorting."""

    if len(references) > MAX_EVIDENCE_REFERENCES:
        raise ValueError(
            "evidence_collection_too_large: "
            f"at most {MAX_EVIDENCE_REFERENCES} references are allowed"
        )

    validated = tuple(references)
    seen: dict[str, tuple[int, EvidenceReference]] = {}
    for index, reference in enumerate(validated):
        existing = seen.get(reference.evidence_id)
        if existing is None:
            seen[reference.evidence_id] = (index, reference)
            continue

        first_index, first = existing
        code = (
            "evidence_exact_duplicate"
            if reference.canonical_metadata_json == first.canonical_metadata_json
            else "evidence_id_conflict"
        )
        raise EvidenceReferenceCollectionError(
            code,
            evidence_id=reference.evidence_id,
            first_index=first_index,
            second_index=index,
        )
    return validated


class ProvenanceTransformation(BaseModel):
    """One descriptive transformation fact; it is not executable pipeline code."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    transformation_type: str = Field(min_length=1, max_length=MAX_TRANSFORMATION_TYPE_LENGTH)
    performed_by: str = Field(min_length=1, max_length=MAX_ACTOR_LENGTH)
    performed_at: datetime
    note: str | None = Field(default=None, max_length=MAX_TRANSFORMATION_NOTE_LENGTH)
    source_reference: str | None = Field(default=None, max_length=MAX_SOURCE_REFERENCE_LENGTH)

    @field_validator("transformation_type", "performed_by", mode="before")
    @classmethod
    def normalize_required_fields(cls, value: Any, info: ValidationInfo) -> str:
        field_name = info.field_name or "transformation field"
        max_length = (
            MAX_TRANSFORMATION_TYPE_LENGTH
            if field_name == "transformation_type"
            else MAX_ACTOR_LENGTH
        )
        return _normalize_required_text(
            value,
            field_name=field_name,
            max_length=max_length,
        )

    @field_validator("note", "source_reference", mode="before")
    @classmethod
    def normalize_optional_fields(cls, value: Any, info: ValidationInfo) -> str | None:
        field_name = info.field_name or "transformation field"
        max_length = (
            MAX_TRANSFORMATION_NOTE_LENGTH if field_name == "note" else MAX_SOURCE_REFERENCE_LENGTH
        )
        return _normalize_optional_text(
            value,
            field_name=field_name,
            max_length=max_length,
        )

    @field_validator("performed_at")
    @classmethod
    def normalize_performed_at(cls, value: datetime) -> datetime:
        return _normalize_aware_datetime(value, field_name="performed_at")


class ProvenanceV2(BaseModel):
    """Expanded provenance with explicit complete and legacy-incomplete modes."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    source_system: str | None = Field(default=None, max_length=MAX_SOURCE_SYSTEM_LENGTH)
    source_reference: str | None = Field(default=None, max_length=MAX_SOURCE_REFERENCE_LENGTH)
    created_by: str | None = Field(default=None, max_length=MAX_ACTOR_LENGTH)
    creation_method: CreationMethod | None = None
    captured_at: datetime | None = None
    source_created_at: datetime | None = None
    transformation_history: tuple[ProvenanceTransformation, ...] = Field(
        default_factory=tuple,
        max_length=MAX_TRANSFORMATIONS,
    )
    derived_from_object_id: UUID | None = None
    derived_from_revision: int | None = Field(default=None, gt=0)
    completeness: ProvenanceCompleteness

    @field_validator("source_system", "source_reference", "created_by", mode="before")
    @classmethod
    def normalize_optional_fields(cls, value: Any, info: ValidationInfo) -> str | None:
        field_name = info.field_name or "provenance field"
        max_lengths = {
            "source_system": MAX_SOURCE_SYSTEM_LENGTH,
            "source_reference": MAX_SOURCE_REFERENCE_LENGTH,
            "created_by": MAX_ACTOR_LENGTH,
        }
        return _normalize_optional_text(
            value,
            field_name=field_name,
            max_length=max_lengths[field_name],
        )

    @field_validator("captured_at", "source_created_at")
    @classmethod
    def normalize_timestamps(
        cls,
        value: datetime | None,
        info: ValidationInfo,
    ) -> datetime | None:
        if value is None:
            return None
        return _normalize_aware_datetime(
            value,
            field_name=info.field_name or "provenance timestamp",
        )

    @model_validator(mode="after")
    def validate_completeness_and_derivation(self) -> ProvenanceV2:
        if self.completeness is ProvenanceCompleteness.COMPLETE:
            missing = [
                field_name
                for field_name, value in (
                    ("source_reference", self.source_reference),
                    ("created_by", self.created_by),
                    ("creation_method", self.creation_method),
                    ("captured_at", self.captured_at),
                )
                if value is None
            ]
            if missing:
                raise _custom_error(
                    "provenance_complete_fields_required",
                    f"complete provenance requires: {', '.join(missing)}",
                )
        if (self.derived_from_object_id is None) != (self.derived_from_revision is None):
            raise _custom_error(
                "provenance_derivation_pair_required",
                "derived_from_object_id and derived_from_revision must appear together",
            )
        return self


class EvidenceCompositionError(ValueError):
    """Typed failure for canonical T02 evidence/provenance composition."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


class KnowledgeObjectV2EvidenceComposition(BaseModel):
    """Detached canonical domain composition; not persistence or an API schema."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    core: KnowledgeObjectV2CoreRecord
    evidence: tuple[EvidenceReference, ...] = Field(max_length=MAX_EVIDENCE_REFERENCES)
    provenance: ProvenanceV2

    @model_validator(mode="before")
    @classmethod
    def detach_inputs(cls, value: Any) -> Any:
        if isinstance(value, cls) or not isinstance(value, dict):
            return value
        detached = dict(value)
        core = detached.get("core")
        if isinstance(core, KnowledgeObjectV2CoreRecord):
            detached["core"] = KnowledgeObjectV2CoreRecord.model_validate_json(
                core.model_dump_json()
            )
        evidence = detached.get("evidence")
        if isinstance(evidence, Sequence) and not isinstance(evidence, (str, bytes)):
            detached["evidence"] = tuple(
                EvidenceReference.model_validate_json(item.model_dump_json())
                if isinstance(item, EvidenceReference)
                else item
                for item in evidence
            )
        provenance = detached.get("provenance")
        if isinstance(provenance, ProvenanceV2):
            detached["provenance"] = ProvenanceV2.model_validate_json(provenance.model_dump_json())
        return detached

    @model_validator(mode="after")
    def validate_composition(self) -> KnowledgeObjectV2EvidenceComposition:
        try:
            validated_evidence = validate_evidence_references(self.evidence)
        except EvidenceReferenceCollectionError as error:
            raise EvidenceCompositionError(error.code, str(error)) from error

        expected_ids = self.core.mutable_state.evidence_ids
        actual_ids = tuple(reference.evidence_id for reference in validated_evidence)
        if actual_ids != expected_ids:
            missing = tuple(
                evidence_id for evidence_id in expected_ids if evidence_id not in actual_ids
            )
            extra = tuple(
                evidence_id for evidence_id in actual_ids if evidence_id not in expected_ids
            )
            if missing and not extra:
                code = "evidence_objects_missing"
            elif extra and not missing:
                code = "evidence_objects_extra"
            elif not missing and not extra:
                code = "evidence_order_mismatch"
            else:
                code = "evidence_identity_mismatch"
            raise EvidenceCompositionError(
                code,
                f"core evidence_ids={expected_ids!r}, supplied evidence_ids={actual_ids!r}",
            )

        if any(
            reference.completeness is not EvidenceCompleteness.COMPLETE
            for reference in validated_evidence
        ):
            raise EvidenceCompositionError(
                "canonical_evidence_incomplete",
                "new canonical composition requires complete evidence references",
            )
        if self.provenance.completeness is not ProvenanceCompleteness.COMPLETE:
            raise EvidenceCompositionError(
                "canonical_provenance_incomplete",
                "new canonical composition requires complete provenance",
            )
        return self


def project_platform_evidence_references(
    composition: KnowledgeObjectV2EvidenceComposition,
) -> tuple[str, ...]:
    """Project ordered unique evidence IDs without changing the envelope schema."""

    return tuple(reference.evidence_id for reference in composition.evidence)


class LegacyEvidenceAdapterResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    reference: EvidenceReference
    is_canonical_complete: Literal[False] = False
    unavailable_fields: tuple[str, ...] = ("captured_by", "captured_at")


class LegacyEvidenceCollectionAdapterResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    references: tuple[EvidenceReference, ...]
    is_canonical_complete: Literal[False] = False

    @property
    def evidence_ids(self) -> tuple[str, ...]:
        return tuple(reference.evidence_id for reference in self.references)


class LegacyProvenanceAdapterResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    provenance: ProvenanceV2
    mapped_fields: tuple[str, ...]
    unavailable_fields: tuple[str, ...]
    unmapped_legacy_method: str | None = None
    is_canonical_complete: Literal[False] = False


class LegacyKnowledgeObjectV2EvidenceAdapterResult(BaseModel):
    """Explicit incomplete input to later T05 migration, never canonical composition."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    evidence: LegacyEvidenceCollectionAdapterResult
    provenance: LegacyProvenanceAdapterResult
    is_canonical_complete: Literal[False] = False


def _legacy_evidence_id(source_reference: str) -> str:
    return str(uuid5(LEGACY_EVIDENCE_NAMESPACE, source_reference))


def adapt_legacy_evidence_reference(source_reference: str) -> LegacyEvidenceAdapterResult:
    """Adapt one untouched Release 1.7 string with deterministic UUIDv5 identity."""

    normalized = _normalize_required_text(
        source_reference,
        field_name="legacy evidence source_reference",
        max_length=MAX_SOURCE_REFERENCE_LENGTH,
    )
    reference = EvidenceReference.model_validate(
        {
            "evidence_id": _legacy_evidence_id(normalized),
            "evidence_type": EvidenceType.LEGACY_REFERENCE,
            "completeness": EvidenceCompleteness.LEGACY_INCOMPLETE,
            "description": (
                "Legacy evidence reference retained without complete actor or capture-time facts."
            ),
            "source_reference": normalized,
        }
    )
    return LegacyEvidenceAdapterResult(reference=reference)


def adapt_legacy_evidence_collection(
    source_references: Sequence[str],
) -> LegacyEvidenceCollectionAdapterResult:
    """Adapt and validate legacy evidence in original order without deduplication."""

    if isinstance(source_references, (str, bytes)):
        raise TypeError("legacy evidence collection must be an ordered collection of strings")
    adapted = tuple(
        adapt_legacy_evidence_reference(source_reference).reference
        for source_reference in source_references
    )
    return LegacyEvidenceCollectionAdapterResult(references=validate_evidence_references(adapted))


_LEGACY_CREATION_METHOD_MAP = {
    "manual": CreationMethod.MANUAL,
    "manual_capture": CreationMethod.MANUAL,
    "import": CreationMethod.IMPORTED,
    "imported": CreationMethod.IMPORTED,
    "system_generated": CreationMethod.SYSTEM_GENERATED,
    "derived": CreationMethod.DERIVED,
    "legacy_adapter": CreationMethod.LEGACY_ADAPTER,
}


def _legacy_optional_text(value: str | None, *, max_length: int) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if not normalized:
        return None
    if len(normalized) > max_length:
        return None
    return normalized


def adapt_legacy_provenance(legacy: Provenance) -> LegacyProvenanceAdapterResult:
    """Map only available Release 1.7 facts through an explicit method table."""

    source_system = _legacy_optional_text(
        legacy.source_system,
        max_length=MAX_SOURCE_SYSTEM_LENGTH,
    )
    source_reference = _legacy_optional_text(
        legacy.source_reference,
        max_length=MAX_SOURCE_REFERENCE_LENGTH,
    )
    created_by = _legacy_optional_text(
        legacy.created_by,
        max_length=MAX_ACTOR_LENGTH,
    )
    legacy_method = _legacy_optional_text(
        legacy.method,
        max_length=MAX_TRANSFORMATION_TYPE_LENGTH,
    )
    creation_method = (
        _LEGACY_CREATION_METHOD_MAP.get(legacy_method.casefold())
        if legacy_method is not None
        else None
    )

    provenance = ProvenanceV2(
        source_system=source_system,
        source_reference=source_reference,
        created_by=created_by,
        creation_method=creation_method,
        captured_at=None,
        source_created_at=None,
        transformation_history=(),
        derived_from_object_id=None,
        derived_from_revision=None,
        completeness=ProvenanceCompleteness.LEGACY_INCOMPLETE,
    )
    mapped_fields = tuple(
        field_name
        for field_name, value in (
            ("source_system", source_system),
            ("source_reference", source_reference),
            ("created_by", created_by),
            ("creation_method", creation_method),
        )
        if value is not None
    )
    unavailable_fields = tuple(
        field_name
        for field_name, value in (
            ("source_system", source_system),
            ("source_reference", source_reference),
            ("created_by", created_by),
            ("creation_method", creation_method),
            ("captured_at", None),
            ("source_created_at", None),
            ("derived_from_object_id", None),
            ("derived_from_revision", None),
        )
        if value is None
    )
    return LegacyProvenanceAdapterResult(
        provenance=provenance,
        mapped_fields=mapped_fields,
        unavailable_fields=unavailable_fields,
        unmapped_legacy_method=(
            legacy_method if legacy_method is not None and creation_method is None else None
        ),
    )


def adapt_legacy_evidence_and_provenance(
    source_references: Sequence[str],
    legacy_provenance: Provenance,
) -> LegacyKnowledgeObjectV2EvidenceAdapterResult:
    """Return an explicitly incomplete migration input without changing its sources."""

    return LegacyKnowledgeObjectV2EvidenceAdapterResult(
        evidence=adapt_legacy_evidence_collection(source_references),
        provenance=adapt_legacy_provenance(legacy_provenance),
    )
