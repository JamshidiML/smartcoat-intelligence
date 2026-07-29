from __future__ import annotations

import os
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from smartcoat.api.main import app
from smartcoat.api.routes.lab_observations import (
    LAB_OBSERVATION_ROLE,
    LAB_OBSERVATION_TAG,
    LAB_SOURCE_SYSTEM,
    get_lab_observation_audit_service,
    get_lab_observation_repository,
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
from smartcoat.domain.knowledge_objects import KnowledgeObjectType
from smartcoat.domain.knowledge_objects_v2 import (
    ConfidentialityLevel,
    KnowledgeObjectV2CoreRecord,
    KnowledgeObjectV2MutableState,
    KnowledgeObjectV2PersistedStateSnapshot,
    OwnerReference,
)
from smartcoat.storage.repositories.knowledge_v2_repository import (
    KnowledgeObjectV2RepositoryError,
)

NOW = datetime(2026, 7, 29, 10, 0, tzinfo=UTC)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
OBJECT_IDS = (
    UUID("11111111-1111-4111-8111-111111111111"),
    UUID("22222222-2222-4222-8222-222222222222"),
    UUID("33333333-3333-4333-8333-333333333333"),
)


def _canonical_composition(
    object_id: UUID,
    *,
    organization_id: str = "synthetic-lab-org",
    source_system: str = LAB_SOURCE_SYSTEM,
    position: int = 0,
) -> KnowledgeObjectV2EvidenceComposition:
    evidence_id = f"lab-observation:evidence-{position}"
    source_reference = f"lab-notebook://synthetic/list/{position}"
    project_reference = ContextReference(
        context_type=ContextType.PROJECT,
        reference_id=f"LAB-LIST-{position:03d}",
        id_kind=ContextIdKind.EXTERNAL,
        source_system=LAB_SOURCE_SYSTEM,
        display_name=f"Synthetic List Project {position}",
        version=None,
        relationship_role=LAB_OBSERVATION_ROLE,
        source_reference=source_reference,
        evidence_reference=evidence_id,
        attributes={},
    )
    observation = f"Synthetic bounded list observation {position}."
    state = KnowledgeObjectV2MutableState(
        title=f"Synthetic List Observation {position}",
        description=None,
        knowledge_type=KnowledgeObjectType.OBSERVATION,
        owner=OwnerReference(
            owner_id="synthetic-list-engineer",
            role="lab_engineer",
        ),
        confidentiality=ConfidentialityLevel.INTERNAL,
        uncertainty=None,
        tags=(LAB_OBSERVATION_TAG,),
        content={"observation": observation},
        context=KnowledgeContext(references=[project_reference]),
        evidence_ids=(evidence_id,),
        knowledge_relationships=(),
        decision_relationships=(),
    )
    evidence = EvidenceReference.model_validate(
        {
            "evidence_id": evidence_id,
            "evidence_type": EvidenceType.OBSERVATION,
            "completeness": EvidenceCompleteness.COMPLETE,
            "title": state.title,
            "description": observation,
            "source_reference": source_reference,
            "source_system": LAB_SOURCE_SYSTEM,
            "captured_by": "synthetic-list-engineer",
            "captured_at": NOW,
            "source_created_at": NOW,
            "confidentiality": ConfidentialityLevel.INTERNAL,
            "context_reference": project_reference,
        }
    )
    provenance = ProvenanceV2(
        source_system=source_system,
        source_reference=source_reference,
        created_by="synthetic-list-engineer",
        creation_method=CreationMethod.MANUAL,
        captured_at=NOW,
        source_created_at=NOW,
        completeness=ProvenanceCompleteness.COMPLETE,
    )
    return KnowledgeObjectV2EvidenceComposition(
        core=KnowledgeObjectV2CoreRecord(
            object_id=object_id,
            organization_id=organization_id,
            revision=1,
            lifecycle_state=LifecycleState.DRAFT,
            created_at=NOW - timedelta(minutes=position),
            updated_at=NOW - timedelta(minutes=position),
            mutable_state=KnowledgeObjectV2PersistedStateSnapshot.from_mutable_state(state),
        ),
        evidence=(evidence,),
        provenance=provenance,
    )


class FakeRepository:
    def __init__(
        self,
        object_ids: tuple[UUID, ...] = (),
        *,
        compositions: dict[UUID, KnowledgeObjectV2EvidenceComposition] | None = None,
        ids_by_organization: dict[str, tuple[UUID, ...]] | None = None,
        list_error: KnowledgeObjectV2RepositoryError | None = None,
    ) -> None:
        self.object_ids = object_ids
        self.compositions = compositions or {}
        self.ids_by_organization = ids_by_organization
        self.list_error = list_error
        self.list_calls: list[dict[str, Any]] = []
        self.get_calls: list[tuple[UUID, str]] = []

    def list_object_ids_by_type_and_tag(
        self,
        *,
        organization_id: str,
        knowledge_type: str,
        required_tag: str,
        limit: int,
        offset: int,
    ) -> tuple[UUID, ...]:
        self.list_calls.append(
            {
                "organization_id": organization_id,
                "knowledge_type": knowledge_type,
                "required_tag": required_tag,
                "limit": limit,
                "offset": offset,
            }
        )
        if self.list_error is not None:
            raise self.list_error
        if self.ids_by_organization is not None:
            return self.ids_by_organization.get(organization_id, ())
        return self.object_ids

    def get(self, *, object_id: UUID, organization_id: str) -> Any:
        self.get_calls.append((object_id, organization_id))
        composition = self.compositions.get(object_id)
        if composition is None or composition.core.organization_id != organization_id:
            return None
        return composition


def _repository_override(repository: FakeRepository) -> Any:
    return lambda: repository


@pytest.fixture(autouse=True)
def _restore_dependency_overrides() -> Any:
    original = app.dependency_overrides.copy()
    try:
        yield
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(original)


def test_list_defaults_to_limit_20_offset_0() -> None:
    composition = _canonical_composition(OBJECT_IDS[0])
    repository = FakeRepository(
        (OBJECT_IDS[0],),
        compositions={OBJECT_IDS[0]: composition},
    )
    app.dependency_overrides[get_lab_observation_repository] = lambda: repository

    response = TestClient(app).get(
        "/api/v2/lab-observations",
        headers={"X-SmartCoat-Organization-ID": "synthetic-lab-org"},
    )

    assert response.status_code == 200
    assert repository.list_calls == [
        {
            "organization_id": "synthetic-lab-org",
            "knowledge_type": "observation",
            "required_tag": "lab-observation",
            "limit": 21,
            "offset": 0,
        }
    ]
    body = response.json()
    assert body["limit"] == 20
    assert body["offset"] == 0
    assert body["returned_count"] == len(body["items"]) == 1
    assert body["has_more"] is False


def test_list_returns_bounded_page_and_has_more() -> None:
    compositions = {
        object_id: _canonical_composition(object_id, position=position)
        for position, object_id in enumerate(OBJECT_IDS)
    }
    repository = FakeRepository(OBJECT_IDS, compositions=compositions)
    app.dependency_overrides[get_lab_observation_repository] = lambda: repository

    response = TestClient(app).get(
        "/api/v2/lab-observations?limit=2&offset=4",
        headers={"X-SmartCoat-Organization-ID": "synthetic-lab-org"},
    )

    assert response.status_code == 200
    body = response.json()
    assert [item["object_id"] for item in body["items"]] == [
        str(OBJECT_IDS[0]),
        str(OBJECT_IDS[1]),
    ]
    assert body["limit"] == 2
    assert body["offset"] == 4
    assert body["returned_count"] == 2
    assert body["has_more"] is True
    assert repository.list_calls[0]["limit"] == 3
    assert repository.list_calls[0]["offset"] == 4


def test_list_final_and_empty_pages() -> None:
    composition = _canonical_composition(OBJECT_IDS[0])
    final_repository = FakeRepository(
        (OBJECT_IDS[0],),
        compositions={OBJECT_IDS[0]: composition},
    )
    app.dependency_overrides[get_lab_observation_repository] = lambda: final_repository
    client = TestClient(app)

    final_page = client.get(
        "/api/v2/lab-observations?limit=2",
        headers={"X-SmartCoat-Organization-ID": "synthetic-lab-org"},
    )
    empty_repository = FakeRepository()
    app.dependency_overrides[get_lab_observation_repository] = lambda: empty_repository
    empty_page = client.get(
        "/api/v2/lab-observations?limit=2&offset=12",
        headers={"X-SmartCoat-Organization-ID": "synthetic-lab-org"},
    )

    assert final_page.status_code == 200
    assert final_page.json()["returned_count"] == 1
    assert final_page.json()["has_more"] is False
    assert empty_page.status_code == 200
    assert empty_page.json()["items"] == []
    assert empty_page.json()["returned_count"] == 0
    assert empty_page.json()["has_more"] is False


def test_list_rejects_invalid_pagination() -> None:
    repository = FakeRepository()
    app.dependency_overrides[get_lab_observation_repository] = lambda: repository
    client = TestClient(app)

    for query in ("limit=0", "limit=101", "offset=-1"):
        response = client.get(
            f"/api/v2/lab-observations?{query}",
            headers={"X-SmartCoat-Organization-ID": "synthetic-lab-org"},
        )
        assert response.status_code == 422

    assert repository.list_calls == []
    assert repository.get_calls == []


def test_list_is_organization_scoped_and_read_only() -> None:
    composition = _canonical_composition(OBJECT_IDS[0])
    repository = FakeRepository(
        compositions={OBJECT_IDS[0]: composition},
        ids_by_organization={
            "synthetic-lab-org": (OBJECT_IDS[0],),
            "another-synthetic-org": (),
        },
    )
    app.dependency_overrides[get_lab_observation_repository] = lambda: repository
    assert get_lab_observation_audit_service not in app.dependency_overrides
    client = TestClient(app)

    primary = client.get(
        "/api/v2/lab-observations",
        headers={"X-SmartCoat-Organization-ID": "  synthetic-lab-org  "},
    )
    other = client.get(
        "/api/v2/lab-observations",
        headers={"X-SmartCoat-Organization-ID": "another-synthetic-org"},
    )

    assert primary.status_code == 200
    assert primary.json()["returned_count"] == 1
    assert other.status_code == 200
    assert other.json()["items"] == []
    assert [call["organization_id"] for call in repository.list_calls] == [
        "synthetic-lab-org",
        "another-synthetic-org",
    ]
    assert repository.get_calls == [
        (OBJECT_IDS[0], "synthetic-lab-org"),
    ]
    assert get_lab_observation_audit_service not in app.dependency_overrides


def test_list_maps_repository_or_composition_failures_safely() -> None:
    client = TestClient(app)
    failing_repositories = (
        FakeRepository(
            list_error=KnowledgeObjectV2RepositoryError(
                "synthetic_repository_code",
                "synthetic raw repository text",
            )
        ),
        FakeRepository((OBJECT_IDS[0],)),
        FakeRepository(
            (OBJECT_IDS[0],),
            compositions={
                OBJECT_IDS[0]: _canonical_composition(
                    OBJECT_IDS[0],
                    source_system="synthetic-non-lab-source",
                )
            },
        ),
    )

    for repository in failing_repositories:
        app.dependency_overrides[get_lab_observation_repository] = _repository_override(repository)
        response = client.get(
            "/api/v2/lab-observations",
            headers={"X-SmartCoat-Organization-ID": "synthetic-lab-org"},
        )
        assert response.status_code == 500
        assert response.json() == {"detail": "Lab observation list could not be loaded"}
        assert "synthetic_repository_code" not in response.text
        assert "synthetic raw repository text" not in response.text


def test_list_openapi_and_import_isolation() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "from smartcoat.api.main import app; "
                "assert 'smartcoat.domain.knowledge_objects_v2' not in sys.modules; "
                "schema = app.openapi(); "
                "operations = schema['paths']['/api/v2/lab-observations']; "
                "assert set(operations) == {'get', 'post'}; "
                "assert 'smartcoat.domain.knowledge_objects_v2' not in sys.modules"
            ),
        ],
        cwd=PROJECT_ROOT,
        env={**os.environ, "PYTHONPATH": str(PROJECT_ROOT / "src")},
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    schema = app.openapi()
    collection = schema["paths"]["/api/v2/lab-observations"]
    detail = schema["paths"]["/api/v2/lab-observations/{object_id}"]
    assert set(collection) == {"get", "post"}
    assert set(detail) == {"get"}
    parameters = {parameter["name"]: parameter for parameter in collection["get"]["parameters"]}
    assert parameters["limit"]["schema"]["minimum"] == 1
    assert parameters["limit"]["schema"]["maximum"] == 100
    assert parameters["offset"]["schema"]["minimum"] == 0
