from __future__ import annotations

import io
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from openpyxl import Workbook

from smartcoat.api.main import app
from smartcoat.api.routes import lab_capture_ai
from smartcoat.api.routes.lab_capture_ai import (
    LocalAIPreflightResponse,
    ReadinessCheck,
    get_structured_extraction_provider,
    get_transcription_provider,
)
from smartcoat.api.routes.lab_project_captures import (
    get_lab_project_capture_audit_service,
    get_lab_project_capture_repository,
)
from smartcoat.api.routes.lab_project_imports import get_local_evidence_registry
from smartcoat.core.config import Settings
from smartcoat.domain.base import LifecycleState
from smartcoat.domain.evidence_provenance import KnowledgeObjectV2EvidenceComposition
from smartcoat.domain.knowledge_audit import GovernedKnowledgeCreateCommand
from smartcoat.domain.knowledge_objects_v2 import (
    KnowledgeObjectV2CoreRecord,
    KnowledgeObjectV2PersistedStateSnapshot,
)
from smartcoat.services.lab_project_extraction import DeterministicFakeExtractionProvider
from smartcoat.services.local_evidence_registry import LocalEvidenceRegistry
from smartcoat.services.voice_transcription import (
    DeterministicFakeTranscriptionProvider,
    TranscriptionResult,
)

NOW = datetime(2026, 8, 10, 9, 0, tzinfo=UTC)
OBJECT_ID = UUID("6d27db4e-5428-4e04-a85c-0b252f21d1be")
AUDIT_EVENT_ID = UUID("dd8f3945-40b7-46aa-9009-0f6f799dc62a")
ORGANIZATION_ID = "smartcoat-startup"
XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _composition(command: GovernedKnowledgeCreateCommand) -> KnowledgeObjectV2EvidenceComposition:
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
        provenance=command.provenance,
    )


class IntegratedAuditService:
    def __init__(self) -> None:
        self.commands: list[GovernedKnowledgeCreateCommand] = []
        self.knowledge: KnowledgeObjectV2EvidenceComposition | None = None

    def create(self, command: GovernedKnowledgeCreateCommand) -> Any:
        self.commands.append(command)
        self.knowledge = _composition(command)
        return SimpleNamespace(
            knowledge=self.knowledge,
            audit_event=SimpleNamespace(event_id=AUDIT_EVENT_ID, audit_sequence=1),
        )


class IntegratedRepository:
    def __init__(self, service: IntegratedAuditService) -> None:
        self.service = service

    def list_object_ids_by_type_and_tag(self, **kwargs: Any) -> tuple[UUID, ...]:
        knowledge = self.service.knowledge
        if knowledge is None or knowledge.core.organization_id != kwargs["organization_id"]:
            return ()
        return (knowledge.core.object_id,)

    def get(self, *, object_id: UUID, organization_id: str) -> Any:
        knowledge = self.service.knowledge
        if (
            knowledge is None
            or knowledge.core.object_id != object_id
            or knowledge.core.organization_id != organization_id
        ):
            return None
        return knowledge


@pytest.fixture()
def integrated_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    service = IntegratedAuditService()
    repository = IntegratedRepository(service)
    registry = LocalEvidenceRegistry(tmp_path / "assets", max_upload_bytes=2 * 1024 * 1024)
    readiness = ReadinessCheck(ready=True, detail="Synthetic local dependency ready")
    preflight = LocalAIPreflightResponse(
        ready=True,
        mlx_whisper_import=readiness,
        whisper_model=readiness,
        ollama_reachability=readiness,
        ollama_model=readiness,
        asset_directory=readiness,
    )
    monkeypatch.setattr(lab_capture_ai, "build_preflight_response", lambda: preflight)
    monkeypatch.setattr(
        lab_capture_ai,
        "get_settings",
        lambda: Settings(asset_root=tmp_path / "assets", max_upload_bytes=2 * 1024 * 1024),
    )
    app.dependency_overrides[get_lab_project_capture_audit_service] = lambda: service
    app.dependency_overrides[get_lab_project_capture_repository] = lambda: repository
    app.dependency_overrides[get_local_evidence_registry] = lambda: registry
    try:
        yield TestClient(app), service
    finally:
        app.dependency_overrides.clear()


def _asset_evidence(descriptor: dict[str, Any]) -> dict[str, Any]:
    return {
        "evidence_id": descriptor["evidence_id"],
        "evidence_type": descriptor["evidence_type"],
        "filename": descriptor["original_filename"],
        "media_type": descriptor["media_type"],
        "source_reference": descriptor["source_reference"],
        "sha256": descriptor["sha256"],
        "captured_at": descriptor["captured_at"],
    }


