"""Knowledge Object v2 core contracts with no API or persistence behavior.

T02 owns governance, mutable-state, command, revision-evaluation, and legacy
compatibility boundaries. ``evidence_ids`` is identity-only and is not the
final structured EvidenceReference contract. T03 will compose structured
evidence and expanded provenance; creator identity therefore remains solely in
that future canonical ``provenance.created_by`` field and is not duplicated
here.
"""

from __future__ import annotations

import json
import math
from collections.abc import Sequence
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator, model_validator
from pydantic_core import PydanticCustomError

from smartcoat.domain.base import LifecycleState
from smartcoat.domain.context_references import KnowledgeContext
from smartcoat.domain.knowledge_objects import KnowledgeObject, KnowledgeObjectType

type JsonValue = str | int | float | bool | None | list[JsonValue] | dict[str, JsonValue]

MAX_TITLE_LENGTH = 256
MAX_DESCRIPTION_LENGTH = 4096
MAX_IDENTIFIER_LENGTH = 512
MAX_ROLE_LENGTH = 128
MAX_RELATIONSHIP_TYPE_LENGTH = 128
MAX_TAG_LENGTH = 128
MAX_TAGS = 64
MAX_EVIDENCE_IDS = 128
MAX_RELATIONSHIPS = 128

MAX_CONTENT_TOP_LEVEL_KEYS = 64
MAX_CONTENT_NESTING_DEPTH = 4
MAX_CONTENT_COLLECTION_ITEMS = 128
MAX_CONTENT_STRING_LENGTH = 4096
MAX_CONTENT_JSON_BYTES = 32768


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
            "knowledge_v2_invalid_text",
            f"{field_name} must be a string",
        )
    normalized = value.strip()
    if not normalized:
        raise _custom_error(
            "knowledge_v2_blank_text",
            f"{field_name} must not be blank",
        )
    if len(normalized) > max_length:
        raise _custom_error(
            "knowledge_v2_text_too_long",
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
    return _normalize_required_text(value, field_name=field_name, max_length=max_length)


def _normalize_unique_text_collection(
    value: Any,
    *,
    field_name: str,
    max_items: int,
    max_item_length: int,
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise _custom_error(
            "knowledge_v2_invalid_text_collection",
            f"{field_name} must be an ordered collection of strings",
        )
    if len(value) > max_items:
        raise _custom_error(
            "knowledge_v2_text_collection_too_large",
            f"{field_name} must contain at most {max_items} items",
        )

    normalized: list[str] = []
    seen: set[str] = set()
    for item in value:
        text = _normalize_required_text(
            item,
            field_name=f"{field_name} item",
            max_length=max_item_length,
        )
        if text in seen:
            raise _custom_error(
                "knowledge_v2_duplicate_text_item",
                f"{field_name} must not contain duplicate values",
            )
        normalized.append(text)
        seen.add(text)
    return tuple(normalized)


def _validate_json_value(value: Any, *, depth: int) -> JsonValue:
    if value is None or isinstance(value, (str, bool, int)):
        if isinstance(value, str) and len(value) > MAX_CONTENT_STRING_LENGTH:
            raise _custom_error(
                "knowledge_v2_content_string_too_long",
                f"content strings must contain at most {MAX_CONTENT_STRING_LENGTH} characters",
            )
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise _custom_error(
                "knowledge_v2_content_non_finite_number",
                "content numbers must be finite JSON values",
            )
        return value
    if isinstance(value, list):
        if depth > MAX_CONTENT_NESTING_DEPTH:
            raise _custom_error(
                "knowledge_v2_content_too_deep",
                f"content nesting depth must not exceed {MAX_CONTENT_NESTING_DEPTH}",
            )
        if len(value) > MAX_CONTENT_COLLECTION_ITEMS:
            raise _custom_error(
                "knowledge_v2_content_collection_too_large",
                f"content collections must contain at most {MAX_CONTENT_COLLECTION_ITEMS} items",
            )
        return [_validate_json_value(item, depth=depth + 1) for item in value]
    if isinstance(value, dict):
        if depth > MAX_CONTENT_NESTING_DEPTH:
            raise _custom_error(
                "knowledge_v2_content_too_deep",
                f"content nesting depth must not exceed {MAX_CONTENT_NESTING_DEPTH}",
            )
        if len(value) > MAX_CONTENT_COLLECTION_ITEMS:
            raise _custom_error(
                "knowledge_v2_content_collection_too_large",
                f"content collections must contain at most {MAX_CONTENT_COLLECTION_ITEMS} items",
            )
        normalized: dict[str, JsonValue] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise _custom_error(
                    "knowledge_v2_content_non_string_key",
                    "content object keys must be strings",
                )
            if len(key) > MAX_CONTENT_STRING_LENGTH:
                raise _custom_error(
                    "knowledge_v2_content_string_too_long",
                    f"content keys must contain at most {MAX_CONTENT_STRING_LENGTH} characters",
                )
            normalized[key] = _validate_json_value(item, depth=depth + 1)
        return normalized
    raise _custom_error(
        "knowledge_v2_content_invalid_type",
        "content allows only finite JSON-compatible values",
    )


def _validate_bounded_content(value: Any) -> dict[str, JsonValue]:
    if not isinstance(value, dict):
        raise _custom_error(
            "knowledge_v2_content_not_object",
            "content must be a JSON object",
        )
    if len(value) > MAX_CONTENT_TOP_LEVEL_KEYS:
        raise _custom_error(
            "knowledge_v2_content_too_many_top_level_keys",
            f"content allows at most {MAX_CONTENT_TOP_LEVEL_KEYS} top-level keys",
        )

    normalized = _validate_json_value(value, depth=1)
    if not isinstance(normalized, dict):
        raise AssertionError("top-level content validation must return an object")
    encoded = json.dumps(
        normalized,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    if len(encoded) > MAX_CONTENT_JSON_BYTES:
        raise _custom_error(
            "knowledge_v2_content_payload_too_large",
            f"content must serialize to at most {MAX_CONTENT_JSON_BYTES} UTF-8 bytes",
        )
    return normalized


class ConfidentialityLevel(StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    STRATEGIC = "strategic"


class OwnerReference(BaseModel):
    """Application ownership metadata, not an authenticated IAM identity."""

    model_config = ConfigDict(extra="forbid")

    owner_id: str = Field(min_length=1, max_length=MAX_IDENTIFIER_LENGTH)
    role: str = Field(min_length=1, max_length=MAX_ROLE_LENGTH)

    @field_validator("owner_id", "role", mode="before")
    @classmethod
    def normalize_required_fields(cls, value: Any, info: ValidationInfo) -> str:
        field_name = info.field_name or "owner field"
        max_length = MAX_IDENTIFIER_LENGTH if field_name == "owner_id" else MAX_ROLE_LENGTH
        return _normalize_required_text(
            value,
            field_name=field_name,
            max_length=max_length,
        )


class UncertaintyKind(StrEnum):
    """Application uncertainty vocabulary; measurement-state schemas remain separate."""

    UNKNOWN = "unknown"
    ASSUMPTION = "assumption"
    ESTIMATE = "estimate"
    INFERENCE = "inference"
    MEASUREMENT = "measurement"
    CONFLICT = "conflict"


class UncertaintyDeclaration(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: UncertaintyKind
    confidence: float | None = Field(default=None, ge=0.0, le=1.0, allow_inf_nan=False)
    note: str | None = Field(default=None, max_length=MAX_DESCRIPTION_LENGTH)

    @field_validator("confidence", mode="before")
    @classmethod
    def reject_non_finite_confidence(cls, value: Any) -> Any:
        if isinstance(value, bool):
            raise _custom_error(
                "knowledge_v2_uncertainty_invalid_confidence",
                "uncertainty confidence must be a number, not a boolean",
            )
        if isinstance(value, float) and not math.isfinite(value):
            raise _custom_error(
                "knowledge_v2_uncertainty_non_finite_confidence",
                "uncertainty confidence must be finite",
            )
        return value

    @field_validator("note", mode="before")
    @classmethod
    def normalize_note(cls, value: Any) -> str | None:
        return _normalize_optional_text(
            value,
            field_name="note",
            max_length=MAX_DESCRIPTION_LENGTH,
        )

    @model_validator(mode="after")
    def validate_kind_rules(self) -> UncertaintyDeclaration:
        if self.kind is UncertaintyKind.CONFLICT and self.note is None:
            raise _custom_error(
                "knowledge_v2_uncertainty_conflict_note_required",
                "conflict uncertainty requires a non-empty note",
            )
        if self.kind is UncertaintyKind.UNKNOWN and self.confidence is not None:
            raise _custom_error(
                "knowledge_v2_uncertainty_unknown_confidence_forbidden",
                "unknown uncertainty must not carry numeric confidence",
            )
        return self


class KnowledgeObjectRelationship(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_object_id: UUID
    relationship_type: str = Field(min_length=1, max_length=MAX_RELATIONSHIP_TYPE_LENGTH)
    target_revision: int | None = Field(default=None, gt=0)

    @field_validator("relationship_type", mode="before")
    @classmethod
    def normalize_relationship_type(cls, value: Any) -> str:
        return _normalize_required_text(
            value,
            field_name="relationship_type",
            max_length=MAX_RELATIONSHIP_TYPE_LENGTH,
        )

    @property
    def identity_key(self) -> tuple[UUID, str]:
        return (self.target_object_id, self.relationship_type)


class DecisionObjectRelationship(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_decision_id: UUID
    relationship_type: str = Field(min_length=1, max_length=MAX_RELATIONSHIP_TYPE_LENGTH)
    target_revision: int | None = Field(default=None, gt=0)

    @field_validator("relationship_type", mode="before")
    @classmethod
    def normalize_relationship_type(cls, value: Any) -> str:
        return _normalize_required_text(
            value,
            field_name="relationship_type",
            max_length=MAX_RELATIONSHIP_TYPE_LENGTH,
        )

    @property
    def identity_key(self) -> tuple[UUID, str]:
        return (self.target_decision_id, self.relationship_type)


def _validate_relationship_collection(
    relationships: Sequence[KnowledgeObjectRelationship | DecisionObjectRelationship],
    *,
    field_name: str,
) -> None:
    seen: dict[tuple[UUID, str], tuple[int, int | None]] = {}
    for index, relationship in enumerate(relationships):
        key = relationship.identity_key
        previous = seen.get(key)
        if previous is None:
            seen[key] = (index, relationship.target_revision)
            continue

        previous_index, previous_revision = previous
        if previous_revision == relationship.target_revision:
            code = "knowledge_v2_relationship_exact_duplicate"
        else:
            code = "knowledge_v2_relationship_revision_conflict"
        raise _custom_error(
            code,
            f"{field_name}[{index}] conflicts with {field_name}[{previous_index}]",
        )


class KnowledgeObjectV2MutableState(BaseModel):
    """Complete normalized replacement state; server-managed fields are excluded."""

    model_config = ConfigDict(extra="forbid", validate_default=True)

    title: str = Field(min_length=1, max_length=MAX_TITLE_LENGTH)
    description: str | None = Field(default=None, max_length=MAX_DESCRIPTION_LENGTH)
    knowledge_type: KnowledgeObjectType
    owner: OwnerReference
    confidentiality: ConfidentialityLevel
    uncertainty: UncertaintyDeclaration | None = None
    tags: tuple[str, ...] = Field(default_factory=tuple, max_length=MAX_TAGS)
    content: dict[str, JsonValue] = Field(default_factory=dict)
    context: KnowledgeContext = Field(default_factory=lambda: KnowledgeContext(references=[]))
    evidence_ids: tuple[str, ...] = Field(default_factory=tuple, max_length=MAX_EVIDENCE_IDS)
    knowledge_relationships: tuple[KnowledgeObjectRelationship, ...] = Field(
        default_factory=tuple,
        max_length=MAX_RELATIONSHIPS,
    )
    decision_relationships: tuple[DecisionObjectRelationship, ...] = Field(
        default_factory=tuple,
        max_length=MAX_RELATIONSHIPS,
    )

    @field_validator("title", mode="before")
    @classmethod
    def normalize_title(cls, value: Any) -> str:
        return _normalize_required_text(
            value,
            field_name="title",
            max_length=MAX_TITLE_LENGTH,
        )

    @field_validator("description", mode="before")
    @classmethod
    def normalize_description(cls, value: Any) -> str | None:
        return _normalize_optional_text(
            value,
            field_name="description",
            max_length=MAX_DESCRIPTION_LENGTH,
        )

    @field_validator("tags", mode="before")
    @classmethod
    def normalize_tags(cls, value: Any) -> tuple[str, ...]:
        return _normalize_unique_text_collection(
            value,
            field_name="tags",
            max_items=MAX_TAGS,
            max_item_length=MAX_TAG_LENGTH,
        )

    @field_validator("evidence_ids", mode="before")
    @classmethod
    def normalize_evidence_ids(cls, value: Any) -> tuple[str, ...]:
        """Keep identity only; T03 owns structured EvidenceReference composition."""

        return _normalize_unique_text_collection(
            value,
            field_name="evidence_ids",
            max_items=MAX_EVIDENCE_IDS,
            max_item_length=MAX_IDENTIFIER_LENGTH,
        )

    @field_validator("content", mode="before")
    @classmethod
    def validate_content(cls, value: Any) -> dict[str, JsonValue]:
        return _validate_bounded_content(value)

    @model_validator(mode="after")
    def validate_relationships(self) -> KnowledgeObjectV2MutableState:
        _validate_relationship_collection(
            self.knowledge_relationships,
            field_name="knowledge_relationships",
        )
        _validate_relationship_collection(
            self.decision_relationships,
            field_name="decision_relationships",
        )
        return self


class KnowledgeObjectV2CreateCommand(BaseModel):
    """Unpersisted create intent; identity, lifecycle, revision, and time are server-owned."""

    model_config = ConfigDict(extra="forbid")

    organization_id: str = Field(min_length=1, max_length=MAX_IDENTIFIER_LENGTH)
    mutable_state: KnowledgeObjectV2MutableState

    @field_validator("organization_id", mode="before")
    @classmethod
    def normalize_organization_id(cls, value: Any) -> str:
        return _normalize_required_text(
            value,
            field_name="organization_id",
            max_length=MAX_IDENTIFIER_LENGTH,
        )


class KnowledgeObjectV2UpdateCommand(BaseModel):
    """Full-state replacement intent with optimistic revision precondition."""

    model_config = ConfigDict(extra="forbid")

    object_id: UUID
    expected_revision: int = Field(gt=0)
    replacement: KnowledgeObjectV2MutableState


class KnowledgeObjectV2CoreRecord(BaseModel):
    """Persisted v2 core snapshot, before T03 evidence/provenance composition."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    object_id: UUID
    organization_id: str = Field(min_length=1, max_length=MAX_IDENTIFIER_LENGTH)
    revision: int = Field(ge=1)
    lifecycle_state: LifecycleState
    created_at: datetime
    updated_at: datetime
    mutable_state: KnowledgeObjectV2MutableState

    @field_validator("organization_id", mode="before")
    @classmethod
    def normalize_organization_id(cls, value: Any) -> str:
        return _normalize_required_text(
            value,
            field_name="organization_id",
            max_length=MAX_IDENTIFIER_LENGTH,
        )

    @field_validator("created_at", "updated_at")
    @classmethod
    def normalize_timestamp(cls, value: datetime, info: ValidationInfo) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise _custom_error(
                "knowledge_v2_naive_timestamp",
                f"{info.field_name} must be timezone-aware",
            )
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def validate_record_invariants(self) -> KnowledgeObjectV2CoreRecord:
        if self.updated_at < self.created_at:
            raise _custom_error(
                "knowledge_v2_updated_before_created",
                "updated_at must not precede created_at",
            )
        if any(
            relationship.target_object_id == self.object_id
            for relationship in self.mutable_state.knowledge_relationships
        ):
            raise _custom_error(
                "knowledge_v2_self_relationship",
                "a persisted Knowledge Object must not relate to itself",
            )
        return self


class UpdateDisposition(StrEnum):
    NO_OP = "no_op"
    MATERIAL_CHANGE = "material_change"


class KnowledgeObjectUpdateError(ValueError):
    """Typed deterministic update-evaluation failure."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


def evaluate_knowledge_object_update(
    current: KnowledgeObjectV2CoreRecord,
    command: KnowledgeObjectV2UpdateCommand,
) -> UpdateDisposition:
    """Evaluate one command without mutation, revision changes, audit, or persistence."""

    if command.object_id != current.object_id:
        raise KnowledgeObjectUpdateError(
            "knowledge_object_target_mismatch",
            "the update command target does not match the current record",
        )
    if command.expected_revision != current.revision:
        raise KnowledgeObjectUpdateError(
            "stale_revision",
            "the update command expected revision does not match the current record",
        )
    if command.replacement == current.mutable_state:
        return UpdateDisposition.NO_OP
    return UpdateDisposition.MATERIAL_CHANGE


class LegacyCompatibilityBlocker(StrEnum):
    MISSING_ORGANIZATION_ID = "missing_organization_id"
    MISSING_STRUCTURED_OWNER = "missing_structured_owner"
    MISSING_CONFIDENTIALITY = "missing_confidentiality"
    LEGACY_EVIDENCE_REQUIRES_T03 = "legacy_evidence_requires_t03_adaptation"
    LEGACY_RELATED_ENTITIES_REQUIRE_CLASSIFICATION = (
        "legacy_related_entities_require_context_classification"
    )
    LEGACY_RELATED_DECISIONS_REQUIRE_TYPING = "legacy_related_decisions_require_relationship_typing"
    LEGACY_CONFIDENCE_REQUIRES_UNCERTAINTY_KIND = "legacy_confidence_requires_uncertainty_kind"
    MINIMAL_PROVENANCE_REQUIRES_T03 = "minimal_provenance_requires_t03_enrichment"
    REVISION_MIGRATION_REQUIRES_T05 = "revision_migration_requires_t05"
    LIFECYCLE_MIGRATION_REQUIRES_T05 = "lifecycle_migration_requires_t05"
    MUTABLE_TEXT_REQUIRES_REVIEW = "legacy_mutable_text_requires_normalized_review"
    CONTENT_REQUIRES_REVIEW = "legacy_content_requires_bounded_review"


class LegacyKnowledgeObjectCompatibilityAssessment(BaseModel):
    """Fail-closed facts about one untouched Release 1.7 object."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    legacy_object_id: UUID
    is_v2_complete: Literal[False] = False
    blockers: tuple[LegacyCompatibilityBlocker, ...]
    safe_copy_fields: tuple[str, ...]
    bounded_content: dict[str, JsonValue] | None


def assess_legacy_knowledge_object(
    legacy: KnowledgeObject,
) -> LegacyKnowledgeObjectCompatibilityAssessment:
    """Assess migration gaps without fabricating or mutating legacy values."""

    blockers = [
        LegacyCompatibilityBlocker.MISSING_ORGANIZATION_ID,
        LegacyCompatibilityBlocker.MISSING_STRUCTURED_OWNER,
        LegacyCompatibilityBlocker.MISSING_CONFIDENTIALITY,
    ]
    if legacy.evidence:
        blockers.append(LegacyCompatibilityBlocker.LEGACY_EVIDENCE_REQUIRES_T03)
    if legacy.related_entities:
        blockers.append(LegacyCompatibilityBlocker.LEGACY_RELATED_ENTITIES_REQUIRE_CLASSIFICATION)
    if legacy.related_decisions:
        blockers.append(LegacyCompatibilityBlocker.LEGACY_RELATED_DECISIONS_REQUIRE_TYPING)
    if legacy.confidence is not None:
        blockers.append(LegacyCompatibilityBlocker.LEGACY_CONFIDENCE_REQUIRES_UNCERTAINTY_KIND)
    blockers.extend(
        [
            LegacyCompatibilityBlocker.MINIMAL_PROVENANCE_REQUIRES_T03,
            LegacyCompatibilityBlocker.REVISION_MIGRATION_REQUIRES_T05,
            LegacyCompatibilityBlocker.LIFECYCLE_MIGRATION_REQUIRES_T05,
        ]
    )

    safe_copy_fields = ["knowledge_type"]
    mutable_text_requires_review = False
    try:
        _normalize_required_text(
            legacy.title,
            field_name="title",
            max_length=MAX_TITLE_LENGTH,
        )
    except (TypeError, ValueError):
        mutable_text_requires_review = True
    else:
        safe_copy_fields.append("title")

    try:
        _normalize_optional_text(
            legacy.description,
            field_name="description",
            max_length=MAX_DESCRIPTION_LENGTH,
        )
    except (TypeError, ValueError):
        mutable_text_requires_review = True
    else:
        safe_copy_fields.append("description")

    try:
        _normalize_unique_text_collection(
            legacy.tags,
            field_name="tags",
            max_items=MAX_TAGS,
            max_item_length=MAX_TAG_LENGTH,
        )
    except (TypeError, ValueError):
        mutable_text_requires_review = True
    else:
        safe_copy_fields.append("tags")

    if mutable_text_requires_review:
        blockers.append(LegacyCompatibilityBlocker.MUTABLE_TEXT_REQUIRES_REVIEW)

    try:
        bounded_content = _validate_bounded_content(legacy.content)
    except (TypeError, ValueError):
        bounded_content = None
        blockers.append(LegacyCompatibilityBlocker.CONTENT_REQUIRES_REVIEW)
    else:
        safe_copy_fields.append("content")

    return LegacyKnowledgeObjectCompatibilityAssessment(
        legacy_object_id=legacy.object_id,
        blockers=tuple(blockers),
        safe_copy_fields=tuple(safe_copy_fields),
        bounded_content=bounded_content,
    )
