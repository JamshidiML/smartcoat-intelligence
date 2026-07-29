from __future__ import annotations

import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from smartcoat.api.main import app
from smartcoat.api.routes.qc_observations import (
    CREATE_REASON,
    QC_OBSERVATION_ROLE,
    QC_OBSERVATION_TAG,
    QC_SOURCE_SYSTEM,
    get_qc_observation_audit_service,
    get_qc_observation_repository,
)
from smartcoat.domain.base import LifecycleState
from smartcoat.domain.context_references import (
    ContextIdKind,
    ContextReference,
    ContextType,
    KnowledgeContext,
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
from smartcoat.domain.knowledge_audit import GovernedKnowledgeCreateCommand
from smartcoat.domain.knowledge_objects import KnowledgeObjectType
from smartcoat.domain.knowledge_objects_v2 import (
    ConfidentialityLevel,
    KnowledgeObjectV2CoreRecord,
    KnowledgeObjectV2MutableState,
    KnowledgeObjectV2PersistedStateSnapshot,
    OwnerReference,
)

NOW = datetime(2026, 7, 29, 14, 0, tzinfo=UTC)
OBJECT_ID = UUID("33333333-3333-4333-8333-333333333333")
AUDIT_EVENT_ID = UUID("44444444-4444-4444-8444-444444444444")
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _payload() -> dict[str, str]:
    return {
        "test_result_id": "QC-TR-2026-001",
        "test_result_name": "Synthetic Coating Thickness Result",
        "title": "Synthetic coating thickness below lower limit",
        "finding": ("Synthetic QC measurement was below the declared test-result limit."),
        "source_reference": "qc-record://synthetic/QC-TR-2026-001",
        "observed_at": NOW.isoformat(),
        "actor_id": "synthetic-qc-inspector",
        "actor_role": "qc_inspector",
    }


def _composition_from_command(
    command: GovernedKnowledgeCreateCommand,
    *,
    source_system: str = QC_SOURCE_SYSTEM,
) -> KnowledgeObjectV2EvidenceComposition:
    provenance = command.provenance.model_copy(
        update={"source_system": source_system},
    )
    return KnowledgeObjectV2EvidenceComposition(
        core=KnowledgeObjectV2CoreRecord(
            object_id=OBJECT_ID,
            organization_id=command.create.organization_id,
            revision=1,
            lifecycle_state=LifecycleState.DRAFT,
            created_at=NOW,
            updated_at=NOW,
            mutable_state=KnowledgeObjectV2PersistedStateSnapshot.from_mutable_state(
                command.create.mutable_state
            ),
        ),
        evidence=command.evidence,
        provenance=provenance,
    )


def _canonical_composition(
    *,
    organization_id: str = "synthetic-qc-org",
    source_system: str = QC_SOURCE_SYSTEM,
) -> KnowledgeObjectV2EvidenceComposition:
    test_result_reference = ContextReference(
        context_type=ContextType.TEST_RESULT,
        reference_id="QC-TR-2026-001",
        id_kind=ContextIdKind.EXTERNAL,
        source_system=QC_SOURCE_SYSTEM,
        display_name="Synthetic Coating Thickness Result",
        relationship_role=QC_OBSERVATION_ROLE,
        source_reference="qc-record://synthetic/QC-TR-2026-001",
        evidence_reference="qc-observation:evidence-1",
        attributes={},
    )
    state = KnowledgeObjectV2MutableState(
        title="Synthetic coating thickness below lower limit",
        description=None,
        knowledge_type=KnowledgeObjectType.FINDING,
        owner=OwnerReference(
            owner_id="synthetic-qc-inspector",
            role="qc_inspector",
        ),
        confidentiality=ConfidentialityLevel.INTERNAL,
        uncertainty=None,
        tags=(QC_OBSERVATION_TAG,),
        content={"finding": ("Synthetic QC measurement was below the declared test-result limit.")},
        context=KnowledgeContext(references=[test_result_reference]),
        evidence_ids=("qc-observation:evidence-1",),
        knowledge_relationships=(),
        decision_relationships=(),
    )
    evidence = EvidenceReference(
        evidence_id="qc-observation:evidence-1",
        evidence_type=EvidenceType.TEST_RESULT,
        completeness=EvidenceCompleteness.COMPLETE,
        title=state.title,
        description=state.content["finding"],
        source_reference="qc-record://synthetic/QC-TR-2026-001",
        source_system=QC_SOURCE_SYSTEM,
        captured_by="synthetic-qc-inspector",
        captured_at=NOW,
        source_created_at=NOW,
        confidentiality=ConfidentialityLevel.INTERNAL,
        context_reference=test_result_reference,
    )
    provenance = ProvenanceV2(
        source_system=source_system,
        source_reference="qc-record://synthetic/QC-TR-2026-001",
        created_by="synthetic-qc-inspector",
        creation_method=CreationMethod.MANUAL,
        captured_at=NOW,
        source_created_at=NOW,
        completeness=ProvenanceCompleteness.COMPLETE,
    )
    return KnowledgeObjectV2EvidenceComposition(
        core=KnowledgeObjectV2CoreRecord(
            object_id=OBJECT_ID,
            organization_id=organization_id,
            revision=1,
            lifecycle_state=LifecycleState.DRAFT,
            created_at=NOW,
            updated_at=NOW,
            mutable_state=KnowledgeObjectV2PersistedStateSnapshot.from_mutable_state(state),
        ),
        evidence=(evidence,),
        provenance=provenance,
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
        self.get_calls: list[tuple[UUID, str]] = []

    def get(self, *, object_id: UUID, organization_id: str) -> Any:
        self.get_calls.append((object_id, organization_id))
        if (
            self.composition is None
            or object_id != self.composition.core.object_id
            or organization_id != self.composition.core.organization_id
        ):
            return None
        return self.composition


@pytest.fixture(autouse=True)
def _clear_dependency_overrides() -> Any:
    original = app.dependency_overrides.copy()
    try:
        yield
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(original)


def test_create_maps_valid_payload_and_returns_201() -> None:
    service = FakeAuditService()
    app.dependency_overrides[get_qc_observation_audit_service] = lambda: service

    response = TestClient(app).post(
        "/api/v2/qc-observations",
        json=_payload(),
        headers={"X-SmartCoat-Organization-ID": "  synthetic-qc-org  "},
    )

    assert response.status_code == 201
    assert len(service.commands) == 1
    command = service.commands[0]
    assert isinstance(command, GovernedKnowledgeCreateCommand)
    assert command.create.organization_id == "synthetic-qc-org"
    assert command.actor.actor_id == "synthetic-qc-inspector"
    assert command.actor.role == "qc_inspector"
    assert command.reason_or_note == CREATE_REASON
    state = command.create.mutable_state
    assert state.knowledge_type is KnowledgeObjectType.FINDING
    assert not hasattr(command.create, "lifecycle_state")
    assert state.confidentiality is ConfidentialityLevel.INTERNAL
    assert state.content == {"finding": _payload()["finding"]}
    assert state.tags == (QC_OBSERVATION_TAG,)
    assert len(state.context.references) == 1
    test_result = state.context.references[0]
    assert test_result.context_type is ContextType.TEST_RESULT
    assert test_result.id_kind is ContextIdKind.EXTERNAL
    assert test_result.reference_id == _payload()["test_result_id"]
    assert test_result.source_system == QC_SOURCE_SYSTEM
    assert test_result.relationship_role == QC_OBSERVATION_ROLE
    assert len(command.evidence) == 1
    evidence = command.evidence[0]
    assert evidence.evidence_type is EvidenceType.TEST_RESULT
    assert evidence.completeness is EvidenceCompleteness.COMPLETE
    assert evidence.context_reference == test_result
    assert command.provenance.completeness is ProvenanceCompleteness.COMPLETE
    assert command.provenance.creation_method is CreationMethod.MANUAL
    assert command.provenance.source_reference == _payload()["source_reference"]
    assert command.provenance.source_created_at == NOW
    body = response.json()
    assert body["observation"]["lifecycle_state"] == "draft"
    assert body["observation"]["revision"] == 1
    assert body["observation"]["finding"] == _payload()["finding"]
    assert body["audit_event_id"] == str(AUDIT_EVENT_ID)
    assert body["audit_sequence"] > 0


def test_create_rejects_missing_or_blank_organization_header() -> None:
    service = FakeAuditService()
    app.dependency_overrides[get_qc_observation_audit_service] = lambda: service
    client = TestClient(app)

    missing = client.post("/api/v2/qc-observations", json=_payload())
    blank = client.post(
        "/api/v2/qc-observations",
        json=_payload(),
        headers={"X-SmartCoat-Organization-ID": "   "},
    )

    assert missing.status_code == 422
    assert blank.status_code == 422
    assert service.commands == []


def test_create_rejects_invalid_payloads() -> None:
    service = FakeAuditService()
    app.dependency_overrides[get_qc_observation_audit_service] = lambda: service
    client = TestClient(app)
    invalid_cases: tuple[tuple[str, Any], ...] = (
        ("test_result_id", "   "),
        ("test_result_name", "   "),
        ("title", "   "),
        ("finding", "   "),
        ("source_reference", "   "),
        ("actor_id", "   "),
        ("actor_role", "   "),
        ("observed_at", "2026-07-29T14:00:00"),
    )

    for field_name, invalid_value in invalid_cases:
        payload = _payload()
        payload[field_name] = invalid_value
        response = client.post(
            "/api/v2/qc-observations",
            json=payload,
            headers={"X-SmartCoat-Organization-ID": "synthetic-qc-org"},
        )
        assert response.status_code == 422

    assert service.commands == []


def test_create_rejects_extra_and_server_owned_fields() -> None:
    service = FakeAuditService()
    app.dependency_overrides[get_qc_observation_audit_service] = lambda: service
    client = TestClient(app)
    extra_fields: dict[str, Any] = {
        "object_id": str(uuid4()),
        "organization_id": "wrong-org",
        "revision": 1,
        "lifecycle_state": "approved",
        "created_at": NOW.isoformat(),
        "updated_at": NOW.isoformat(),
        "confidentiality": "public",
    }

    for field_name, value in extra_fields.items():
        response = client.post(
            "/api/v2/qc-observations",
            json={**_payload(), field_name: value},
            headers={"X-SmartCoat-Organization-ID": "synthetic-qc-org"},
        )
        assert response.status_code == 422

    assert service.commands == []


def test_get_returns_existing_qc_observation_without_mutation() -> None:
    composition = _canonical_composition()
    repository = FakeRepository(composition)
    app.dependency_overrides[get_qc_observation_repository] = lambda: repository
    assert get_qc_observation_audit_service not in app.dependency_overrides

    response = TestClient(app).get(
        f"/api/v2/qc-observations/{OBJECT_ID}",
        headers={"X-SmartCoat-Organization-ID": "synthetic-qc-org"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["test_result_id"] == "QC-TR-2026-001"
    assert body["test_result_name"] == "Synthetic Coating Thickness Result"
    assert body["finding"] == _payload()["finding"]
    assert body["evidence_id"] == "qc-observation:evidence-1"
    assert body["provenance"]["source_system"] == QC_SOURCE_SYSTEM
    assert body["provenance"]["creation_method"] == "manual"
    assert body["provenance"]["completeness"] == "complete"
    assert body["revision"] == 1
    assert body["lifecycle_state"] == "draft"
    assert body["created_at"] == NOW.isoformat().replace("+00:00", "Z")
    assert body["updated_at"] == NOW.isoformat().replace("+00:00", "Z")
    assert repository.get_calls == [(OBJECT_ID, "synthetic-qc-org")]
    assert get_qc_observation_audit_service not in app.dependency_overrides


def test_get_returns_404_for_missing_wrong_org_or_non_qc_object() -> None:
    client = TestClient(app)
    app.dependency_overrides[get_qc_observation_repository] = lambda: FakeRepository(None)
    missing = client.get(
        f"/api/v2/qc-observations/{OBJECT_ID}",
        headers={"X-SmartCoat-Organization-ID": "synthetic-qc-org"},
    )

    composition = _canonical_composition()
    app.dependency_overrides[get_qc_observation_repository] = lambda: FakeRepository(composition)
    wrong_org = client.get(
        f"/api/v2/qc-observations/{OBJECT_ID}",
        headers={"X-SmartCoat-Organization-ID": "another-synthetic-org"},
    )

    non_qc = _canonical_composition(source_system="synthetic-other-source")
    app.dependency_overrides[get_qc_observation_repository] = lambda: FakeRepository(non_qc)
    wrong_type = client.get(
        f"/api/v2/qc-observations/{OBJECT_ID}",
        headers={"X-SmartCoat-Organization-ID": "synthetic-qc-org"},
    )

    assert missing.status_code == 404
    assert wrong_org.status_code == 404
    assert wrong_type.status_code == 404


def test_qc_routes_and_legacy_contracts_remain_isolated() -> None:
    schema = app.openapi()
    assert "/knowledge" in schema["paths"]
    assert "/events" in schema["paths"]
    assert "/decisions" in schema["paths"]
    assert "/lab-observations" not in schema["paths"]

    qc_paths = {
        path: operations
        for path, operations in schema["paths"].items()
        if path.startswith("/api/v2/qc-observations")
    }
    assert set(qc_paths) == {
        "/api/v2/qc-observations",
        "/api/v2/qc-observations/{object_id}",
    }
    assert set(qc_paths["/api/v2/qc-observations"]) == {"post"}
    assert set(qc_paths["/api/v2/qc-observations/{object_id}"]) == {"get"}
    assert set(schema["paths"]["/api/v2/lab-observations"]) == {"get", "post"}
    assert set(schema["paths"]["/api/v2/lab-observations/{object_id}"]) == {"get"}

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "from smartcoat.api.main import app; "
                "assert 'smartcoat.domain.knowledge_objects_v2' not in sys.modules; "
                "schema = app.openapi(); "
                "assert set(schema['paths']['/api/v2/qc-observations']) == {'post'}; "
                "assert set(schema['paths']"
                "['/api/v2/qc-observations/{object_id}']) == {'get'}; "
                "assert 'smartcoat.domain.knowledge_objects_v2' not in sys.modules"
            ),
        ],
        env={**os.environ, "PYTHONPATH": str(PROJECT_ROOT / "src")},
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
