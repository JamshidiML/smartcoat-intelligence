from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError

from smartcoat.domain.base import LifecycleState
from smartcoat.domain.knowledge_audit import (
    KnowledgeAuditChangedField,
    KnowledgeAuditEvent,
    KnowledgeAuditEventType,
    audit_event_type_for_lifecycle_action,
    audit_request_from_lifecycle_plan,
)
from smartcoat.domain.knowledge_lifecycle import (
    KnowledgeAuditAppendRequest as LifecycleAuditAppendRequest,
)
from smartcoat.domain.knowledge_lifecycle import (
    LifecycleAction,
    LifecycleActor,
    LifecycleMutationPlan,
    LifecycleReviewProjection,
)

NOW = datetime(2026, 7, 20, 12, 0, tzinfo=UTC)


def _event(**overrides: object) -> KnowledgeAuditEvent:
    payload: dict[str, object] = {
        "event_id": uuid4(),
        "organization_id": "synthetic-org",
        "object_id": uuid4(),
        "event_type": KnowledgeAuditEventType.UPDATE,
        "lifecycle_action": None,
        "actor_id": "synthetic-actor",
        "actor_role": "knowledge_author",
        "occurred_at": NOW,
        "recorded_at": NOW + timedelta(seconds=1),
        "correlation_id": uuid4(),
        "previous_lifecycle": LifecycleState.DRAFT,
        "resulting_lifecycle": LifecycleState.DRAFT,
        "previous_revision": 1,
        "resulting_revision": 2,
        "reason_or_note": "Synthetic bounded change.",
        "changed_fields": [KnowledgeAuditChangedField.CONTENT],
        "audit_sequence": 1,
    }
    payload.update(overrides)
    return KnowledgeAuditEvent.model_validate(payload)


@pytest.mark.parametrize(
    ("action", "event_type"),
    [
        (LifecycleAction.SUBMIT_DRAFT, KnowledgeAuditEventType.TRANSITION),
        (
            LifecycleAction.REQUEST_CAPTURED_CORRECTION,
            KnowledgeAuditEventType.CORRECTION_REQUEST,
        ),
        (LifecycleAction.COMPLETE_REVIEW, KnowledgeAuditEventType.TRANSITION),
        (LifecycleAction.REJECT_CAPTURED, KnowledgeAuditEventType.REJECT),
        (
            LifecycleAction.REQUEST_REVIEWED_CORRECTION,
            KnowledgeAuditEventType.CORRECTION_REQUEST,
        ),
        (LifecycleAction.VALIDATE_REVIEWED, KnowledgeAuditEventType.TRANSITION),
        (LifecycleAction.REJECT_REVIEWED, KnowledgeAuditEventType.REJECT),
        (
            LifecycleAction.REQUEST_VALIDATED_CORRECTION,
            KnowledgeAuditEventType.CORRECTION_REQUEST,
        ),
        (LifecycleAction.APPROVE_VALIDATED, KnowledgeAuditEventType.APPROVE),
        (LifecycleAction.REJECT_VALIDATED, KnowledgeAuditEventType.REJECT),
        (LifecycleAction.DEPRECATE_APPROVED, KnowledgeAuditEventType.DEPRECATE),
        (LifecycleAction.REOPEN_REJECTED, KnowledgeAuditEventType.REOPEN),
        (LifecycleAction.DELETE_DRAFT, KnowledgeAuditEventType.DRAFT_DELETE),
    ],
)
def test_every_lifecycle_action_has_one_canonical_event_type(
    action: LifecycleAction,
    event_type: KnowledgeAuditEventType,
) -> None:
    assert audit_event_type_for_lifecycle_action(action) is event_type


def test_create_update_and_delete_revision_contracts() -> None:
    created = _event(
        event_type=KnowledgeAuditEventType.CREATE,
        previous_lifecycle=None,
        previous_revision=None,
        resulting_lifecycle=LifecycleState.DRAFT,
        resulting_revision=1,
        changed_fields=["title", "evidence", "revision"],
    )
    updated = _event()
    deleted = _event(
        event_type=KnowledgeAuditEventType.DRAFT_DELETE,
        lifecycle_action=LifecycleAction.DELETE_DRAFT,
        previous_lifecycle=LifecycleState.DRAFT,
        previous_revision=2,
        resulting_lifecycle=None,
        resulting_revision=None,
        changed_fields=[],
    )

    assert created.previous_revision is None
    assert updated.resulting_revision == updated.previous_revision + 1
    assert deleted.resulting_revision is None


