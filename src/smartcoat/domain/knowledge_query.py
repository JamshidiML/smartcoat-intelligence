"""Read-only Knowledge Object v2 collection and cursor contracts."""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import re
from collections.abc import Sequence
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    field_validator,
    model_validator,
)
from pydantic_core import PydanticCustomError

from smartcoat.domain.base import LifecycleState
from smartcoat.domain.context_references import ContextIdKind, ContextType
from smartcoat.domain.knowledge_objects import KnowledgeObjectType
from smartcoat.domain.knowledge_objects_v2 import ConfidentialityLevel

KNOWLEDGE_QUERY_CONTRACT_VERSION = "2"
KNOWLEDGE_QUERY_CURSOR_VERSION = 1
DEFAULT_PAGE_SIZE = 25
MIN_PAGE_SIZE = 1
MAX_PAGE_SIZE = 100
MAX_QUERY_TAGS = 16
MAX_IDENTIFIER_LENGTH = 512
MAX_TAG_LENGTH = 128
MAX_SOURCE_SYSTEM_LENGTH = 128
MAX_RELATIONSHIP_ROLE_LENGTH = 128
MIN_CURSOR_KEY_BYTES = 32

_CURSOR_TIMESTAMP_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z$")
_BASE64URL_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


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
            "knowledge_query_invalid_text",
            f"{field_name} must be a string",
        )
    normalized = value.strip()
    if not normalized:
        raise _custom_error(
            "knowledge_query_blank_text",
            f"{field_name} must not be blank",
        )
    if len(normalized) > max_length:
        raise _custom_error(
            "knowledge_query_text_too_long",
            f"{field_name} must contain at most {max_length} characters",
        )
    return normalized


def _normalize_optional_text(
    value: Any,
    *,
    field_name: str,
    max_length: int,
    casefold: bool = False,
) -> str | None:
    if value is None:
        return None
    normalized = _normalize_required_text(
        value,
        field_name=field_name,
        max_length=max_length,
    )
    return normalized.casefold() if casefold else normalized


