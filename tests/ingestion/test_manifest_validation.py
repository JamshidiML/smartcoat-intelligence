from smartcoat.ingestion.models import (
    ConfidentialityLevel,
    IngestionStatus,
    PermittedUse,
    SchemaTarget,
    SourceFormat,
    SourceManifest,
    SourceType,
)
from smartcoat.ingestion.validation import ManifestRegistry, create_candidate, validate_manifest


def valid_manifest() -> SourceManifest:
    return SourceManifest(
        source_type=SourceType.SPREADSHEET,
        source_format=SourceFormat.CSV,
        source_system="synthetic_lab_export",
        source_reference="synthetic://lab/trial-summary.csv",
        organization_id="org_synthetic",
        site_id="site_synthetic",
        source_owner="R&D steward",
        confidentiality_level=ConfidentialityLevel.INTERNAL,
        permitted_uses=[PermittedUse.INVENTORY_ONLY, PermittedUse.HUMAN_REVIEW],
        schema_target=SchemaTarget(name="technical_textile_trial", version="v1"),
        checksum_sha256="a" * 64,
    )


def test_valid_manifest_produces_validated_result() -> None:
    manifest = valid_manifest()

    result = validate_manifest(manifest)

    assert result.status == IngestionStatus.VALIDATED
    assert result.accepted is True
    assert result.duplicate_key == f"sha256:{'a' * 64}"


def test_invalid_manifest_returns_structured_errors() -> None:
    result = validate_manifest(
        {
            "source_type": "spreadsheet",
            "source_format": "csv",
            "source_system": "",
        }
    )

    assert result.status == IngestionStatus.REJECTED
    assert result.errors
    assert {issue.code for issue in result.errors} == {"invalid_manifest"}


def test_duplicate_manifest_is_deterministic() -> None:
    registry = ManifestRegistry()
    manifest = valid_manifest()

    first = registry.validate(manifest)
    second = registry.validate(manifest)

    assert first.status == IngestionStatus.VALIDATED
    assert second.status == IngestionStatus.DUPLICATE
    assert second.duplicate_key == first.duplicate_key


def test_model_training_permission_blocks_until_governed() -> None:
    manifest = valid_manifest().model_copy(
        update={"permitted_uses": [PermittedUse.INVENTORY_ONLY, PermittedUse.MODEL_TRAINING]}
    )

    result = validate_manifest(manifest)

    assert result.status == IngestionStatus.BLOCKED
    assert result.warnings[0].code == "model_training_requires_approval"


def test_create_candidate_preserves_manifest_boundary_metadata() -> None:
    manifest = valid_manifest()

    candidate = create_candidate(manifest)

    assert candidate.manifest_id == manifest.manifest_id
    assert candidate.organization_id == "org_synthetic"
    assert candidate.confidentiality_level == ConfidentialityLevel.INTERNAL
    assert candidate.dry_run is True