def _confirm(candidate: dict[str, Any]) -> dict[str, Any]:
    candidate["human_confirmed"] = True
    candidate["human_confirmed_by"] = "synthetic-lab-reviewer"
    candidate["human_confirmed_at"] = NOW.isoformat()
    return candidate


def _xlsx_bytes() -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Intake"
    sheet.append(
        [
            "Project Number",
            "Project",
            "Customer",
            "Request",
            "Target Application",
            "Base Fabric",
            "Formulation",
            "Approach",
            "Result",
            "Failure Reason",
            "Test",
            "Temperature",
            "Coating Weight",
            "Sample",
            "Shipment Date",
            "Production Feasibility",
            "Cost",
            "Comments",
        ]
    )
    sheet.append(
        [
            "P-SYN-INT-02",
            "Synthetic Excel intake",
            "Example Customer",
            "Evaluate a generalized laboratory concept.",
            "Synthetic protective application",
            "Synthetic woven substrate",
            "Component Alpha 80 / Component Beta 20",
            "Synthetic coating trial",
            "failed",
            "Synthetic adhesion threshold was not met.",
            "Generalized adhesion test",
            "180 degC",
            "35 g/m2",
            "SOURCE-SAMPLE-07",
            "2026-08-10",
            "requires review",
            "125 EUR",
            "Synthetic workbook row only.",
        ]
    )
    stream = io.BytesIO()
    workbook.save(stream)
    workbook.close()
    return stream.getvalue()


def test_real_app_registers_pilot_and_existing_routes(integrated_client: Any) -> None:
    client, _service = integrated_client
    schema_paths = app.openapi()["paths"]
    required: dict[str, tuple[str, ...]] = {
        "/api/v2/lab-capture/preflight": ("get",),
        "/api/v2/lab-capture/process-audio": ("post",),
        "/api/v2/lab-capture/extract-text": ("post",),
        "/api/v2/lab-capture/assets": ("post",),
        "/api/v2/lab-capture/import-excel": ("post",),
        "/api/v2/lab-project-captures": ("get", "post"),
        "/api/v2/lab-project-captures/{object_id}": ("get",),
        "/health": ("get",),
        "/api/v2/lab-observations": ("post",),
        "/api/v2/qc-observations": ("post",),
    }
    for path, methods in required.items():
        assert path in schema_paths
        assert set(methods) <= set(schema_paths[path])

    assert client.get("/health").json()["status"] == "ok"
    assert client.get("/lab-observations").status_code == 200
    assert client.get("/lab-project-capture").status_code == 200
    assert client.get("/api/v2/lab-capture/preflight").json()["ready"] is True
    listed = client.get(
        "/api/v2/lab-project-captures",
        headers={"X-SmartCoat-Organization-ID": ORGANIZATION_ID},
    )
    assert listed.status_code == 200
    assert listed.json()["items"] == []


