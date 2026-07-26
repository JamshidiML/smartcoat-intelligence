from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from pydantic import TypeAdapter, ValidationError

from smartcoat.api.knowledge_v2_schemas import (
    ApproveValidatedActionRequest,
    CompleteReviewActionRequest,
    DeprecateApprovedActionRequest,
    KnowledgeCreateRequest,
    KnowledgeLifecycleActionRequest,
    KnowledgeObjectV2Response,
    KnowledgeUpdateRequest,
    RejectCapturedActionRequest,
    RejectReviewedActionRequest,
    RejectValidatedActionRequest,
    ReopenRejectedActionRequest,
    RequestCapturedCorrectionActionRequest,
    RequestReviewedCorrectionActionRequest,
    RequestValidatedCorrectionActionRequest,
    SubmitDraftActionRequest,
    ValidateReviewedActionRequest,
    lifecycle_request_to_domain,
)
from smartcoat.domain.base import LifecycleState
from smartcoat.domain.context_references import (
    ContextIdKind,
    ContextReference,
    ContextType,
)
from smartcoat.domain.evidence_provenance import (
    CreationMethod,
    EvidenceCompleteness,
    EvidenceReference,
    EvidenceType,
    KnowledgeObjectV2EvidenceComposition,
    ProvenanceCompleteness,
    ProvenanceV2,
)
from smartcoat.domain.knowledge_audit import (
    GovernedKnowledgeCreateCommand,
    GovernedKnowledgeUpdateCommand,
)
from smartcoat.domain.knowledge_lifecycle import (
    ApproveValidatedCommand,
    CompleteReviewCommand,
    DeprecateApprovedCommand,
    RejectCapturedCommand,
    RejectReviewedCommand,
    RejectValidatedCommand,
    ReopenRejectedCommand,
    RequestCapturedCorrectionCommand,
    RequestReviewedCorrectionCommand,
    RequestValidatedCorrectionCommand,
    SubmitDraftCommand,
    ValidateReviewedCommand,
)
from smartcoat.domain.knowledge_objects_v2 import (
    KnowledgeObjectV2CoreRecord,
    KnowledgeObjectV2PersistedStateSnapshot,
    OwnerReference,
)

NOW = datetime(2026, 7, 27, 10, 0, tzinfo=UTC)
OBJECT_ID = UUID("00000000-0000-0000-0000-000000000901")
CORRELATION_ID = UUID("00000000-0000-0000-0000-000000000902")


def _mutable_state_payload() -> dict[str, object]:
    return {
        "title": "Synthetic coating observation",
        "description": "Generalized metadata-only API contract fixture.",
        "knowledge_type": "observation",
        "owner": {
            "owner_id": "synthetic-owner",
            "role": "knowledge_author",
        },
        "confidentiality": "internal",
        "tags": ["synthetic", "coating"],
        "content": {"result": True, "sample_count": 3},
        "context": {
            "references": [
                {
                    "context_type": "project",
                    "id_kind": "uuid",
                    "reference_id": "00000000-0000-0000-0000-000000000903",
                    "display_name": "Synthetic project",
                    "relationship_role": "source",
                    "attributes": {"phase": "pilot"},
                }
            ]
        },
        "evidence_ids": ["synthetic-evidence-1"],
        "knowledge_relationships": [],
        "decision_relationships": [],
    }


def _evidence_payload() -> dict[str, object]:
    return {
        "evidence_id": "synthetic-evidence-1",
        "evidence_type": "observation",
        "completeness": "complete",
        "title": "Synthetic observation",
        "source_reference": "synthetic://evidence/1",
        "captured_by": "synthetic-author",
        "captured_at": (NOW - timedelta(minutes=2)).isoformat(),
    }


def _provenance_payload() -> dict[str, object]:
    return {
        "source_system": "synthetic-test",
        "source_reference": "synthetic://knowledge/1",
        "created_by": "synthetic-author",
        "creation_method": "manual",
        "captured_at": (NOW - timedelta(minutes=1)).isoformat(),
        "transformation_history": [],
        "completeness": "complete",
    }


def _create_payload() -> dict[str, object]:
    return {
        "mutable_state": _mutable_state_payload(),
        "evidence": [_evidence_payload()],
        "provenance": _provenance_payload(),
        "actor": {
            "actor_id": "synthetic-author",
            "actor_role": "knowledge_author",
        },
        "reason_or_note": "Create synthetic draft.",
    }


