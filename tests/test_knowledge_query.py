from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from smartcoat.domain.base import LifecycleState
from smartcoat.domain.context_references import ContextIdKind, ContextType
from smartcoat.domain.knowledge_objects import KnowledgeObjectType
from smartcoat.domain.knowledge_objects_v2 import ConfidentialityLevel
from smartcoat.domain.knowledge_query import (
    MAX_PAGE_SIZE,
    MAX_QUERY_TAGS,
    MAX_TAG_LENGTH,
    KnowledgeContextIdentityFilter,
    KnowledgeObjectV2CollectionItem,
    KnowledgeObjectV2CollectionOwner,
    KnowledgeObjectV2Page,
    KnowledgeObjectV2Query,
    KnowledgeQueryCursorCodec,
    KnowledgeQueryCursorError,
    KnowledgeQueryCursorPosition,
    KnowledgeQueryFilters,
    KnowledgeQuerySort,
    knowledge_query_fingerprint,
)

SYNTHETIC_KEY = b"synthetic-t06-cursor-signing-key-0000000000000001"
NOW = datetime(2026, 7, 26, 12, 30, 45, 123456, tzinfo=UTC)
OBJECT_ID = UUID("00000000-0000-0000-0000-000000000123")


def _validation_error_type(factory: object) -> str:
    with pytest.raises(ValidationError) as captured:
        factory()  # type: ignore[operator]
    return captured.value.errors()[0]["type"]


def _item(
    *,
    object_id: UUID = OBJECT_ID,
    created_at: datetime = NOW,
    updated_at: datetime = NOW,
) -> KnowledgeObjectV2CollectionItem:
    return KnowledgeObjectV2CollectionItem(
        object_id=object_id,
        revision=3,
        lifecycle_state=LifecycleState.REVIEWED,
        title="Synthetic collection summary",
        knowledge_type=KnowledgeObjectType.FINDING,
        owner=KnowledgeObjectV2CollectionOwner(
            owner_id="synthetic-owner",
            role="reviewer",
        ),
        confidentiality=ConfidentialityLevel.INTERNAL,
        created_at=created_at,
        updated_at=updated_at,
    )


def _signed_cursor_payload(payload: bytes) -> str:
    encoded_payload = base64.urlsafe_b64encode(payload).rstrip(b"=").decode()
    signature = hmac.digest(SYNTHETIC_KEY, payload, "sha256")
    encoded_signature = base64.urlsafe_b64encode(signature).rstrip(b"=").decode()
    return f"{encoded_payload}.{encoded_signature}"


def _cursor_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "fingerprint": hashlib.sha256(b"synthetic-query").hexdigest(),
        "object_id": str(OBJECT_ID),
        "sort": KnowledgeQuerySort.UPDATED_AT_DESC.value,
        "timestamp": "2026-07-26T12:30:45.123456Z",
        "version": 1,
    }
    payload.update(overrides)
    return payload


