from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any, cast
from uuid import UUID

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from smartcoat.api.routes.lab_observations import router as lab_observation_router
from smartcoat.api.routes.lab_project_captures import (
    CREATE_REASON,
    LAB_PROJECT_CAPTURE_ACTOR_ROLE,
    LAB_PROJECT_CAPTURE_ROLE,
    LAB_PROJECT_CAPTURE_SOURCE_SYSTEM,
    LAB_PROJECT_CAPTURE_TAG,
    _build_create_command,
    get_lab_project_capture_audit_service,
    get_lab_project_capture_repository,
    router,
)
from smartcoat.api.routes.qc_observations import router as qc_observation_router
from smartcoat.domain.base import LifecycleState
from smartcoat.domain.context_references import ContextIdKind, ContextType
from smartcoat.domain.evidence_provenance import (
    CreationMethod,
    EvidenceCompleteness,
    EvidenceType,
    IntegrityAlgorithm,
    KnowledgeObjectV2EvidenceComposition,
    ProvenanceCompleteness,
)
from smartcoat.domain.knowledge_audit import GovernedKnowledgeCreateCommand
from smartcoat.domain.knowledge_objects import KnowledgeObjectType
from smartcoat.domain.knowledge_objects_v2 import (
    ConfidentialityLevel,
    KnowledgeObjectV2CoreRecord,
    KnowledgeObjectV2PersistedStateSnapshot,
)
from smartcoat.domain.lab_project_capture import LabProjectCaptureCandidate

NOW = datetime(2026, 8, 6, 9, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 8, 6, 8, 0, tzinfo=UTC)
OBJECT_ID = UUID("0a13d814-5b80-46f1-9f49-6dcd486c8349")
AUDIT_EVENT_ID = UUID("3c2666ee-9304-4bb6-a977-6855da760fa1")
SESSION_ID = UUID("72d399c6-5fdf-4897-a4ab-126739220028")
ORGANIZATION_ID = "synthetic-project-org"
LOCAL_EVIDENCE_SHA = "e" * 64


def _payload(*, confirmed: bool = True) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "capture_session_id": str(SESSION_ID),
        "source_kind": "text",
        "source_language": "en",
        "transcript": "Synthetic project intake for governed API validation.",
        "extraction_model": "deterministic-local-extractor",
        "extraction_started_at": "2026-08-06T08:05:00Z",
        "extraction_completed_at": "2026-08-06T08:06:00Z",
        "project": {
            "project_id": "P-SYN-101",
            "project_name": "Synthetic thermal barrier project",
            "customer_company": "Example Customer",
            "request_summary": "Evaluate a synthetic coated substrate.",
            "target_application": "Generalized thermal protection",
            "success_criteria": ["Pass the declared synthetic test."],
            "project_status": "open",
        },
        "substrate": {
            "substrate_id": "SUB-SYN-01",
            "substrate_name": "Synthetic woven substrate",
            "reason_selected": "Selected for a generalized laboratory trial.",
        },
        "approaches": [
            {
                "approach_id": "C-A-001",
                "title": "Synthetic baseline",
                "outcome": "successful",
                "price_optimization_status": "assessed",
                "production_feasibility_status": "assessed",
                "reuse_potential": "Suitable for another generalized experiment.",
            }
        ],
        "tests": [
            {
                "approach_id": "C-A-001",
                "test_name": "Synthetic thermal test",
                "method": "Generalized internal method",
                "acceptance_criteria": "Meets the synthetic threshold.",
                "text_result": "Passed",
                "outcome": "passed",
            }
        ],
        "evidence": [
            {
                "evidence_id": "EV-SYN-001",
                "evidence_type": "transcript",
                "filename": "synthetic-transcript.txt",
                "media_type": "text/plain",
                "source_reference": "asset://synthetic/EV-SYN-001",
                "sha256": "a" * 64,
                "captured_at": OBSERVED_AT.isoformat(),
                "description": "Synthetic transcript evidence.",
                "approach_id": "C-A-001",
            }
        ],
        "current_next_action": "Schedule a synthetic review.",
        "next_action_due_at": "2026-08-08T09:00:00Z",
        "unresolved_questions": ["Who will attend the synthetic review?"],
        "human_confirmed": confirmed,
    }
    if confirmed:
        payload.update(
            {
                "human_confirmed_by": "synthetic-reviewer",
                "human_confirmed_at": NOW.isoformat(),
            }
        )
    return payload