def _normalize_aware_timestamp(value: datetime, *, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise _custom_error(
            "knowledge_query_naive_timestamp",
            f"{field_name} must be timezone-aware",
        )
    return value.astimezone(UTC)


class KnowledgeQuerySort(StrEnum):
    UPDATED_AT_DESC = "updated_at_desc"
    UPDATED_AT_ASC = "updated_at_asc"
    CREATED_AT_DESC = "created_at_desc"
    CREATED_AT_ASC = "created_at_asc"

    @property
    def timestamp_field(self) -> str:
        if self in {self.UPDATED_AT_DESC, self.UPDATED_AT_ASC}:
            return "updated_at"
        return "created_at"

    @property
    def descending(self) -> bool:
        return self in {self.UPDATED_AT_DESC, self.CREATED_AT_DESC}


class KnowledgeContextIdentityFilter(BaseModel):
    """Exact bounded context identity without display or evidence metadata."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    context_type: ContextType
    id_kind: ContextIdKind
    reference_id: str = Field(min_length=1, max_length=MAX_IDENTIFIER_LENGTH)
    source_system: str | None = Field(default=None, max_length=MAX_SOURCE_SYSTEM_LENGTH)
    relationship_role: str | None = Field(
        default=None,
        max_length=MAX_RELATIONSHIP_ROLE_LENGTH,
    )

    @field_validator("reference_id", mode="before")
    @classmethod
    def normalize_reference_id(cls, value: Any) -> str:
        return _normalize_required_text(
            value,
            field_name="reference_id",
            max_length=MAX_IDENTIFIER_LENGTH,
        )

    @field_validator("source_system", mode="before")
    @classmethod
    def normalize_source_system(cls, value: Any) -> str | None:
        return _normalize_optional_text(
            value,
            field_name="source_system",
            max_length=MAX_SOURCE_SYSTEM_LENGTH,
        )

    @field_validator("relationship_role", mode="before")
    @classmethod
    def normalize_relationship_role(cls, value: Any) -> str | None:
        return _normalize_optional_text(
            value,
            field_name="relationship_role",
            max_length=MAX_RELATIONSHIP_ROLE_LENGTH,
            casefold=True,
        )

    @model_validator(mode="after")
    def normalize_identity(self) -> KnowledgeContextIdentityFilter:
        if self.id_kind is ContextIdKind.UUID:
            try:
                canonical_reference_id = str(UUID(self.reference_id))
            except ValueError as error:
                raise _custom_error(
                    "knowledge_query_context_invalid_uuid",
                    "reference_id must be a valid UUID when id_kind is uuid",
                ) from error
            object.__setattr__(self, "reference_id", canonical_reference_id)
        elif self.source_system is None:
            raise _custom_error(
                "knowledge_query_context_source_system_required",
                "source_system is required when id_kind is external",
            )
        return self


class KnowledgeQueryFilters(BaseModel):
    """Canonical AND-combined collection filters."""

    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=True)

    knowledge_type: KnowledgeObjectType | None = None
    lifecycle_state: LifecycleState | None = None
    owner_id: str | None = Field(default=None, max_length=MAX_IDENTIFIER_LENGTH)
    tags_all: tuple[str, ...] = Field(default_factory=tuple, max_length=MAX_QUERY_TAGS)
    context: KnowledgeContextIdentityFilter | None = None
    created_from: datetime | None = None
    created_before: datetime | None = None
    updated_from: datetime | None = None
    updated_before: datetime | None = None

    @field_validator("owner_id", mode="before")
    @classmethod
    def normalize_owner_id(cls, value: Any) -> str | None:
        return _normalize_optional_text(
            value,
            field_name="owner_id",
            max_length=MAX_IDENTIFIER_LENGTH,
        )

    @field_validator("tags_all", mode="before")
    @classmethod
    def normalize_tags_all(cls, value: Any) -> tuple[str, ...]:
        if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
            raise _custom_error(
                "knowledge_query_invalid_tags",
                "tags_all must be an ordered collection of strings",
            )
        if len(value) > MAX_QUERY_TAGS:
            raise _custom_error(
                "knowledge_query_too_many_tags",
                f"tags_all must contain at most {MAX_QUERY_TAGS} tags",
            )

        normalized: list[str] = []
        seen: set[str] = set()
        for item in value:
            tag = _normalize_required_text(
                item,
                field_name="tags_all item",
                max_length=MAX_TAG_LENGTH,
            )
            if tag in seen:
                raise _custom_error(
                    "knowledge_query_duplicate_tag",
                    "tags_all must not contain duplicate values",
                )
            normalized.append(tag)
            seen.add(tag)
        return tuple(normalized)

    @field_validator(
        "created_from",
        "created_before",
        "updated_from",
        "updated_before",
    )
    @classmethod
    def normalize_timestamps(cls, value: datetime | None, info: ValidationInfo) -> datetime | None:
        if value is None:
            return None
        return _normalize_aware_timestamp(
            value,
            field_name=info.field_name or "query timestamp",
        )

    @model_validator(mode="after")
    def validate_time_ranges(self) -> KnowledgeQueryFilters:
        if (
            self.created_from is not None
            and self.created_before is not None
            and self.created_from >= self.created_before
        ):
            raise _custom_error(
                "knowledge_query_created_range_invalid",
                "created_from must precede created_before",
            )
        if (
            self.updated_from is not None
            and self.updated_before is not None
            and self.updated_from >= self.updated_before
        ):
            raise _custom_error(
                "knowledge_query_updated_range_invalid",
                "updated_from must precede updated_before",
            )
        return self


class KnowledgeObjectV2Query(BaseModel):
    """One bounded read-only collection request."""

    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=True)

    organization_id: str = Field(min_length=1, max_length=MAX_IDENTIFIER_LENGTH)
    filters: KnowledgeQueryFilters = Field(default_factory=KnowledgeQueryFilters)
    sort: KnowledgeQuerySort = KnowledgeQuerySort.UPDATED_AT_DESC
    page_size: int = Field(default=DEFAULT_PAGE_SIZE, ge=MIN_PAGE_SIZE, le=MAX_PAGE_SIZE)
    cursor: str | None = None

    @field_validator("organization_id", mode="before")
    @classmethod
    def normalize_organization_id(cls, value: Any) -> str:
        return _normalize_required_text(
            value,
            field_name="organization_id",
            max_length=MAX_IDENTIFIER_LENGTH,
        )

    @field_validator("page_size", mode="before")
    @classmethod
    def validate_page_size_type(cls, value: Any) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise _custom_error(
                "knowledge_query_page_size_invalid",
                "page_size must be an integer, not a boolean or coercible value",
            )
        return value

    @field_validator("cursor", mode="before")
    @classmethod
    def validate_cursor_text(cls, value: Any) -> str | None:
        if value is None:
            return None
        return _normalize_required_text(
            value,
            field_name="cursor",
            max_length=4096,
        )


class KnowledgeObjectV2CollectionOwner(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    owner_id: str = Field(min_length=1, max_length=MAX_IDENTIFIER_LENGTH)
    role: str = Field(min_length=1, max_length=128)


class KnowledgeObjectV2CollectionItem(BaseModel):
    """Detached root-only collection summary."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    object_id: UUID
    revision: int = Field(ge=1)
    lifecycle_state: LifecycleState
    title: str = Field(min_length=1, max_length=256)
    knowledge_type: KnowledgeObjectType
    owner: KnowledgeObjectV2CollectionOwner
    confidentiality: ConfidentialityLevel
    created_at: datetime
    updated_at: datetime

    @field_validator("created_at", "updated_at")
    @classmethod
    def normalize_timestamps(cls, value: datetime, info: ValidationInfo) -> datetime:
        return _normalize_aware_timestamp(
            value,
            field_name=info.field_name or "collection timestamp",
        )

    @model_validator(mode="after")
    def validate_timestamp_order(self) -> KnowledgeObjectV2CollectionItem:
        if self.updated_at < self.created_at:
            raise _custom_error(
                "knowledge_query_updated_before_created",
                "updated_at must not precede created_at",
            )
        return self


class KnowledgeQueryCursorPosition(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    timestamp: datetime
    object_id: UUID

    @field_validator("timestamp")
    @classmethod
    def normalize_timestamp(cls, value: datetime) -> datetime:
        return _normalize_aware_timestamp(value, field_name="cursor timestamp")


class KnowledgeObjectV2QueryRepositoryPage(BaseModel):
    """Internal detached result passed from repository to service."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    items: tuple[KnowledgeObjectV2CollectionItem, ...]
    has_more: bool
    final_position: KnowledgeQueryCursorPosition | None

    @model_validator(mode="after")
    def validate_position(self) -> KnowledgeObjectV2QueryRepositoryPage:
        if self.items and self.final_position is None:
            raise ValueError("a non-empty repository page requires a final cursor position")
        if not self.items and self.final_position is not None:
            raise ValueError("an empty repository page must not carry a cursor position")
        if self.has_more and not self.items:
            raise ValueError("has_more requires at least one returned item")
        return self


class KnowledgeObjectV2Page(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    items: tuple[KnowledgeObjectV2CollectionItem, ...]
    returned_count: int = Field(ge=0)
    requested_page_size: int = Field(ge=MIN_PAGE_SIZE, le=MAX_PAGE_SIZE)
    has_more: bool
    next_cursor: str | None
    applied_sort: KnowledgeQuerySort

    @model_validator(mode="after")
    def validate_page_metadata(self) -> KnowledgeObjectV2Page:
        if self.returned_count != len(self.items):
            raise ValueError("returned_count must equal the number of items")
        if self.returned_count > self.requested_page_size:
            raise ValueError("returned_count must not exceed requested_page_size")
        if self.has_more != (self.next_cursor is not None):
            raise ValueError("next_cursor must be present exactly when has_more is true")
        return self


class KnowledgeQueryCursorError(ValueError):
    """Typed deterministic cursor failure."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


def knowledge_query_fingerprint(
    *,
    organization_id: str,
    filters: KnowledgeQueryFilters,
    sort: KnowledgeQuerySort,
    contract_version: str = KNOWLEDGE_QUERY_CONTRACT_VERSION,
) -> str:
    """Hash the complete normalized query without page size or cursor."""

    canonical = json.dumps(
        {
            "contract_version": contract_version,
            "filters": filters.model_dump(mode="json"),
            "organization_id": organization_id,
            "sort": sort.value,
        },
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _encode_base64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _decode_base64url(value: str) -> bytes:
    if _BASE64URL_PATTERN.fullmatch(value) is None:
        raise ValueError("non-canonical base64url value")
    padded = value + "=" * (-len(value) % 4)
    try:
        decoded = base64.b64decode(
            padded.encode("ascii"),
            altchars=b"-_",
            validate=True,
        )
    except (binascii.Error, ValueError) as error:
        raise ValueError("invalid base64url value") from error
    if _encode_base64url(decoded) != value:
        raise ValueError("non-canonical base64url value")
    return decoded


def _encode_cursor_timestamp(value: datetime) -> str:
    normalized = _normalize_aware_timestamp(value, field_name="cursor timestamp")
    return normalized.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _decode_cursor_timestamp(value: Any) -> datetime:
    if not isinstance(value, str) or _CURSOR_TIMESTAMP_PATTERN.fullmatch(value) is None:
        raise ValueError("cursor timestamp is not canonical UTC microsecond text")
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=UTC)


class KnowledgeQueryCursorCodec:
    """Versioned tamper-evident cursor codec; cursors are not encrypted tokens."""

    def __init__(self, signing_key: bytes) -> None:
        if not isinstance(signing_key, bytes) or len(signing_key) < MIN_CURSOR_KEY_BYTES:
            raise ValueError(
                f"cursor signing key must be bytes with at least {MIN_CURSOR_KEY_BYTES} bytes"
            )
        self._signing_key = bytes(signing_key)

    def encode(
        self,
        *,
        sort: KnowledgeQuerySort,
        position: KnowledgeQueryCursorPosition,
        query_fingerprint: str,
    ) -> str:
        if _SHA256_PATTERN.fullmatch(query_fingerprint) is None:
            raise ValueError("query_fingerprint must be a lowercase SHA-256 digest")
        payload = json.dumps(
            {
                "fingerprint": query_fingerprint,
                "object_id": str(position.object_id),
                "sort": sort.value,
                "timestamp": _encode_cursor_timestamp(position.timestamp),
                "version": KNOWLEDGE_QUERY_CURSOR_VERSION,
            },
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        signature = hmac.digest(self._signing_key, payload, "sha256")
        return f"{_encode_base64url(payload)}.{_encode_base64url(signature)}"

    def decode(
        self,
        cursor: str,
        *,
        expected_sort: KnowledgeQuerySort,
        expected_query_fingerprint: str,
    ) -> KnowledgeQueryCursorPosition:
        try:
            payload_text, signature_text = cursor.split(".")
        except (AttributeError, ValueError) as error:
            raise KnowledgeQueryCursorError(
                "knowledge_query_cursor_malformed",
                "cursor envelope must contain one payload and one signature",
            ) from error

        try:
            payload = _decode_base64url(payload_text)
            signature = _decode_base64url(signature_text)
        except ValueError as error:
            raise KnowledgeQueryCursorError(
                "knowledge_query_cursor_malformed",
                "cursor envelope contains invalid base64url",
            ) from error

        expected_signature = hmac.digest(self._signing_key, payload, "sha256")
        if not hmac.compare_digest(signature, expected_signature):
            raise KnowledgeQueryCursorError(
                "knowledge_query_cursor_signature_invalid",
                "cursor signature verification failed",
            )

        try:
            decoded = json.loads(payload)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise KnowledgeQueryCursorError(
                "knowledge_query_cursor_malformed",
                "signed cursor payload is not valid JSON",
            ) from error
        if not isinstance(decoded, dict) or set(decoded) != {
            "fingerprint",
            "object_id",
            "sort",
            "timestamp",
            "version",
        }:
            raise KnowledgeQueryCursorError(
                "knowledge_query_cursor_malformed",
                "signed cursor payload has an invalid field set",
            )

        if (
            type(decoded["version"]) is not int
            or decoded["version"] != KNOWLEDGE_QUERY_CURSOR_VERSION
        ):
            raise KnowledgeQueryCursorError(
                "knowledge_query_cursor_version_unsupported",
                "cursor schema version is not supported",
            )

        try:
            cursor_sort = KnowledgeQuerySort(decoded["sort"])
            timestamp = _decode_cursor_timestamp(decoded["timestamp"])
            object_id_text = decoded["object_id"]
            if not isinstance(object_id_text, str):
                raise ValueError("object_id is not text")
            object_id = UUID(object_id_text)
            if str(object_id) != object_id_text:
                raise ValueError("object_id is not canonical UUID text")
            fingerprint = decoded["fingerprint"]
            if not isinstance(fingerprint, str) or _SHA256_PATTERN.fullmatch(fingerprint) is None:
                raise ValueError("fingerprint is not a SHA-256 digest")
        except (TypeError, ValueError) as error:
            raise KnowledgeQueryCursorError(
                "knowledge_query_cursor_position_invalid",
                "cursor sort or keyset position is invalid",
            ) from error

        if cursor_sort is not expected_sort or fingerprint != expected_query_fingerprint:
            raise KnowledgeQueryCursorError(
                "knowledge_query_cursor_query_mismatch",
                "cursor is bound to a different organization, filter set, sort, or contract",
            )
        return KnowledgeQueryCursorPosition(timestamp=timestamp, object_id=object_id)
