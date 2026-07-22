from __future__ import annotations

import json
import math
import re
from collections.abc import Sequence
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator, model_validator
from pydantic_core import PydanticCustomError

type JsonScalar = str | int | float | bool | None
type ContextAttributeValue = JsonScalar | list[JsonScalar] | dict[str, JsonScalar]
type ContextLinkKey = tuple[str, str, str | None]

MAX_ATTRIBUTE_KEYS = 16
MAX_NESTED_ATTRIBUTE_ITEMS = 16
MAX_ATTRIBUTE_KEY_LENGTH = 64
MAX_ATTRIBUTE_STRING_LENGTH = 512
MAX_ATTRIBUTES_JSON_BYTES = 4096

_CREDENTIAL_KEY_PARTS = {"credential", "password", "passwd", "secret", "token"}
_CREDENTIAL_KEY_PAIRS = {
    ("access", "key"),
    ("api", "key"),
    ("client", "secret"),
    ("private", "key"),
}
_SECRET_VALUE_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"(?i)\b(?:basic|bearer)\s+[A-Za-z0-9._~+/=-]{20,}"),
    re.compile(
        r"(?i)\b(?:password|passwd|api[_-]?key|access[_-]?token|client[_-]?secret)"
        r"\b\s*[:=]\s*[^\s]{8,}"
    ),
)


class ContextType(StrEnum):
    PROJECT = "project"
    EXPERIMENT_OR_TRIAL = "experiment_or_trial"
    MATERIAL = "material"
    FABRIC_OR_SUBSTRATE = "fabric_or_substrate"
    FORMULATION_REFERENCE = "formulation_reference"
    PROCESS_CONDITIONS = "process_conditions"
    TEST_RESULT = "test_result"


class ContextIdKind(StrEnum):
    UUID = "uuid"
    EXTERNAL = "external"


class ContextReferenceCollectionError(ValueError):
    """Typed deterministic failure for one invalid reference collection."""

    def __init__(
        self,
        code: str,
        *,
        first_index: int,
        second_index: int,
        key: ContextLinkKey,
    ) -> None:
        self.code = code
        self.first_index = first_index
        self.second_index = second_index
        self.key = key
        super().__init__(
            f"{code}: context_references[{second_index}] conflicts with "
            f"context_references[{first_index}]"
        )


