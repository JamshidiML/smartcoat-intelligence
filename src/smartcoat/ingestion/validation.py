from collections.abc import Iterable, Mapping
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from pydantic import ValidationError

from smartcoat.ingestion.models import (
    GovernancePurpose,
    IngestionCandidate,
    IngestionStatus,
    IngestionWorkflowResult,
    ManifestValidationIssue,
    ManifestValidationResult,
    PurposeDecisionStatus,
    SourceManifest,
)

CANDIDATE_NAMESPACE = uuid5(NAMESPACE_URL, "urn:smartcoat:ingestion-candidate:v1")


def _parse_manifest(
    manifest: SourceManifest | Mapping[str, Any],
) -> tuple[SourceManifest | None, ManifestValidationResult | None]:
    payload = (
        manifest.model_dump(mode="python") if isinstance(manifest, SourceManifest) else manifest
    )
    try:
        return SourceManifest.model_validate(payload), None
    except ValidationError as error:
        return None, ManifestValidationResult(
            status=IngestionStatus.REJECTED,
            errors=[
                ManifestValidationIssue(
                    code="invalid_manifest",
                    message=str(detail["msg"]),
                    field=".".join(str(part) for part in detail["loc"]) or None,
                )
                for detail in error.errors()
            ],
        )


def _validate_parsed_manifest(
    manifest: SourceManifest,
    known_duplicate_keys: Iterable[str] | None = None,
) -> ManifestValidationResult:
    duplicate_key = manifest.duplicate_key
    model_training_decision = manifest.purpose_decisions[GovernancePurpose.MODEL_TRAINING]
    if model_training_decision in {
        PurposeDecisionStatus.IN_REVIEW,
        PurposeDecisionStatus.APPROVED,
    }:
        return ManifestValidationResult(
            manifest_id=manifest.manifest_id,
            status=IngestionStatus.BLOCKED,
            warnings=[
                ManifestValidationIssue(
                    code="model_training_authorization_not_verified",
                    message=(
                        "A declared model-training decision or approval reference is metadata "
                        "only; service/API authorization must be verified before candidate "
                        "creation."
                    ),
                    field="model_training_approval_reference",
                )
            ],
            duplicate_key=duplicate_key,
        )

    if duplicate_key in set(known_duplicate_keys or []):
        return ManifestValidationResult(
            manifest_id=manifest.manifest_id,
            status=IngestionStatus.DUPLICATE,
            warnings=[
                ManifestValidationIssue(
                    code="duplicate_manifest",
                    message=(
                        "A manifest with the same organization-scoped checksum or fingerprint "
                        "was already accepted."
                    ),
                    field=manifest.duplicate_source_field,
                )
            ],
            duplicate_key=duplicate_key,
        )

    return ManifestValidationResult(
        manifest_id=manifest.manifest_id,
        status=IngestionStatus.VALIDATED,
        duplicate_key=duplicate_key,
    )


def validate_manifest(
    manifest: SourceManifest | Mapping[str, Any],
    known_duplicate_keys: Iterable[str] | None = None,
) -> ManifestValidationResult:
    """Validate metadata without creating or registering a candidate."""

    parsed, invalid_result = _parse_manifest(manifest)
    if invalid_result is not None:
        return invalid_result
    if parsed is None:
        raise RuntimeError("manifest parsing produced no result")
    return _validate_parsed_manifest(parsed, known_duplicate_keys)


def _build_validated_candidate(
    manifest: SourceManifest,
    validation: ManifestValidationResult,
) -> IngestionCandidate:
    if validation.status != IngestionStatus.VALIDATED:
        raise ValueError("candidate creation requires VALIDATED status")
    if validation.manifest_id != manifest.manifest_id:
        raise ValueError("validation result does not belong to this manifest")
    if validation.duplicate_key != manifest.duplicate_key:
        raise ValueError("validation duplicate identity does not match this manifest")
    if manifest.dry_run is not True:
        raise ValueError("ingestion prototype candidates require dry_run=True")
    if manifest.purpose_decisions[GovernancePurpose.MODEL_TRAINING] in {
        PurposeDecisionStatus.IN_REVIEW,
        PurposeDecisionStatus.APPROVED,
    }:
        raise ValueError("model-training authorization is not verified by this prototype")

    return IngestionCandidate(
        candidate_id=uuid5(CANDIDATE_NAMESPACE, manifest.candidate_identity),
        manifest_id=manifest.manifest_id,
        ingestion_job_id=manifest.ingestion_job_id,
        source_type=manifest.source_type,
        source_format=manifest.source_format,
        source_system=manifest.source_system,
        source_reference=manifest.source_reference,
        source_owner=manifest.source_owner,
        source_created_at=manifest.source_created_at,
        manifest_created_at=manifest.manifest_created_at,
        organization_id=manifest.organization_id,
        site_id=manifest.site_id,
        confidentiality_level=manifest.confidentiality_level,
        governance_schema_version=manifest.governance_schema_version,
        purpose_decisions=manifest.purpose_decisions,
        model_training_approval_reference=manifest.model_training_approval_reference,
        schema_target=manifest.schema_target,
        checksum_sha256=manifest.checksum_sha256,
        content_fingerprint=manifest.content_fingerprint,
        duplicate_key=manifest.duplicate_key,
        dry_run=True,
        created_at=manifest.manifest_created_at,
    )


class ManifestRegistry:
    """In-memory registry and the approved validated candidate workflow."""

    def __init__(self, known_duplicate_keys: Iterable[str] | None = None) -> None:
        self._known_duplicate_keys = set(known_duplicate_keys or [])
        self._blocked_duplicate_keys: set[str] = set()

    def process(
        self,
        manifest: SourceManifest | Mapping[str, Any],
    ) -> IngestionWorkflowResult:
        parsed, invalid_result = _parse_manifest(manifest)
        if invalid_result is not None:
            return IngestionWorkflowResult(validation=invalid_result)
        if parsed is None:
            raise RuntimeError("manifest parsing produced no result")

        validation = _validate_parsed_manifest(parsed, self._known_duplicate_keys)
        if validation.status == IngestionStatus.BLOCKED:
            if parsed.duplicate_key in self._blocked_duplicate_keys:
                validation.warnings.append(
                    ManifestValidationIssue(
                        code="blocked_manifest_repeated",
                        message=(
                            "This organization-scoped source remains blocked; repeated submission "
                            "does not create a candidate or change duplicate state."
                        ),
                        field=parsed.duplicate_source_field,
                    )
                )
            self._blocked_duplicate_keys.add(parsed.duplicate_key)
            return IngestionWorkflowResult(validation=validation)

        if validation.status != IngestionStatus.VALIDATED:
            return IngestionWorkflowResult(validation=validation)

        candidate = _build_validated_candidate(parsed, validation)
        self._known_duplicate_keys.add(parsed.duplicate_key)
        return IngestionWorkflowResult(validation=validation, candidate=candidate)