def test_lifecycle_event_must_match_action_pair_and_revision() -> None:
    accepted = _event(
        event_type=KnowledgeAuditEventType.APPROVE,
        lifecycle_action=LifecycleAction.APPROVE_VALIDATED,
        previous_lifecycle=LifecycleState.VALIDATED,
        resulting_lifecycle=LifecycleState.APPROVED,
        previous_revision=6,
        resulting_revision=7,
        changed_fields=["lifecycle_state", "revision"],
    )
    assert accepted.event_type is KnowledgeAuditEventType.APPROVE

    with pytest.raises(ValidationError, match="exactly match"):
        _event(
            event_type=KnowledgeAuditEventType.APPROVE,
            lifecycle_action=LifecycleAction.APPROVE_VALIDATED,
            previous_lifecycle=LifecycleState.REVIEWED,
            resulting_lifecycle=LifecycleState.APPROVED,
            previous_revision=6,
            resulting_revision=7,
            changed_fields=["lifecycle_state", "revision"],
        )


def _deprecation_event(**overrides: object) -> KnowledgeAuditEvent:
    return _event(
        event_type=KnowledgeAuditEventType.DEPRECATE,
        lifecycle_action=LifecycleAction.DEPRECATE_APPROVED,
        previous_lifecycle=LifecycleState.APPROVED,
        resulting_lifecycle=LifecycleState.DEPRECATED,
        previous_revision=5,
        resulting_revision=6,
        changed_fields=["lifecycle_state", "revision"],
        **overrides,
    )


def test_ir_c02_deprecation_replacement_round_trips_or_remains_null() -> None:
    replacement_object_id = uuid4()
    with_replacement = _deprecation_event(
        replacement_object_id=replacement_object_id,
    )
    without_replacement = _deprecation_event()
    round_trip = KnowledgeAuditEvent.model_validate(with_replacement.model_dump(mode="json"))

    assert with_replacement.replacement_object_id == replacement_object_id
    assert round_trip.replacement_object_id == replacement_object_id
    assert without_replacement.replacement_object_id is None


@pytest.mark.parametrize(
    "overrides",
    [
        {
            "event_type": KnowledgeAuditEventType.CREATE,
            "lifecycle_action": None,
            "previous_lifecycle": None,
            "resulting_lifecycle": LifecycleState.DRAFT,
            "previous_revision": None,
            "resulting_revision": 1,
            "changed_fields": ["title", "revision"],
        },
        {},
        {
            "event_type": KnowledgeAuditEventType.DRAFT_DELETE,
            "lifecycle_action": LifecycleAction.DELETE_DRAFT,
            "previous_lifecycle": LifecycleState.DRAFT,
            "resulting_lifecycle": None,
            "previous_revision": 1,
            "resulting_revision": None,
            "changed_fields": [],
        },
        {
            "event_type": KnowledgeAuditEventType.TRANSITION,
            "lifecycle_action": LifecycleAction.SUBMIT_DRAFT,
            "previous_lifecycle": LifecycleState.DRAFT,
            "resulting_lifecycle": LifecycleState.CAPTURED,
            "changed_fields": ["lifecycle_state", "revision"],
        },
        {
            "event_type": KnowledgeAuditEventType.CORRECTION_REQUEST,
            "lifecycle_action": LifecycleAction.REQUEST_CAPTURED_CORRECTION,
            "previous_lifecycle": LifecycleState.CAPTURED,
            "resulting_lifecycle": LifecycleState.DRAFT,
            "changed_fields": ["lifecycle_state", "revision"],
        },
        {
            "event_type": KnowledgeAuditEventType.REJECT,
            "lifecycle_action": LifecycleAction.REJECT_CAPTURED,
            "previous_lifecycle": LifecycleState.CAPTURED,
            "resulting_lifecycle": LifecycleState.REJECTED,
            "changed_fields": ["lifecycle_state", "revision"],
        },
        {
            "event_type": KnowledgeAuditEventType.REOPEN,
            "lifecycle_action": LifecycleAction.REOPEN_REJECTED,
            "previous_lifecycle": LifecycleState.REJECTED,
            "resulting_lifecycle": LifecycleState.DRAFT,
            "changed_fields": ["lifecycle_state", "revision"],
        },
        {
            "event_type": KnowledgeAuditEventType.APPROVE,
            "lifecycle_action": LifecycleAction.APPROVE_VALIDATED,
            "previous_lifecycle": LifecycleState.VALIDATED,
            "resulting_lifecycle": LifecycleState.APPROVED,
            "changed_fields": ["lifecycle_state", "revision"],
        },
    ],
)
def test_ir_c02_replacement_is_rejected_outside_deprecation(
    overrides: dict[str, object],
) -> None:
    with pytest.raises(ValidationError):
        _event(replacement_object_id=uuid4(), **overrides)