def _composition() -> KnowledgeObjectV2EvidenceComposition:
    request = KnowledgeCreateRequest.model_validate(_create_payload())
    command = request.to_domain(
        organization_id="synthetic-org",
        correlation_id=CORRELATION_ID,
    )
    return KnowledgeObjectV2EvidenceComposition(
        core=KnowledgeObjectV2CoreRecord(
            object_id=OBJECT_ID,
            organization_id="synthetic-org",
            revision=1,
            lifecycle_state=LifecycleState.DRAFT,
            created_at=NOW,
            updated_at=NOW,
            mutable_state=KnowledgeObjectV2PersistedStateSnapshot.from_mutable_state(
                command.create.mutable_state
            ),
        ),
        evidence=command.evidence,
        provenance=command.provenance,
    )


def test_create_request_maps_exact_governed_command() -> None:
    request = KnowledgeCreateRequest.model_validate(_create_payload())

    command = request.to_domain(
        organization_id=" synthetic-org ",
        correlation_id=CORRELATION_ID,
    )

    assert isinstance(command, GovernedKnowledgeCreateCommand)
    assert command.create.organization_id == "synthetic-org"
    assert command.create.mutable_state.title == "Synthetic coating observation"
    assert command.evidence[0].evidence_id == "synthetic-evidence-1"
    assert command.provenance.creation_method is CreationMethod.MANUAL
    assert command.actor.actor_id == "synthetic-author"
    assert command.actor.role == "knowledge_author"
    assert command.correlation_id == CORRELATION_ID


@pytest.mark.parametrize(
    "field",
    [
        "object_id",
        "organization_id",
        "lifecycle_state",
        "revision",
        "created_at",
        "updated_at",
        "audit_sequence",
        "event_id",
        "recorded_at",
        "audit_payload",
    ],
)
def test_create_rejects_server_owned_and_arbitrary_fields(field: str) -> None:
    payload = _create_payload()
    payload[field] = "forbidden"

    with pytest.raises(ValidationError, match="extra_forbidden"):
        KnowledgeCreateRequest.model_validate(payload)


def test_update_path_id_is_authoritative_and_body_has_no_immutable_fields() -> None:
    request = KnowledgeUpdateRequest.model_validate(
        {
            "expected_revision": 4,
            "replacement": _mutable_state_payload(),
            "actor": {
                "actor_id": "synthetic-author",
                "actor_role": "knowledge_author",
            },
            "reason_or_note": "Replace complete mutable state.",
        }
    )

    command = request.to_domain(
        object_id=OBJECT_ID,
        organization_id="synthetic-org",
        correlation_id=CORRELATION_ID,
    )

    assert isinstance(command, GovernedKnowledgeUpdateCommand)
    assert command.update.object_id == OBJECT_ID
    assert command.update.expected_revision == 4
    assert command.organization_id == "synthetic-org"
    for field in ("object_id", "organization_id", "lifecycle_state", "revision"):
        payload = request.model_dump(mode="python")
        payload[field] = "forbidden"
        with pytest.raises(ValidationError, match="extra_forbidden"):
            KnowledgeUpdateRequest.model_validate(payload)


_ACTION_CASES = (
    (
        {"action": "submit_draft", "submission_note": "Submit."},
        SubmitDraftActionRequest,
        SubmitDraftCommand,
    ),
    (
        {
            "action": "request_captured_correction",
            "correction_reason": "Correct.",
        },
        RequestCapturedCorrectionActionRequest,
        RequestCapturedCorrectionCommand,
    ),
    (
        {"action": "complete_review", "review_note": "Reviewed."},
        CompleteReviewActionRequest,
        CompleteReviewCommand,
    ),
    (
        {"action": "reject_captured", "rejection_reason": "Reject."},
        RejectCapturedActionRequest,
        RejectCapturedCommand,
    ),
    (
        {
            "action": "request_reviewed_correction",
            "correction_reason": "Correct.",
        },
        RequestReviewedCorrectionActionRequest,
        RequestReviewedCorrectionCommand,
    ),
    (
        {"action": "validate_reviewed", "validation_note": "Validated."},
        ValidateReviewedActionRequest,
        ValidateReviewedCommand,
    ),
    (
        {"action": "reject_reviewed", "rejection_reason": "Reject."},
        RejectReviewedActionRequest,
        RejectReviewedCommand,
    ),
    (
        {
            "action": "request_validated_correction",
            "correction_reason": "Correct.",
        },
        RequestValidatedCorrectionActionRequest,
        RequestValidatedCorrectionCommand,
    ),
    (
        {"action": "approve_validated", "approval_note": "Approved."},
        ApproveValidatedActionRequest,
        ApproveValidatedCommand,
    ),
    (
        {"action": "reject_validated", "rejection_reason": "Reject."},
        RejectValidatedActionRequest,
        RejectValidatedCommand,
    ),
    (
        {
            "action": "deprecate_approved",
            "deprecation_reason": "Superseded.",
            "replacement_object_id": "00000000-0000-0000-0000-000000000904",
        },
        DeprecateApprovedActionRequest,
        DeprecateApprovedCommand,
    ),
    (
        {"action": "reopen_rejected", "reopen_reason": "Reopen."},
        ReopenRejectedActionRequest,
        ReopenRejectedCommand,
    ),
)


