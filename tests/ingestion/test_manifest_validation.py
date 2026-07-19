from datetime import UTC, datetime
from uuid import UUID

import pytest

import smartcoat.ingestion as ingestion_api
from smartcoat.ingestion.models import (
    ConfidentialityLevel,
    GovernancePurpose,
    IngestionStatus,
    PurposeDecisionStatus,
    SchemaTarget,
    SourceFormat,
    SourceManifest,
    SourceType,
)
from smartcoat.ingestion.validation import ManifestRegistry, validate_manifest


def canonical_purpose_decisions(**updates: str) -> dict[str, str]:
    decisions = {
        "inventory": "approved",
        "retrieval": "not_requested",
        "analytics": "not_requested",
        "human_review": "approved",
        "model_training": "denied",
        "external_sharing": "denied",
    }
    decisions.update(updates)
    return decisions


def valid_manifest_payload() -> dict:
    return {
        "manifest_id": "11111111-1111-4111-8111-111111111111",
        "ingestion_job_id": "22222222-2222-4222-8222-222222222222",
        "source_type": "spreadsheet",
        "source_format": "csv",
        "source_system": "synthetic_lab_export",
        "source_reference": "synthetic://lab/trial-summary.csv",
        "organization_id": "org_synthetic",
        "site_id": "site_synthetic",
        "source_owner": "R&D steward",
        "confidentiality_level": "internal",
        "governance_schema_version": "smartcoat-governance-v1.1-draft",
        "purpose_decisions": canonical_purpose_decisions(),
        "schema_target": {"name": "technical_textile_trial", "version": "v1"},
        "checksum_sha256": "a" * 64,
        "source_created_at": "2026-01-02T03:04:05Z",
        "manifest_created_at": "2026-01-03T04:05:06Z",
        "dry_run": True,
    }


def valid_manifest(**updates: object) -> SourceManifest:
    payload = valid_manifest_payload()
    payload.update(updates)
    return SourceManifest.model_validate(payload)


def test_validated_workflow_creates_candidate() -> None:
    result = ManifestRegistry().process(valid_manifest())

    assert result.validation.status == IngestionStatus.VALIDATED
    assert result.accepted is True
    assert result.candidate is not None
    assert result.candidate.status == IngestionStatus.CANDIDATE_CREATED


def test_rejected_manifest_cannot_create_candidate() -> None:
    result = ManifestRegistry().process(
        {
            "source_type": "spreadsheet",
            "source_format": "csv",
            "source_system": "",
        }
    )

    assert result.validation.status == IngestionStatus.REJECTED
    assert result.validation.errors
    assert result.candidate is None


def test_dry_run_false_cannot_create_candidate() -> None:
    payload = valid_manifest_payload()
    payload["dry_run"] = False

    result = ManifestRegistry().process(payload)

    assert result.validation.status == IngestionStatus.REJECTED
    assert any(issue.field == "dry_run" for issue in result.validation.errors)
    assert result.candidate is None


def test_declared_model_training_approval_is_blocked_without_authorization() -> None:
    manifest = valid_manifest(
        purpose_decisions=canonical_purpose_decisions(model_training="approved")
    )

    result = ManifestRegistry().process(manifest)

    assert result.validation.status == IngestionStatus.BLOCKED
    assert result.validation.warnings[0].code == "model_training_authorization_not_verified"
    assert result.candidate is None


def test_approval_reference_is_metadata_and_does_not_authorize_candidate() -> None:
    manifest = valid_manifest(
        purpose_decisions=canonical_purpose_decisions(model_training="approved"),
        model_training_approval_reference="synthetic-approval-001",
    )

    result = ManifestRegistry().process(manifest)

    assert result.validation.status == IngestionStatus.BLOCKED
    assert result.candidate is None
    assert result.validation.warnings[0].field == "model_training_approval_reference"


def test_repeated_blocked_manifest_remains_blocked_and_registered() -> None:
    registry = ManifestRegistry()
    manifest = valid_manifest(
        purpose_decisions=canonical_purpose_decisions(model_training="in_review")
    )

    first = registry.process(manifest)
    second = registry.process(manifest)

    assert first.validation.status == IngestionStatus.BLOCKED
    assert second.validation.status == IngestionStatus.BLOCKED
    assert first.candidate is None
    assert second.candidate is None
    assert {warning.code for warning in second.validation.warnings} == {
        "blocked_manifest_repeated",
        "model_training_authorization_not_verified",
    }


def test_same_checksum_in_same_organization_is_duplicate() -> None:
    registry = ManifestRegistry()

    first = registry.process(valid_manifest())
    second = registry.process(
        valid_manifest(
            manifest_id="33333333-3333-4333-8333-333333333333",
            ingestion_job_id="44444444-4444-4444-8444-444444444444",
        )
    )

    assert first.candidate is not None
    assert second.validation.status == IngestionStatus.DUPLICATE
    assert second.candidate is None


def test_same_checksum_in_two_organizations_is_not_duplicate() -> None:
    registry = ManifestRegistry()

    first = registry.process(valid_manifest(organization_id="org_alpha"))
    second = registry.process(
        valid_manifest(
            manifest_id="33333333-3333-4333-8333-333333333333",
            organization_id="org_beta",
        )
    )

    assert first.validation.status == IngestionStatus.VALIDATED
    assert second.validation.status == IngestionStatus.VALIDATED
    assert first.candidate is not None
    assert second.candidate is not None
    assert first.candidate.candidate_id != second.candidate.candidate_id