def test_ir_c02_lifecycle_translation_preserves_exact_t04_replacement() -> None:
    replacement_object_id = uuid4()
    object_id = uuid4()
    actor = LifecycleActor(
        actor_id="synthetic-steward",
        role="knowledge_steward",
    )
    lifecycle_request = LifecycleAuditAppendRequest(
        object_id=object_id,
        action=LifecycleAction.DEPRECATE_APPROVED,
        previous_lifecycle=LifecycleState.APPROVED,
        resulting_lifecycle=LifecycleState.DEPRECATED,
        actor=actor,
        reason_or_note="Replace synthetic approved knowledge.",
        expected_revision=5,
        resulting_revision=6,
        occurred_at=NOW,
        replacement_object_id=replacement_object_id,
    )
    plan = LifecycleMutationPlan(
        object_id=object_id,
        action=LifecycleAction.DEPRECATE_APPROVED,
        from_lifecycle=LifecycleState.APPROVED,
        to_lifecycle=LifecycleState.DEPRECATED,
        expected_revision=5,
        resulting_revision=6,
        actor=actor,
        note_or_reason="Replace synthetic approved knowledge.",
        occurred_at=NOW,
        resulting_review_projection=LifecycleReviewProjection.ACCEPTED,
        audit_append_request=lifecycle_request,
    )

    audit_request = audit_request_from_lifecycle_plan(
        organization_id="synthetic-org",
        plan=plan,
        correlation_id=uuid4(),
    )

    assert audit_request.replacement_object_id == replacement_object_id


@pytest.mark.parametrize(
    "overrides",
    [
        {
            "event_type": KnowledgeAuditEventType.CREATE,
            "previous_lifecycle": LifecycleState.DRAFT,
            "previous_revision": None,
            "resulting_lifecycle": LifecycleState.DRAFT,
            "resulting_revision": 1,
        },
        {
            "event_type": KnowledgeAuditEventType.UPDATE,
            "changed_fields": [],
        },
        {
            "event_type": KnowledgeAuditEventType.DRAFT_DELETE,
            "lifecycle_action": LifecycleAction.DELETE_DRAFT,
            "previous_lifecycle": LifecycleState.DRAFT,
            "resulting_lifecycle": None,
            "resulting_revision": None,
            "changed_fields": ["content"],
        },
        {
            "event_type": KnowledgeAuditEventType.REJECT,
            "lifecycle_action": None,
            "previous_lifecycle": LifecycleState.CAPTURED,
            "resulting_lifecycle": LifecycleState.REJECTED,
            "changed_fields": ["lifecycle_state", "revision"],
        },
    ],
)
def test_invalid_event_combinations_fail_closed(
    overrides: dict[str, object],
) -> None:
    with pytest.raises(ValidationError):
        _event(**overrides)


def test_event_is_frozen_alias_free_and_uses_utc() -> None:
    offset = datetime.fromisoformat("2026-07-20T14:00:00+02:00")
    event = _event(
        occurred_at=offset,
        recorded_at=offset + timedelta(seconds=1),
        changed_fields=["  CONTENT  ", "revision"],
    )
    snapshot = event.model_dump(mode="json")
    snapshot["changed_fields"].append("title")

    assert event.occurred_at == NOW
    assert event.changed_fields == (
        KnowledgeAuditChangedField.CONTENT,
        KnowledgeAuditChangedField.REVISION,
    )
    with pytest.raises(ValidationError, match="frozen"):
        event.actor_id = "changed"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("actor_id", "   "),
        ("actor_role", "x" * 129),
        ("reason_or_note", "x" * 4097),
    ],
)
def test_blank_or_oversized_actor_and_note_are_rejected(
    field_name: str,
    value: str,
) -> None:
    with pytest.raises(ValidationError):
        _event(**{field_name: value})


@pytest.mark.parametrize(
    "changed_fields",
    [
        ["content.secret"],
        ["old_value"],
        ["evidence_metadata"],
        ["content", "content"],
    ],
)
def test_changed_fields_reject_values_and_non_top_level_names(
    changed_fields: list[str],
) -> None:
    with pytest.raises(ValidationError):
        _event(changed_fields=changed_fields)


def test_raw_payload_fields_and_naive_timestamps_are_rejected() -> None:
    payload = _event().model_dump()
    payload["content"] = {"raw": "forbidden"}
    with pytest.raises(ValidationError, match="Extra inputs"):
        KnowledgeAuditEvent.model_validate(payload)

    with pytest.raises(ValidationError, match="timezone-aware"):
        _event(occurred_at=datetime(2026, 7, 20, 12, 0))


def test_recorded_timestamp_cannot_precede_occurrence() -> None:
    with pytest.raises(ValidationError, match="must not precede"):
        _event(recorded_at=NOW - timedelta(seconds=1))