def test_integrated_voice_review_evidence_save_and_reads(
    integrated_client: Any,
) -> None:
    client, service = integrated_client
    transcript = "Immutable synthetic voice transcript for project intake."
    extraction = DeterministicFakeExtractionProvider()
    transcription = DeterministicFakeTranscriptionProvider(
        TranscriptionResult(
            transcript=transcript,
            detected_language="en",
            duration_seconds=1.25,
            provider="deterministic-fake",
            model="synthetic-local-model",
        )
    )
    app.dependency_overrides[get_structured_extraction_provider] = lambda: extraction
    app.dependency_overrides[get_transcription_provider] = lambda: transcription
    headers = {"X-SmartCoat-Organization-ID": ORGANIZATION_ID}
    audio = b"RIFF0000WAVEsynthetic-audio"

    processed = client.post(
        "/api/v2/lab-capture/process-audio",
        content=audio,
        headers={
            **headers,
            "Content-Type": "audio/wav",
            "X-SmartCoat-Filename": "synthetic.wav",
        },
    )
    assert processed.status_code == 200, processed.text
    candidate = processed.json()["candidate"]
    assert candidate["source_kind"] == "voice"
    assert candidate["transcript"] == transcript
    assert candidate["human_confirmed"] is False
    assert service.commands == []

    supplemental = "Question: Who reviews this?\nAnswer: Synthetic reviewer."
    reextracted = client.post(
        "/api/v2/lab-capture/extract-text",
        headers=headers,
        json={
            "transcript": transcript,
            "source_kind": "voice",
            "supplemental_context": supplemental,
            "project_hints": {
                "project_id": "P-SYN-INT-01",
                "project_name": "Synthetic voice intake",
            },
            "actor_metadata": {
                "actor_id": "synthetic-lab-reviewer",
                "actor_role": "lab_engineer",
            },
        },
    )
    assert reextracted.status_code == 200
    candidate = reextracted.json()["candidate"]
    assert candidate["source_kind"] == "voice"
    assert candidate["transcript"] == transcript
    assert supplemental not in candidate["transcript"]

    wrong_org = client.post(
        "/api/v2/lab-capture/extract-text",
        headers={"X-SmartCoat-Organization-ID": "other-organization"},
        json={
            "transcript": transcript,
            "actor_metadata": {"actor_id": "reviewer", "actor_role": "lab_engineer"},
        },
    )
    assert wrong_org.status_code == 403

    evidence = []
    for filename, media_type, content in (
        ("synthetic.wav", "audio/wav", audio),
        ("capture-transcript.txt", "text/plain", transcript.encode()),
    ):
        registered = client.post(
            "/api/v2/lab-capture/assets",
            content=content,
            headers={
                **headers,
                "Content-Type": media_type,
                "X-SmartCoat-Filename": filename,
            },
        )
        assert registered.status_code == 201, registered.text
        evidence.append(_asset_evidence(registered.json()))

    candidate["evidence"] = evidence
    direct_ai = client.post(
        "/api/v2/lab-project-captures",
        headers=headers,
        json=candidate,
    )
    assert direct_ai.status_code == 422

    confirmed = client.post(
        "/api/v2/lab-project-captures",
        headers=headers,
        json=_confirm(candidate),
    )
    assert confirmed.status_code == 201, confirmed.text
    created = confirmed.json()
    assert created["capture"]["lifecycle"] == "draft"
    assert created["audit_event_id"] == str(AUDIT_EVENT_ID)
    assert len(service.commands) == 1
    command = service.commands[0]
    assert {item.evidence_id for item in command.evidence} == {
        evidence[0]["evidence_id"],
        evidence[1]["evidence_id"],
    }
    assert command.provenance.source_reference.startswith("lab-project-capture://")
    assert [item.transformation_type for item in command.provenance.transformation_history] == [
        "local_structured_extraction",
        "human_confirmation",
    ]

    listed = client.get("/api/v2/lab-project-captures", headers=headers)
    detail = client.get(
        "/api/v2/lab-project-captures/" + created["capture"]["object_id"],
        headers=headers,
    )
    assert listed.status_code == 200
    assert listed.json()["items"] == [created["capture"]]
    assert detail.json() == created["capture"]


def test_integrated_excel_dry_run_review_and_canonical_save(integrated_client: Any) -> None:
    client, service = integrated_client
    headers = {
        "Content-Type": XLSX_MEDIA_TYPE,
        "X-SmartCoat-Filename": "synthetic-intake.xlsx",
        "X-SmartCoat-Organization-ID": ORGANIZATION_ID,
    }
    imported = client.post(
        "/api/v2/lab-capture/import-excel",
        content=_xlsx_bytes(),
        headers=headers,
    )
    assert imported.status_code == 200, imported.text
    report = imported.json()
    assert report["dry_run"] is True
    assert report["canonical_writes"] == 0
    assert service.commands == []

    imported_row = report["candidates"][0]
    candidate = imported_row["candidate"]
    assert candidate["approaches"][0]["approach_id"] == "C-A-001"
    assert candidate["samples"][0]["sample_id"] == "C-S-001"
    assert candidate["samples"][0]["source_sample_id"] == "SOURCE-SAMPLE-07"
    assert candidate["formulation_source_text"] == "Component Alpha 80 / Component Beta 20"
    assert candidate["materials"] == []
    assert candidate["source_cell_references"]
    assert imported_row["cell_provenance"]
    assert "formulation_requires_structured_review" in {
        warning["code"] for warning in report["warnings"]
    }

    saved = client.post(
        "/api/v2/lab-project-captures",
        headers={"X-SmartCoat-Organization-ID": ORGANIZATION_ID},
        json=_confirm(candidate),
    )
    assert saved.status_code == 201, saved.text
    assert saved.json()["capture"]["lifecycle"] == "draft"
    assert len(service.commands) == 1
    command = service.commands[0]
    assert len(command.evidence) == 1
    assert command.evidence[0].source_reference == report["source_reference"]
    quality = command.create.mutable_state.content["quality_summary"][0]
    assert quality["formulation_source_text"] == "Component Alpha 80 / Component Beta 20"
    assert quality["source_cell_references"] == candidate["source_cell_references"]
    assert any(
        "no material or quantity was inferred" in warning
        for warning in quality["extraction_warnings"]
    )
    assert command.provenance.source_reference.startswith("lab-project-capture://")