def _composition_from_command(
    command: GovernedKnowledgeCreateCommand,
    *,
    organization_id: str | None = None,
) -> KnowledgeObjectV2EvidenceComposition:
    return KnowledgeObjectV2EvidenceComposition(
        core=KnowledgeObjectV2CoreRecord(
            object_id=OBJECT_ID,
            organization_id=organization_id or command.create.organization_id,
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


class FakeAuditService:
    def __init__(self) -> None:
        self.commands: list[GovernedKnowledgeCreateCommand] = []

    def create(self, command: GovernedKnowledgeCreateCommand) -> Any:
        self.commands.append(command)
        return SimpleNamespace(
            knowledge=_composition_from_command(command),
            audit_event=SimpleNamespace(
                event_id=AUDIT_EVENT_ID,
                audit_sequence=1,
            ),
        )


class FakeRepository:
    def __init__(
        self,
        composition: KnowledgeObjectV2EvidenceComposition | None,
    ) -> None:
        self.composition = composition
        self.list_calls: list[dict[str, Any]] = []

    def list_object_ids_by_type_and_tag(self, **kwargs: Any) -> tuple[UUID, ...]:
        self.list_calls.append(kwargs)
        organization_id = kwargs["organization_id"]
        if self.composition is None or self.composition.core.organization_id != organization_id:
            return ()
        return (self.composition.core.object_id,)

    def get(self, *, object_id: UUID, organization_id: str) -> Any:
        if (
            self.composition is None
            or self.composition.core.object_id != object_id
            or self.composition.core.organization_id != organization_id
        ):
            return None
        return self.composition


@pytest.fixture()
def api() -> FastAPI:
    application = FastAPI()
    application.include_router(router)
    return application


def test_confirmed_candidate_creates_governed_draft(api: FastAPI) -> None:
    service = FakeAuditService()
    api.dependency_overrides[get_lab_project_capture_audit_service] = lambda: service

    response = TestClient(api).post(
        "/api/v2/lab-project-captures",
        json=_payload(),
        headers={"X-SmartCoat-Organization-ID": f"  {ORGANIZATION_ID}  "},
    )

    assert response.status_code == 201, response.text
    assert len(service.commands) == 1
    command = service.commands[0]
    assert command.create.organization_id == ORGANIZATION_ID
    assert command.reason_or_note == CREATE_REASON
    assert command.actor.actor_id == "synthetic-reviewer"
    assert command.actor.role == LAB_PROJECT_CAPTURE_ACTOR_ROLE

    state = command.create.mutable_state
    assert state.knowledge_type is KnowledgeObjectType.OBSERVATION
    assert state.confidentiality is ConfidentialityLevel.CONFIDENTIAL
    assert state.tags == (LAB_PROJECT_CAPTURE_TAG,)
    assert not hasattr(command.create, "lifecycle_state")
    quality = cast(list[dict[str, Any]], state.content["quality_summary"])[0]
    assert quality["human_confirmed"] is True
    assert quality["completeness_score"] == 100

    assert len(state.context.references) == 1
    project_context = state.context.references[0]
    assert project_context.context_type is ContextType.PROJECT
    assert project_context.id_kind is ContextIdKind.EXTERNAL
    assert project_context.reference_id == "P-SYN-101"
    assert project_context.source_system == LAB_PROJECT_CAPTURE_SOURCE_SYSTEM
    assert project_context.relationship_role == LAB_PROJECT_CAPTURE_ROLE

    assert state.evidence_ids == ("EV-SYN-001",)
    evidence = command.evidence[0]
    assert evidence.evidence_type is EvidenceType.DOCUMENT
    assert evidence.completeness is EvidenceCompleteness.COMPLETE
    assert evidence.source_reference == "asset://synthetic/EV-SYN-001"
    assert evidence.integrity is not None
    assert evidence.integrity.algorithm is IntegrityAlgorithm.SHA256
    assert evidence.integrity.value == "a" * 64
    assert evidence.context_reference is not None
    assert evidence.context_reference.attributes["approach_id"] == "C-A-001"

    provenance = command.provenance
    assert provenance.completeness is ProvenanceCompleteness.COMPLETE
    assert provenance.creation_method is CreationMethod.IMPORTED
    assert provenance.source_reference == f"lab-project-capture://{SESSION_ID}"
    assert [item.transformation_type for item in provenance.transformation_history] == [
        "local_structured_extraction",
        "human_confirmation",
    ]

    body = response.json()
    capture = body["capture"]
    assert capture["object_id"] == str(OBJECT_ID)
    assert capture["project_id"] == "P-SYN-101"
    assert capture["project_name"] == "Synthetic thermal barrier project"
    assert capture["customer"] == "Example Customer"
    assert capture["current_status"] == "open"
    assert capture["completeness_score"] == 100
    assert capture["lifecycle"] == "draft"
    assert capture["revision"] == 1
    assert capture["observed_at"] == OBSERVED_AT.isoformat().replace("+00:00", "Z")
    assert capture["captured_at"] == NOW.isoformat().replace("+00:00", "Z")
    assert capture["unresolved_question_count"] == 1
    assert capture["next_action"] == "Schedule a synthetic review."
    assert capture["follow_up_due_at"] == "2026-08-08T09:00:00Z"
    assert body["audit_event_id"] == str(AUDIT_EVENT_ID)
    assert body["audit_sequence"] == 1


def test_unconfirmed_candidate_and_missing_confirmation_metadata_are_rejected(
    api: FastAPI,
) -> None:
    service = FakeAuditService()
    api.dependency_overrides[get_lab_project_capture_audit_service] = lambda: service
    client = TestClient(api)

    unconfirmed = client.post(
        "/api/v2/lab-project-captures",
        json=_payload(confirmed=False),
        headers={"X-SmartCoat-Organization-ID": ORGANIZATION_ID},
    )
    missing_actor = _payload()
    missing_actor.pop("human_confirmed_by")
    incomplete = client.post(
        "/api/v2/lab-project-captures",
        json=missing_actor,
        headers={"X-SmartCoat-Organization-ID": ORGANIZATION_ID},
    )

    assert unconfirmed.status_code == 422
    assert unconfirmed.json() == {"detail": "A human-confirmed candidate is required"}
    assert incomplete.status_code == 422
    assert service.commands == []


def test_blocking_readiness_issue_rejects_before_audit_then_saves_after_edit(
    api: FastAPI,
) -> None:
    service = FakeAuditService()
    api.dependency_overrides[get_lab_project_capture_audit_service] = lambda: service
    payload = _payload()
    payload["materials"] = [
        {
            "material_id": "C-M-001",
            "material_name": "Synthetic magnesium hydroxide",
            "amount": 5,
        }
    ]
    client = TestClient(api)

    blocked = client.post(
        "/api/v2/lab-project-captures",
        json=payload,
        headers={"X-SmartCoat-Organization-ID": ORGANIZATION_ID},
    )

    assert blocked.status_code == 422
    assert blocked.json()["detail"] == {
        "code": "candidate_not_ready",
        "message": "Candidate has blocking readiness issues",
        "issues": [
            {
                "code": "material_amount_missing_unit",
                "path": "materials.0.unit",
                "message": "Material Synthetic magnesium hydroxide has an amount but no unit.",
                "question": "What unit belongs to the Synthetic magnesium hydroxide amount?",
            }
        ],
    }
    assert service.commands == []

    payload["materials"][0]["unit"] = "g"
    saved = client.post(
        "/api/v2/lab-project-captures",
        json=payload,
        headers={"X-SmartCoat-Organization-ID": ORGANIZATION_ID},
    )

    assert saved.status_code == 201, saved.text
    assert len(service.commands) == 1


def test_same_organization_local_evidence_is_accepted(api: FastAPI) -> None:
    service = FakeAuditService()
    api.dependency_overrides[get_lab_project_capture_audit_service] = lambda: service
    payload = _payload()
    payload["evidence"][0].update(
        {
            "source_reference": (f"smartcoat-asset://{ORGANIZATION_ID}/{LOCAL_EVIDENCE_SHA}"),
            "sha256": LOCAL_EVIDENCE_SHA,
        }
    )

    response = TestClient(api).post(
        "/api/v2/lab-project-captures",
        json=payload,
        headers={"X-SmartCoat-Organization-ID": ORGANIZATION_ID},
    )

    assert response.status_code == 201, response.text
    assert len(service.commands) == 1


def test_cross_organization_local_evidence_is_rejected_before_service(
    api: FastAPI,
) -> None:
    service = FakeAuditService()
    api.dependency_overrides[get_lab_project_capture_audit_service] = lambda: service
    payload = _payload()
    payload["evidence"][0].update(
        {
            "source_reference": (f"smartcoat-asset://synthetic-org-a/{LOCAL_EVIDENCE_SHA}"),
            "sha256": LOCAL_EVIDENCE_SHA,
        }
    )

    response = TestClient(api).post(
        "/api/v2/lab-project-captures",
        json=payload,
        headers={"X-SmartCoat-Organization-ID": "synthetic-org-b"},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == {
        "code": "evidence_organization_mismatch",
        "message": "Local SmartCoat evidence belongs to another organization",
    }
    assert service.commands == []


def test_cross_organization_local_evidence_is_rejected_before_command_creation() -> None:
    payload = _payload()
    payload["evidence"][0].update(
        {
            "source_reference": (f"smartcoat-asset://synthetic-org-a/{LOCAL_EVIDENCE_SHA}"),
            "sha256": LOCAL_EVIDENCE_SHA,
        }
    )

    with pytest.raises(HTTPException) as captured:
        _build_create_command(
            LabProjectCaptureCandidate.model_validate(payload),
            "synthetic-org-b",
        )

    assert captured.value.status_code == 422
    assert captured.value.detail["code"] == "evidence_organization_mismatch"


def test_local_evidence_digest_mismatch_is_rejected_before_service(
    api: FastAPI,
) -> None:
    service = FakeAuditService()
    api.dependency_overrides[get_lab_project_capture_audit_service] = lambda: service
    payload = _payload()
    payload["evidence"][0].update(
        {
            "source_reference": f"smartcoat-asset://{ORGANIZATION_ID}/{'f' * 64}",
            "sha256": LOCAL_EVIDENCE_SHA,
        }
    )

    response = TestClient(api).post(
        "/api/v2/lab-project-captures",
        json=payload,
        headers={"X-SmartCoat-Organization-ID": ORGANIZATION_ID},
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "invalid_local_evidence_reference"
    assert service.commands == []


@pytest.mark.parametrize(
    "source_reference",
    [
        "smartcoat-asset://",
        f"smartcoat-asset:///{LOCAL_EVIDENCE_SHA}",
        f"smartcoat-asset://{ORGANIZATION_ID}/not-a-sha",
        f"smartcoat-asset://{ORGANIZATION_ID}/{LOCAL_EVIDENCE_SHA}/extra",
    ],
)
def test_malformed_local_evidence_reference_is_rejected_before_service(
    api: FastAPI,
    source_reference: str,
) -> None:
    service = FakeAuditService()
    api.dependency_overrides[get_lab_project_capture_audit_service] = lambda: service
    payload = _payload()
    payload["evidence"][0].update(
        {
            "source_reference": source_reference,
            "sha256": LOCAL_EVIDENCE_SHA,
        }
    )

    response = TestClient(api).post(
        "/api/v2/lab-project-captures",
        json=payload,
        headers={"X-SmartCoat-Organization-ID": ORGANIZATION_ID},
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "invalid_local_evidence_reference"
    assert service.commands == []


def test_non_local_evidence_reference_preserves_existing_behavior(api: FastAPI) -> None:
    service = FakeAuditService()
    api.dependency_overrides[get_lab_project_capture_audit_service] = lambda: service

    response = TestClient(api).post(
        "/api/v2/lab-project-captures",
        json=_payload(),
        headers={"X-SmartCoat-Organization-ID": ORGANIZATION_ID},
    )

    assert response.status_code == 201, response.text
    assert service.commands[0].evidence[0].source_reference == "asset://synthetic/EV-SYN-001"


def test_orphan_process_references_are_reviewable_but_not_canonical(api: FastAPI) -> None:
    service = FakeAuditService()
    api.dependency_overrides[get_lab_project_capture_audit_service] = lambda: service
    payload = _payload()
    payload["process_parameters"] = [
        {
            "approach_id": "C-A-004",
            "process_stage": "curing",
            "parameter_name": "curing temperature",
            "measurement_state": "unknown",
        }
    ]

    response = TestClient(api).post(
        "/api/v2/lab-project-captures",
        json=payload,
        headers={"X-SmartCoat-Organization-ID": ORGANIZATION_ID},
    )

    assert response.status_code == 422
    assert response.json()["detail"]["issues"][0]["code"] == ("process_parameter_unknown_approach")
    assert service.commands == []


@pytest.mark.parametrize(
    ("missing_type", "detail_fragment"),
    [("audio", "audio evidence"), ("transcript", "transcript evidence")],
)
def test_voice_candidate_requires_audio_and_transcript_evidence(
    api: FastAPI,
    missing_type: str,
    detail_fragment: str,
) -> None:
    service = FakeAuditService()
    api.dependency_overrides[get_lab_project_capture_audit_service] = lambda: service
    payload = _payload()
    payload["source_kind"] = "voice"
    payload["evidence"] = [
        {
            "evidence_id": "EV-VOICE-AUDIO",
            "evidence_type": "audio",
            "filename": "synthetic.webm",
            "media_type": "audio/webm",
            "source_reference": f"smartcoat-asset://{ORGANIZATION_ID}/{'b' * 64}",
            "sha256": "b" * 64,
            "captured_at": OBSERVED_AT.isoformat(),
        },
        {
            "evidence_id": "EV-VOICE-TRANSCRIPT",
            "evidence_type": "transcript",
            "filename": "capture-transcript.txt",
            "media_type": "text/plain",
            "source_reference": f"smartcoat-asset://{ORGANIZATION_ID}/{'c' * 64}",
            "sha256": "c" * 64,
            "captured_at": OBSERVED_AT.isoformat(),
        },
    ]
    payload["evidence"] = [
        item for item in payload["evidence"] if item["evidence_type"] != missing_type
    ]

    response = TestClient(api).post(
        "/api/v2/lab-project-captures",
        json=payload,
        headers={"X-SmartCoat-Organization-ID": ORGANIZATION_ID},
    )

    assert response.status_code == 422
    assert detail_fragment in response.json()["detail"]
    assert service.commands == []


def test_organization_header_and_invalid_evidence_are_rejected(api: FastAPI) -> None:
    service = FakeAuditService()
    api.dependency_overrides[get_lab_project_capture_audit_service] = lambda: service
    client = TestClient(api)

    missing_header = client.post("/api/v2/lab-project-captures", json=_payload())
    blank_header = client.post(
        "/api/v2/lab-project-captures",
        json=_payload(),
        headers={"X-SmartCoat-Organization-ID": "   "},
    )
    invalid_evidence = _payload()
    invalid_evidence["evidence"][0]["sha256"] = "not-a-sha256"
    malformed_evidence = client.post(
        "/api/v2/lab-project-captures",
        json=invalid_evidence,
        headers={"X-SmartCoat-Organization-ID": ORGANIZATION_ID},
    )

    assert missing_header.status_code == 422
    assert blank_header.status_code == 422
    assert malformed_evidence.status_code == 422
    assert service.commands == []


def test_list_and_detail_are_organization_scoped(api: FastAPI) -> None:
    service = FakeAuditService()
    api.dependency_overrides[get_lab_project_capture_audit_service] = lambda: service
    create_response = TestClient(api).post(
        "/api/v2/lab-project-captures",
        json=_payload(),
        headers={"X-SmartCoat-Organization-ID": ORGANIZATION_ID},
    )
    assert create_response.status_code == 201
    repository = FakeRepository(_composition_from_command(service.commands[0]))
    api.dependency_overrides[get_lab_project_capture_repository] = lambda: repository
    client = TestClient(api)

    listed = client.get(
        "/api/v2/lab-project-captures?limit=10&offset=0",
        headers={"X-SmartCoat-Organization-ID": ORGANIZATION_ID},
    )
    detail = client.get(
        f"/api/v2/lab-project-captures/{OBJECT_ID}",
        headers={"X-SmartCoat-Organization-ID": ORGANIZATION_ID},
    )
    other_list = client.get(
        "/api/v2/lab-project-captures",
        headers={"X-SmartCoat-Organization-ID": "another-synthetic-org"},
    )
    other_detail = client.get(
        f"/api/v2/lab-project-captures/{OBJECT_ID}",
        headers={"X-SmartCoat-Organization-ID": "another-synthetic-org"},
    )

    assert listed.status_code == 200
    assert listed.json()["returned_count"] == 1
    assert listed.json()["has_more"] is False
    assert listed.json()["items"][0] == detail.json()
    assert repository.list_calls[0] == {
        "organization_id": ORGANIZATION_ID,
        "knowledge_type": "observation",
        "required_tag": LAB_PROJECT_CAPTURE_TAG,
        "limit": 11,
        "offset": 0,
    }
    assert other_list.status_code == 200
    assert other_list.json()["items"] == []
    assert other_detail.status_code == 404


def test_unknown_project_identity_is_not_invented(api: FastAPI) -> None:
    service = FakeAuditService()
    api.dependency_overrides[get_lab_project_capture_audit_service] = lambda: service
    payload = _payload()
    payload["project"].pop("project_id")
    payload["project"].pop("project_name")

    response = TestClient(api).post(
        "/api/v2/lab-project-captures",
        json=payload,
        headers={"X-SmartCoat-Organization-ID": ORGANIZATION_ID},
    )

    assert response.status_code == 201, response.text
    command = service.commands[0]
    assert command.create.mutable_state.content["project"][0].get("project_id") is None  # type: ignore[index, union-attr]
    assert command.create.mutable_state.content["project"][0].get("project_name") is None  # type: ignore[index, union-attr]
    assert command.create.mutable_state.context.references[0].attributes == {
        "project_identity_state": "unknown",
        "capture_session_id": str(SESSION_ID),
    }
    assert response.json()["capture"]["project_id"] is None
    assert response.json()["capture"]["project_name"] is None


def test_existing_lab_and_qc_routes_remain_unchanged() -> None:
    application = FastAPI()
    application.include_router(lab_observation_router)
    application.include_router(qc_observation_router)
    application.include_router(router)

    paths = application.openapi()["paths"]
    assert set(paths["/api/v2/lab-observations"]) == {"get", "post"}
    assert set(paths["/api/v2/lab-observations/{object_id}"]) == {"get"}
    assert set(paths["/api/v2/qc-observations"]) == {"post"}
    assert set(paths["/api/v2/qc-observations/{object_id}"]) == {"get"}
    assert set(paths["/api/v2/lab-project-captures"]) == {"get", "post"}
    assert set(paths["/api/v2/lab-project-captures/{object_id}"]) == {"get"}

    client = TestClient(application)
    assert client.post("/api/v2/lab-observations", json={}).status_code == 422
    assert client.post("/api/v2/qc-observations", json={}).status_code == 422