def _signed_json_cursor(**overrides: object) -> str:
    payload = json.dumps(
        _cursor_payload(**overrides),
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    return _signed_cursor_payload(payload)


def test_empty_filters_and_default_query_are_bounded() -> None:
    query = KnowledgeObjectV2Query(organization_id=" synthetic-org ")

    assert query.organization_id == "synthetic-org"
    assert query.filters == KnowledgeQueryFilters()
    assert query.sort is KnowledgeQuerySort.UPDATED_AT_DESC
    assert query.page_size == 25
    assert query.cursor is None


def test_every_filter_normalizes_and_combines_without_aliasing() -> None:
    tags = ["Tag-A", "tag-b"]
    filters = KnowledgeQueryFilters(
        knowledge_type=KnowledgeObjectType.FINDING,
        lifecycle_state=LifecycleState.REVIEWED,
        owner_id=" synthetic-owner ",
        tags_all=tags,
        context=KnowledgeContextIdentityFilter(
            context_type=ContextType.MATERIAL,
            id_kind=ContextIdKind.EXTERNAL,
            reference_id=" material-42 ",
            source_system=" synthetic-catalog ",
            relationship_role=" Primary ",
        ),
        created_from=NOW,
        created_before=NOW + timedelta(days=1),
        updated_from=NOW + timedelta(hours=1),
        updated_before=NOW + timedelta(days=2),
    )
    tags.append("late-mutation")

    assert filters.owner_id == "synthetic-owner"
    assert filters.tags_all == ("Tag-A", "tag-b")
    assert filters.context is not None
    assert filters.context.reference_id == "material-42"
    assert filters.context.source_system == "synthetic-catalog"
    assert filters.context.relationship_role == "primary"


@pytest.mark.parametrize(
    ("payload", "error_type"),
    [
        ({"owner_id": "   "}, "knowledge_query_blank_text"),
        ({"tags_all": ["duplicate", "duplicate"]}, "knowledge_query_duplicate_tag"),
        ({"tags_all": [""]}, "knowledge_query_blank_text"),
        (
            {"tags_all": ["x" * (MAX_TAG_LENGTH + 1)]},
            "knowledge_query_text_too_long",
        ),
        (
            {"tags_all": [f"tag-{index}" for index in range(MAX_QUERY_TAGS + 1)]},
            "knowledge_query_too_many_tags",
        ),
    ],
)
def test_invalid_owner_and_tag_filters_are_rejected(
    payload: dict[str, object],
    error_type: str,
) -> None:
    assert _validation_error_type(lambda: KnowledgeQueryFilters(**payload)) == error_type


def test_tag_matching_contract_remains_case_sensitive() -> None:
    filters = KnowledgeQueryFilters(tags_all=["Synthetic", "synthetic"])
    assert filters.tags_all == ("Synthetic", "synthetic")


def test_context_uuid_is_canonical_and_external_source_is_required() -> None:
    identity = KnowledgeContextIdentityFilter(
        context_type=ContextType.PROJECT,
        id_kind=ContextIdKind.UUID,
        reference_id="{12345678-1234-5678-1234-567812345678}",
    )
    assert identity.reference_id == "12345678-1234-5678-1234-567812345678"

    assert (
        _validation_error_type(
            lambda: KnowledgeContextIdentityFilter(
                context_type=ContextType.PROJECT,
                id_kind=ContextIdKind.EXTERNAL,
                reference_id="project-1",
            )
        )
        == "knowledge_query_context_source_system_required"
    )


def test_context_filter_forbids_display_or_attribute_payloads() -> None:
    assert (
        _validation_error_type(
            lambda: KnowledgeContextIdentityFilter(
                context_type=ContextType.PROJECT,
                id_kind=ContextIdKind.EXTERNAL,
                reference_id="project-1",
                source_system="synthetic",
                display_name="not-authorized",  # type: ignore[call-arg]
            )
        )
        == "extra_forbidden"
    )


def test_aware_timestamps_normalize_to_utc_and_ranges_are_half_open() -> None:
    source = datetime(
        2026,
        7,
        26,
        14,
        30,
        45,
        123456,
        tzinfo=timezone(timedelta(hours=2)),
    )
    filters = KnowledgeQueryFilters(
        created_from=source,
        created_before=source + timedelta(seconds=1),
        updated_from=source,
        updated_before=source + timedelta(seconds=1),
    )
    assert filters.created_from == NOW
    assert filters.updated_from == NOW


@pytest.mark.parametrize(
    "field_name",
    ["created_from", "created_before", "updated_from", "updated_before"],
)
def test_naive_timestamps_are_rejected(field_name: str) -> None:
    assert (
        _validation_error_type(
            lambda: KnowledgeQueryFilters(**{field_name: datetime(2026, 7, 26, 12, 0)})
        )
        == "knowledge_query_naive_timestamp"
    )


@pytest.mark.parametrize(
    ("payload", "error_type"),
    [
        (
            {"created_from": NOW, "created_before": NOW},
            "knowledge_query_created_range_invalid",
        ),
        (
            {"updated_from": NOW + timedelta(seconds=1), "updated_before": NOW},
            "knowledge_query_updated_range_invalid",
        ),
    ],
)
def test_invalid_timestamp_ranges_are_rejected(
    payload: dict[str, datetime],
    error_type: str,
) -> None:
    assert _validation_error_type(lambda: KnowledgeQueryFilters(**payload)) == error_type


@pytest.mark.parametrize("sort", list(KnowledgeQuerySort))
def test_all_four_sort_modes_are_bounded(sort: KnowledgeQuerySort) -> None:
    query = KnowledgeObjectV2Query(
        organization_id="synthetic-org",
        sort=sort,
        page_size=MAX_PAGE_SIZE,
    )
    assert query.sort is sort
    assert query.page_size == MAX_PAGE_SIZE


@pytest.mark.parametrize("page_size", [True, False, 1.0, "25", None])
def test_page_size_rejects_boolean_and_non_integer_values(page_size: object) -> None:
    assert (
        _validation_error_type(
            lambda: KnowledgeObjectV2Query(
                organization_id="synthetic-org",
                page_size=page_size,  # type: ignore[arg-type]
            )
        )
        == "knowledge_query_page_size_invalid"
    )


@pytest.mark.parametrize("page_size", [0, -1, MAX_PAGE_SIZE + 1])
def test_page_size_rejects_out_of_bounds_values(page_size: int) -> None:
    assert _validation_error_type(
        lambda: KnowledgeObjectV2Query(
            organization_id="synthetic-org",
            page_size=page_size,
        )
    ) in {"greater_than_equal", "less_than_equal"}


def test_query_page_and_nested_items_are_frozen_and_detached() -> None:
    item = _item()
    page = KnowledgeObjectV2Page(
        items=[item],
        returned_count=1,
        requested_page_size=1,
        has_more=False,
        next_cursor=None,
        applied_sort=KnowledgeQuerySort.UPDATED_AT_DESC,
    )

    with pytest.raises(ValidationError):
        page.returned_count = 2
    with pytest.raises(ValidationError):
        page.items[0].title = "mutated"
    with pytest.raises(ValidationError):
        page.items[0].owner.role = "mutated"
    assert isinstance(page.items, tuple)


def test_page_metadata_invariants_are_enforced() -> None:
    with pytest.raises(ValidationError, match="returned_count"):
        KnowledgeObjectV2Page(
            items=(_item(),),
            returned_count=0,
            requested_page_size=1,
            has_more=False,
            next_cursor=None,
            applied_sort=KnowledgeQuerySort.UPDATED_AT_DESC,
        )
    with pytest.raises(ValidationError, match="next_cursor"):
        KnowledgeObjectV2Page(
            items=(_item(),),
            returned_count=1,
            requested_page_size=1,
            has_more=True,
            next_cursor=None,
            applied_sort=KnowledgeQuerySort.UPDATED_AT_DESC,
        )


def test_cursor_round_trip_uses_canonical_microseconds() -> None:
    codec = KnowledgeQueryCursorCodec(SYNTHETIC_KEY)
    fingerprint = hashlib.sha256(b"synthetic-query").hexdigest()
    position = KnowledgeQueryCursorPosition(timestamp=NOW, object_id=OBJECT_ID)

    cursor = codec.encode(
        sort=KnowledgeQuerySort.UPDATED_AT_DESC,
        position=position,
        query_fingerprint=fingerprint,
    )
    decoded = codec.decode(
        cursor,
        expected_sort=KnowledgeQuerySort.UPDATED_AT_DESC,
        expected_query_fingerprint=fingerprint,
    )

    assert decoded == position
    payload = json.loads(base64.urlsafe_b64decode(cursor.split(".")[0] + "==").decode())
    assert payload["timestamp"] == "2026-07-26T12:30:45.123456Z"


def test_cursor_payload_contains_only_position_and_fingerprint_fields() -> None:
    query = KnowledgeObjectV2Query(
        organization_id="private-synthetic-org",
        filters=KnowledgeQueryFilters(
            owner_id="private-synthetic-owner",
            tags_all=("private-synthetic-tag",),
        ),
    )
    fingerprint = knowledge_query_fingerprint(
        organization_id=query.organization_id,
        filters=query.filters,
        sort=query.sort,
    )
    cursor = KnowledgeQueryCursorCodec(SYNTHETIC_KEY).encode(
        sort=query.sort,
        position=KnowledgeQueryCursorPosition(timestamp=NOW, object_id=OBJECT_ID),
        query_fingerprint=fingerprint,
    )
    payload = base64.urlsafe_b64decode(cursor.split(".")[0] + "==").decode()

    assert set(json.loads(payload)) == {
        "fingerprint",
        "object_id",
        "sort",
        "timestamp",
        "version",
    }
    assert "private-synthetic" not in payload


def test_cursor_requires_an_injected_key_of_at_least_32_bytes() -> None:
    with pytest.raises(ValueError, match="at least 32"):
        KnowledgeQueryCursorCodec(b"short")
    with pytest.raises(ValueError, match="must be bytes"):
        KnowledgeQueryCursorCodec("x" * 64)  # type: ignore[arg-type]


@pytest.mark.parametrize("cursor", ["not-an-envelope", "***.***", "a.b.c"])
def test_malformed_cursor_envelopes_use_one_typed_error(cursor: str) -> None:
    codec = KnowledgeQueryCursorCodec(SYNTHETIC_KEY)
    with pytest.raises(KnowledgeQueryCursorError) as captured:
        codec.decode(
            cursor,
            expected_sort=KnowledgeQuerySort.UPDATED_AT_DESC,
            expected_query_fingerprint=hashlib.sha256(b"synthetic-query").hexdigest(),
        )
    assert captured.value.code == "knowledge_query_cursor_malformed"


def test_wrong_key_and_modified_signature_are_rejected() -> None:
    fingerprint = hashlib.sha256(b"synthetic-query").hexdigest()
    cursor = KnowledgeQueryCursorCodec(SYNTHETIC_KEY).encode(
        sort=KnowledgeQuerySort.UPDATED_AT_DESC,
        position=KnowledgeQueryCursorPosition(timestamp=NOW, object_id=OBJECT_ID),
        query_fingerprint=fingerprint,
    )
    wrong_key_codec = KnowledgeQueryCursorCodec(b"another-synthetic-signing-key-000000000000000")
    with pytest.raises(KnowledgeQueryCursorError) as captured:
        wrong_key_codec.decode(
            cursor,
            expected_sort=KnowledgeQuerySort.UPDATED_AT_DESC,
            expected_query_fingerprint=fingerprint,
        )
    assert captured.value.code == "knowledge_query_cursor_signature_invalid"

    payload = cursor.split(".")[0]
    bad_signature = base64.urlsafe_b64encode(b"x" * 32).rstrip(b"=").decode()
    with pytest.raises(KnowledgeQueryCursorError) as captured:
        KnowledgeQueryCursorCodec(SYNTHETIC_KEY).decode(
            f"{payload}.{bad_signature}",
            expected_sort=KnowledgeQuerySort.UPDATED_AT_DESC,
            expected_query_fingerprint=fingerprint,
        )
    assert captured.value.code == "knowledge_query_cursor_signature_invalid"


def test_signed_malformed_json_is_rejected() -> None:
    with pytest.raises(KnowledgeQueryCursorError) as captured:
        KnowledgeQueryCursorCodec(SYNTHETIC_KEY).decode(
            _signed_cursor_payload(b"{"),
            expected_sort=KnowledgeQuerySort.UPDATED_AT_DESC,
            expected_query_fingerprint=hashlib.sha256(b"synthetic-query").hexdigest(),
        )
    assert captured.value.code == "knowledge_query_cursor_malformed"


def test_unsupported_cursor_version_is_rejected() -> None:
    for version in (999, True, "1"):
        with pytest.raises(KnowledgeQueryCursorError) as captured:
            KnowledgeQueryCursorCodec(SYNTHETIC_KEY).decode(
                _signed_json_cursor(version=version),
                expected_sort=KnowledgeQuerySort.UPDATED_AT_DESC,
                expected_query_fingerprint=hashlib.sha256(b"synthetic-query").hexdigest(),
            )
        assert captured.value.code == "knowledge_query_cursor_version_unsupported"


@pytest.mark.parametrize(
    "overrides",
    [
        {"timestamp": "2026-07-26T12:30:45Z"},
        {"timestamp": "not-a-time"},
        {"object_id": "not-a-uuid"},
        {"object_id": 123},
        {"object_id": str(uuid4()).upper()},
        {"fingerprint": "not-a-digest"},
        {"sort": "title_desc"},
    ],
)
def test_invalid_cursor_positions_are_rejected(overrides: dict[str, object]) -> None:
    with pytest.raises(KnowledgeQueryCursorError) as captured:
        KnowledgeQueryCursorCodec(SYNTHETIC_KEY).decode(
            _signed_json_cursor(**overrides),
            expected_sort=KnowledgeQuerySort.UPDATED_AT_DESC,
            expected_query_fingerprint=hashlib.sha256(b"synthetic-query").hexdigest(),
        )
    assert captured.value.code == "knowledge_query_cursor_position_invalid"


def test_fingerprint_binds_contract_organization_filters_and_sort_not_page_size() -> None:
    base_filters = KnowledgeQueryFilters(tags_all=("synthetic",))
    base = knowledge_query_fingerprint(
        organization_id="synthetic-org",
        filters=base_filters,
        sort=KnowledgeQuerySort.UPDATED_AT_DESC,
    )
    assert base == knowledge_query_fingerprint(
        organization_id="synthetic-org",
        filters=base_filters,
        sort=KnowledgeQuerySort.UPDATED_AT_DESC,
    )
    assert base != knowledge_query_fingerprint(
        organization_id="synthetic-other",
        filters=base_filters,
        sort=KnowledgeQuerySort.UPDATED_AT_DESC,
    )
    assert base != knowledge_query_fingerprint(
        organization_id="synthetic-org",
        filters=KnowledgeQueryFilters(tags_all=("other",)),
        sort=KnowledgeQuerySort.UPDATED_AT_DESC,
    )
    assert base != knowledge_query_fingerprint(
        organization_id="synthetic-org",
        filters=base_filters,
        sort=KnowledgeQuerySort.CREATED_AT_DESC,
    )
    assert base != knowledge_query_fingerprint(
        organization_id="synthetic-org",
        filters=base_filters,
        sort=KnowledgeQuerySort.UPDATED_AT_DESC,
        contract_version="future",
    )


def test_cursor_query_mismatch_and_page_size_independence() -> None:
    codec = KnowledgeQueryCursorCodec(SYNTHETIC_KEY)
    filters = KnowledgeQueryFilters(tags_all=("synthetic",))
    fingerprint = knowledge_query_fingerprint(
        organization_id="synthetic-org",
        filters=filters,
        sort=KnowledgeQuerySort.UPDATED_AT_DESC,
    )
    cursor = codec.encode(
        sort=KnowledgeQuerySort.UPDATED_AT_DESC,
        position=KnowledgeQueryCursorPosition(timestamp=NOW, object_id=OBJECT_ID),
        query_fingerprint=fingerprint,
    )

    for mismatched in (
        knowledge_query_fingerprint(
            organization_id="other-org",
            filters=filters,
            sort=KnowledgeQuerySort.UPDATED_AT_DESC,
        ),
        knowledge_query_fingerprint(
            organization_id="synthetic-org",
            filters=KnowledgeQueryFilters(tags_all=("other",)),
            sort=KnowledgeQuerySort.UPDATED_AT_DESC,
        ),
    ):
        with pytest.raises(KnowledgeQueryCursorError) as captured:
            codec.decode(
                cursor,
                expected_sort=KnowledgeQuerySort.UPDATED_AT_DESC,
                expected_query_fingerprint=mismatched,
            )
        assert captured.value.code == "knowledge_query_cursor_query_mismatch"

    with pytest.raises(KnowledgeQueryCursorError) as captured:
        codec.decode(
            cursor,
            expected_sort=KnowledgeQuerySort.CREATED_AT_DESC,
            expected_query_fingerprint=fingerprint,
        )
    assert captured.value.code == "knowledge_query_cursor_query_mismatch"

    first_query = KnowledgeObjectV2Query(
        organization_id="synthetic-org",
        filters=filters,
        page_size=1,
    )
    second_query = first_query.model_copy(update={"page_size": 100, "cursor": cursor})
    assert knowledge_query_fingerprint(
        organization_id=first_query.organization_id,
        filters=first_query.filters,
        sort=first_query.sort,
    ) == knowledge_query_fingerprint(
        organization_id=second_query.organization_id,
        filters=second_query.filters,
        sort=second_query.sort,
    )
    assert (
        codec.decode(
            second_query.cursor or "",
            expected_sort=second_query.sort,
            expected_query_fingerprint=fingerprint,
        ).object_id
        == OBJECT_ID
    )