class ContextReferenceOrganizationError(ValueError):
    """Typed failure for a supplied organization-boundary comparison."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


def _custom_error(code: str, message: str) -> PydanticCustomError:
    return PydanticCustomError(code, message)


def _normalize_attribute_key(key: Any) -> str:
    if not isinstance(key, str):
        raise _custom_error(
            "context_attribute_invalid_key",
            "attribute keys must be strings",
        )
    normalized = key.strip()
    if not normalized:
        raise _custom_error(
            "context_attribute_blank_key",
            "attribute keys must not be blank",
        )
    if len(normalized) > MAX_ATTRIBUTE_KEY_LENGTH:
        raise _custom_error(
            "context_attribute_key_too_long",
            f"attribute keys must contain at most {MAX_ATTRIBUTE_KEY_LENGTH} characters",
        )

    parts = [part for part in re.split(r"[^a-z0-9]+", normalized.casefold()) if part]
    pairs = set(zip(parts, parts[1:], strict=False))
    if _CREDENTIAL_KEY_PARTS.intersection(parts) or _CREDENTIAL_KEY_PAIRS.intersection(pairs):
        raise _custom_error(
            "context_attribute_credential_key",
            "credential and secret attribute keys are prohibited",
        )
    return normalized


def _validate_attribute_scalar(value: Any) -> JsonScalar:
    if value is None or isinstance(value, (str, bool, int)):
        pass
    elif isinstance(value, float):
        if not math.isfinite(value):
            raise _custom_error(
                "context_attribute_non_finite_number",
                "attribute numbers must be finite JSON values",
            )
    else:
        raise _custom_error(
            "context_attribute_invalid_type",
            "attributes allow only JSON scalars or one shallow list or object",
        )

    if isinstance(value, str):
        if len(value) > MAX_ATTRIBUTE_STRING_LENGTH:
            raise _custom_error(
                "context_attribute_string_too_long",
                f"attribute strings must contain at most {MAX_ATTRIBUTE_STRING_LENGTH} characters",
            )
        if any(pattern.search(value) for pattern in _SECRET_VALUE_PATTERNS):
            raise _custom_error(
                "context_attribute_secret_value",
                "credential and secret-like attribute values are prohibited",
            )
    return value


def _validate_attribute_value(value: Any) -> ContextAttributeValue:
    if isinstance(value, list):
        if len(value) > MAX_NESTED_ATTRIBUTE_ITEMS:
            raise _custom_error(
                "context_attribute_collection_too_large",
                f"attribute collections allow at most {MAX_NESTED_ATTRIBUTE_ITEMS} items",
            )
        return [_validate_attribute_scalar(item) for item in value]
    if isinstance(value, dict):
        if len(value) > MAX_NESTED_ATTRIBUTE_ITEMS:
            raise _custom_error(
                "context_attribute_collection_too_large",
                f"attribute collections allow at most {MAX_NESTED_ATTRIBUTE_ITEMS} items",
            )
        normalized: dict[str, JsonScalar] = {}
        for key, item in value.items():
            normalized_key = _normalize_attribute_key(key)
            if normalized_key in normalized:
                raise _custom_error(
                    "context_attribute_duplicate_key",
                    "attribute keys must be unique after whitespace normalization",
                )
            normalized[normalized_key] = _validate_attribute_scalar(item)
        return normalized
    return _validate_attribute_scalar(value)


class ContextReference(BaseModel):
    """Embedded bounded context link governed by ADR-0024."""

    model_config = ConfigDict(extra="forbid")

    context_type: ContextType
    reference_id: str = Field(min_length=1, max_length=512)
    id_kind: ContextIdKind
    source_system: str | None = Field(default=None, max_length=128)
    display_name: str = Field(min_length=1, max_length=256)
    version: str | None = Field(default=None, max_length=128)
    relationship_role: str | None = Field(default=None, max_length=128)
    source_reference: str | None = Field(default=None, max_length=512)
    evidence_reference: str | None = Field(default=None, max_length=512)
    attributes: dict[str, ContextAttributeValue] = Field(default_factory=dict)

    @field_validator("reference_id", "display_name", mode="before")
    @classmethod
    def normalize_required_text(cls, value: Any, info: ValidationInfo) -> str:
        if not isinstance(value, str):
            raise _custom_error(
                "context_reference_invalid_text",
                f"{info.field_name} must be a string",
            )
        normalized = value.strip()
        if not normalized:
            raise _custom_error(
                "context_reference_blank_text",
                f"{info.field_name} must not be blank",
            )
        return normalized

    @field_validator(
        "source_system",
        "version",
        "relationship_role",
        "source_reference",
        "evidence_reference",
        mode="before",
    )
    @classmethod
    def normalize_optional_text(cls, value: Any, info: ValidationInfo) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise _custom_error(
                "context_reference_invalid_text",
                f"{info.field_name} must be a string or null",
            )
        normalized = value.strip()
        if not normalized:
            raise _custom_error(
                "context_reference_blank_optional_text",
                f"{info.field_name} must not be blank when supplied",
            )
        if info.field_name == "relationship_role":
            return normalized.casefold()
        return normalized

    @field_validator("attributes", mode="before")
    @classmethod
    def validate_bounded_attributes(cls, value: Any) -> dict[str, ContextAttributeValue]:
        if not isinstance(value, dict):
            raise _custom_error(
                "context_attributes_not_object",
                "attributes must be a JSON object",
            )
        if len(value) > MAX_ATTRIBUTE_KEYS:
            raise _custom_error(
                "context_attributes_too_large",
                f"attributes allow at most {MAX_ATTRIBUTE_KEYS} top-level keys",
            )

        normalized: dict[str, ContextAttributeValue] = {}
        for key, item in value.items():
            normalized_key = _normalize_attribute_key(key)
            if normalized_key in normalized:
                raise _custom_error(
                    "context_attribute_duplicate_key",
                    "attribute keys must be unique after whitespace normalization",
                )
            normalized[normalized_key] = _validate_attribute_value(item)

        try:
            encoded = json.dumps(normalized, allow_nan=False, separators=(",", ":"))
        except (TypeError, ValueError) as error:
            raise _custom_error(
                "context_attributes_not_json_compatible",
                "attributes must contain finite JSON-compatible values",
            ) from error
        if len(encoded.encode("utf-8")) > MAX_ATTRIBUTES_JSON_BYTES:
            raise _custom_error(
                "context_attributes_payload_too_large",
                f"attributes must serialize to at most {MAX_ATTRIBUTES_JSON_BYTES} bytes",
            )
        return normalized

    @model_validator(mode="after")
    def normalize_identity(self) -> ContextReference:
        if self.id_kind == ContextIdKind.UUID:
            try:
                self.reference_id = str(UUID(self.reference_id))
            except ValueError as error:
                raise _custom_error(
                    "context_reference_invalid_uuid",
                    "reference_id must be a valid UUID when id_kind is uuid",
                ) from error
        elif self.source_system is None:
            raise _custom_error(
                "context_reference_source_system_required",
                "source_system is required when id_kind is external",
            )
        return self

    @property
    def link_key(self) -> ContextLinkKey:
        return (self.context_type.value, self.reference_id, self.relationship_role)

    @property
    def identity_signature(self) -> tuple[str, str | None, str | None]:
        return (self.id_kind.value, self.source_system, self.version)


def validate_context_references(
    references: Sequence[ContextReference],
) -> list[ContextReference]:
    """Validate one ordered collection without merging or selecting entries."""

    validated = list(references)
    seen: dict[ContextLinkKey, tuple[int, ContextReference]] = {}
    for index, reference in enumerate(validated):
        existing = seen.get(reference.link_key)
        if existing is None:
            seen[reference.link_key] = (index, reference)
            continue

        first_index, first = existing
        if reference == first:
            code = "context_reference_exact_duplicate"
        elif reference.identity_signature != first.identity_signature:
            code = "context_reference_identity_conflict"
        else:
            code = "context_reference_link_key_conflict"
        raise ContextReferenceCollectionError(
            code,
            first_index=first_index,
            second_index=index,
            key=reference.link_key,
        )
    return validated


def validate_context_organization_boundary(
    *,
    containing_organization_id: str,
    referenced_organization_id: str | None,
    verification_required: bool = True,
) -> None:
    """Fail closed for supplied cross-organization boundary evidence."""

    containing = containing_organization_id.strip()
    if not containing:
        raise ContextReferenceOrganizationError(
            "context_reference_containing_organization_invalid",
            "the containing Knowledge Object organization must be known",
        )
    if referenced_organization_id is None:
        if verification_required:
            raise ContextReferenceOrganizationError(
                "context_reference_organization_unverifiable",
                "the referenced organization is required for this verification",
            )
        return

    referenced = referenced_organization_id.strip()
    if not referenced:
        raise ContextReferenceOrganizationError(
            "context_reference_organization_unverifiable",
            "the referenced organization must not be blank",
        )
    if referenced != containing:
        raise ContextReferenceOrganizationError(
            "context_reference_cross_organization",
            "cross-organization context references are prohibited",
        )
