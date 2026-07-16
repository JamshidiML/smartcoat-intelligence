from collections.abc import Iterable

from pydantic import ValidationError

from smartcoat.ingestion.models import (
    IngestionCandidate,
    IngestionStatus,
    ManifestValidationIssue,
    ManifestValidationResult,
    PermittedUse,
    SourceManifest,
)


class ManifestRegistry:
    """In-memory manifest duplicate registry for deterministic dry runs."""

    def __init__(self, known_duplicate_keys: Iterable[str] | None = None) -> None:
        self._known_duplicate_keys = set(known_duplicate_keys or [])

    def validate(self, manifest: SourceManifest | dict) -> ManifestValidationResult:
        result = validate_manifest(
            manifest,
            known_duplicate_keys=self._known_duplicate_keys,
        )
        if result.accepted and result.duplicate_key:
            self._known_duplicate_keys.add(result.duplicate_key)
        return result


def validate_manifest(
    manifest: SourceManifest | dict,
    known_duplicate_keys: Iterable[str] | None = None,
) -> ManifestValidationResult:
    """Validate a metadata-only manifest without extracting raw source content."""

    try:
        parsed = (
            manifest
            if isinstance(manifest, SourceManifest)
            else SourceManifest.model_validate(manifest)
        )
    except ValidationError as error:
        return ManifestValidationResult(
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

    duplicate_key = parsed.duplicate_key
    if duplicate_key in set(known_duplicate_keys or []):
        return ManifestValidationResult(
            manifest_id=parsed.manifest_id,
            status=IngestionStatus.DUPLICATE,
            warnings=[
                ManifestValidationIssue(
                    code="duplicate_manifest",
                    message=(
                        "A manifest with the same checksum or fingerprint "
                        "was already registered."
                    ),
                    field="checksum_sha256",
                )
            ],
            duplicate_key=duplicate_key,
        )

    warnings: list[ManifestValidationIssue] = []
    if parsed.dry_run is False:
        warnings.append(
            ManifestValidationIssue(
                code="dry_run_disabled",
                message=(
                    "Prototype supports metadata validation only; raw ingestion "
                    "remains out of scope."
                ),
                field="dry_run",
            )
        )
    if PermittedUse.MODEL_TRAINING in parsed.permitted_uses:
        warnings.append(
            ManifestValidationIssue(
                code="model_training_requires_approval",
                message=(
                    "Model-training use requires explicit governance approval "
                    "before ingestion."
                ),
                field="permitted_uses",
            )
        )

    status = IngestionStatus.VALIDATED if not warnings else IngestionStatus.BLOCKED
    return ManifestValidationResult(
        manifest_id=parsed.manifest_id,
        status=status,
        warnings=warnings,
        duplicate_key=duplicate_key,
    )


def create_candidate(manifest: SourceManifest) -> IngestionCandidate:
    """Create a deterministic dry-run candidate from a validated manifest."""

    return IngestionCandidate(
        manifest_id=manifest.manifest_id,
        ingestion_job_id=manifest.ingestion_job_id,
        source_type=manifest.source_type,
        source_format=manifest.source_format,
        source_reference=manifest.source_reference,
        organization_id=manifest.organization_id,
        site_id=manifest.site_id,
        confidentiality_level=manifest.confidentiality_level,
        permitted_uses=manifest.permitted_uses,
        schema_target=manifest.schema_target,
        duplicate_key=manifest.duplicate_key,
        dry_run=manifest.dry_run,
    )