def test_same_source_at_two_sites_is_one_organization_duplicate() -> None:
    registry = ManifestRegistry()

    first = registry.process(valid_manifest(site_id="site_alpha"))
    second = registry.process(
        valid_manifest(
            manifest_id="33333333-3333-4333-8333-333333333333",
            site_id="site_beta",
        )
    )

    assert first.candidate is not None
    assert first.candidate.site_id == "site_alpha"
    assert second.validation.status == IngestionStatus.DUPLICATE
    assert second.candidate is None


def test_candidate_id_is_stable_for_same_organization_source_and_schema() -> None:
    first = ManifestRegistry().process(valid_manifest())
    second = ManifestRegistry().process(
        valid_manifest(
            manifest_id="33333333-3333-4333-8333-333333333333",
            ingestion_job_id="44444444-4444-4444-8444-444444444444",
        )
    )

    assert first.candidate is not None
    assert second.candidate is not None
    assert first.candidate.candidate_id == second.candidate.candidate_id
    assert first.candidate.candidate_id.version == 5


def test_candidate_preserves_required_provenance() -> None:
    manifest = valid_manifest()
    result = ManifestRegistry().process(manifest)

    assert result.candidate is not None
    candidate = result.candidate
    assert candidate.manifest_id == UUID("11111111-1111-4111-8111-111111111111")
    assert candidate.ingestion_job_id == UUID("22222222-2222-4222-8222-222222222222")
    assert candidate.source_system == manifest.source_system
    assert candidate.source_reference == manifest.source_reference
    assert candidate.source_owner == manifest.source_owner
    assert candidate.source_created_at == datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)
    assert candidate.manifest_created_at == datetime(2026, 1, 3, 4, 5, 6, tzinfo=UTC)
    assert candidate.organization_id == manifest.organization_id
    assert candidate.site_id == manifest.site_id
    assert candidate.confidentiality_level == ConfidentialityLevel.INTERNAL
    assert candidate.governance_schema_version == "smartcoat-governance-v1.1-draft"
    assert candidate.purpose_decisions == {
        GovernancePurpose.INVENTORY: PurposeDecisionStatus.APPROVED,
        GovernancePurpose.RETRIEVAL: PurposeDecisionStatus.NOT_REQUESTED,
        GovernancePurpose.ANALYTICS: PurposeDecisionStatus.NOT_REQUESTED,
        GovernancePurpose.HUMAN_REVIEW: PurposeDecisionStatus.APPROVED,
        GovernancePurpose.MODEL_TRAINING: PurposeDecisionStatus.DENIED,
        GovernancePurpose.EXTERNAL_SHARING: PurposeDecisionStatus.DENIED,
    }
    assert candidate.schema_target == SchemaTarget(
        name="technical_textile_trial",
        version="v1",
    )
    assert candidate.checksum_sha256 == "a" * 64
    assert candidate.dry_run is True


@pytest.mark.parametrize(
    "fingerprint",
    ["", "short", "aaaaaaaaaaaaaaaa", "contains spaces 123"],
)
def test_invalid_or_trivial_fingerprint_is_rejected(fingerprint: str) -> None:
    payload = valid_manifest_payload()
    payload["checksum_sha256"] = None
    payload["content_fingerprint"] = fingerprint

    result = ManifestRegistry().process(payload)

    assert result.validation.status == IngestionStatus.REJECTED
    assert any(issue.field == "content_fingerprint" for issue in result.validation.errors)
    assert result.candidate is None


def test_duplicate_warning_names_checksum_field() -> None:
    registry = ManifestRegistry()
    registry.process(valid_manifest())

    duplicate = registry.process(valid_manifest())

    assert duplicate.validation.status == IngestionStatus.DUPLICATE
    assert duplicate.validation.warnings[0].field == "checksum_sha256"


def test_duplicate_warning_names_fingerprint_field() -> None:
    registry = ManifestRegistry()
    manifest = valid_manifest(
        checksum_sha256=None,
        content_fingerprint="synthetic-content-fingerprint-v1",
    )
    registry.process(manifest)

    duplicate = registry.process(manifest)

    assert duplicate.validation.status == IngestionStatus.DUPLICATE
    assert duplicate.validation.warnings[0].field == "content_fingerprint"


def test_stateless_validation_does_not_create_candidate() -> None:
    result = validate_manifest(valid_manifest())

    assert result.status == IngestionStatus.VALIDATED
    assert result.accepted is True


def test_missing_canonical_purpose_is_rejected() -> None:
    payload = valid_manifest_payload()
    del payload["purpose_decisions"]["external_sharing"]

    result = ManifestRegistry().process(payload)

    assert result.validation.status == IngestionStatus.REJECTED
    assert any(issue.field == "purpose_decisions" for issue in result.validation.errors)


def test_retired_confidentiality_value_is_rejected() -> None:
    payload = valid_manifest_payload()
    payload["confidentiality_level"] = "highly_confidential"

    result = ManifestRegistry().process(payload)

    assert result.validation.status == IngestionStatus.REJECTED
    assert any(issue.field == "confidentiality_level" for issue in result.validation.errors)


def test_package_api_exposes_only_validated_candidate_workflow() -> None:
    assert "ManifestRegistry" in ingestion_api.__all__
    assert "create_candidate" not in ingestion_api.__all__
    assert "IngestionCandidate" not in ingestion_api.__all__
    assert "validate_manifest" not in ingestion_api.__all__


def test_manifest_enum_values_remain_stable() -> None:
    assert SourceType.SPREADSHEET.value == "spreadsheet"
    assert SourceFormat.CSV.value == "csv"
    assert ConfidentialityLevel.STRATEGIC.value == "strategic"
    assert GovernancePurpose.EXTERNAL_SHARING.value == "external_sharing"
    assert PurposeDecisionStatus.REVOKED.value == "revoked"