@pytest.mark.parametrize(("specific", "request_type", "command_type"), _ACTION_CASES)
def test_each_lifecycle_action_maps_one_to_one(
    specific: dict[str, object],
    request_type: type,
    command_type: type,
) -> None:
    payload = {
        **specific,
        "expected_revision": 3,
        "actor": {
            "actor_id": "synthetic-actor",
            "actor_role": "reviewer",
        },
    }
    request = TypeAdapter(KnowledgeLifecycleActionRequest).validate_python(payload)
    command = lifecycle_request_to_domain(request, object_id=OBJECT_ID)

    assert isinstance(request, request_type)
    assert isinstance(command, command_type)
    assert command.object_id == OBJECT_ID
    assert command.expected_revision == 3
    assert command.actor.actor_id == "synthetic-actor"


@pytest.mark.parametrize(
    "payload",
    [
        {
            "action": "delete_draft",
            "expected_revision": 1,
            "actor": {"actor_id": "x", "actor_role": "knowledge_author"},
            "reason": "Delete.",
        },
        {
            "action": "unknown",
            "expected_revision": 1,
            "actor": {"actor_id": "x", "actor_role": "knowledge_author"},
        },
        {
            "action": "submit_draft",
            "expected_revision": 1,
            "actor": {"actor_id": "x", "actor_role": "knowledge_author"},
            "submission_note": "Submit.",
            "rejection_reason": "Irrelevant.",
        },
        {
            "action": "approve_validated",
            "expected_revision": 1,
            "actor": {"actor_id": "x", "actor_role": "approver"},
            "approval_note": "Approve.",
            "replacement_object_id": str(uuid4()),
        },
    ],
)
def test_lifecycle_union_rejects_delete_unknown_and_irrelevant_fields(
    payload: dict[str, object],
) -> None:
    with pytest.raises(ValidationError):
        TypeAdapter(KnowledgeLifecycleActionRequest).validate_python(payload)


def test_response_mapping_is_explicit_alias_safe_and_storage_free() -> None:
    composition = _composition()
    response = KnowledgeObjectV2Response.from_domain(composition)
    serialized = response.model_dump(mode="json")
    encoded = json.dumps(serialized, sort_keys=True)

    assert response.object_id == OBJECT_ID
    assert response.mutable_state.context_references[0].context_type is ContextType.PROJECT
    assert response.mutable_state.context_references[0].id_kind is ContextIdKind.UUID
    assert response.evidence[0].evidence_type is EvidenceType.OBSERVATION
    assert response.evidence[0].completeness is EvidenceCompleteness.COMPLETE
    assert response.provenance.completeness is ProvenanceCompleteness.COMPLETE
    assert "canonical_state_json" not in encoded
    assert "canonical_metadata_json" not in encoded
    assert "xmin" not in encoded
    assert "database_table" not in encoded

    response.mutable_state.content["result"] = False
    response.mutable_state.context_references[0].attributes["phase"] = "changed"
    assert composition.core.mutable_state.content["result"] is True
    assert composition.core.mutable_state.context.references[0].attributes["phase"] == "pilot"


def test_response_context_and_evidence_models_are_safe_public_contracts() -> None:
    response = KnowledgeObjectV2Response.from_domain(_composition())
    schema_text = json.dumps(KnowledgeObjectV2Response.model_json_schema(), sort_keys=True)

    assert isinstance(response.evidence[0], object)
    assert "canonical_state_json" not in schema_text
    assert "canonical_metadata_json" not in schema_text
    assert ContextReference.model_fields.keys() <= {
        "context_type",
        "id_kind",
        "reference_id",
        "source_system",
        "version",
        "display_name",
        "relationship_role",
        "source_reference",
        "evidence_reference",
        "attributes",
    }
    assert isinstance(response.provenance, ProvenanceV2)
    assert isinstance(response.evidence[0].to_domain(), EvidenceReference)
    assert isinstance(response.mutable_state.context_references, tuple)
    assert isinstance(response.provenance, ProvenanceV2)
    assert isinstance(response.mutable_state.title, str)
    assert isinstance(response.mutable_state.owner, OwnerReference)
