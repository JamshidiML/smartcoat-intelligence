"""Raw evidence upload and dry-run XLSX import routes for the local pilot."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request

from smartcoat.core.config import get_settings
from smartcoat.services.lab_project_excel_import import (
    ExcelImportError,
    LabProjectExcelImporter,
    WorkbookImportReport,
)
from smartcoat.services.local_evidence_registry import (
    EvidenceRegistryError,
    LocalEvidenceDescriptor,
    LocalEvidenceRegistry,
)

XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def get_local_evidence_registry() -> LocalEvidenceRegistry:
    settings = get_settings()
    return LocalEvidenceRegistry(
        asset_root=settings.asset_root,
        max_upload_bytes=settings.max_upload_bytes,
    )


def get_lab_project_excel_importer() -> LabProjectExcelImporter:
    return LabProjectExcelImporter()


def _registry_error(error: EvidenceRegistryError) -> HTTPException:
    if error.code == "asset_too_large":
        return HTTPException(status_code=413, detail=str(error))
    if error.code in {"unsupported_media_type", "media_signature_mismatch"}:
        return HTTPException(status_code=415, detail=str(error))
    if error.code in {
        "empty_asset",
        "invalid_filename",
        "invalid_organization_id",
        "invalid_sha256",
    }:
        return HTTPException(status_code=422, detail=str(error))
    if error.code == "asset_not_found":
        return HTTPException(status_code=404, detail=str(error))
    return HTTPException(status_code=500, detail="Evidence asset could not be stored")


router = APIRouter(prefix="/api/v2/lab-capture", tags=["lab-project-imports"])


@router.post("/assets", status_code=201, response_model=LocalEvidenceDescriptor)
async def register_lab_capture_asset(
    request: Request,
    content_type: Annotated[
        str,
        Header(alias="Content-Type", min_length=1, max_length=256),
    ],
    original_filename: Annotated[
        str,
        Header(alias="X-SmartCoat-Filename", min_length=1, max_length=512),
    ],
    organization_id: Annotated[
        str,
        Header(alias="X-SmartCoat-Organization-ID", min_length=1, max_length=128),
    ],
    registry: Annotated[LocalEvidenceRegistry, Depends(get_local_evidence_registry)],
) -> LocalEvidenceDescriptor:
    try:
        return await registry.register_async(
            request.stream(),
            organization_id=organization_id,
            original_filename=original_filename,
            media_type=content_type,
        )
    except EvidenceRegistryError as error:
        raise _registry_error(error) from error


@router.post("/import-excel", status_code=200, response_model=WorkbookImportReport)
async def import_lab_project_excel(
    request: Request,
    content_type: Annotated[
        str,
        Header(alias="Content-Type", min_length=1, max_length=256),
    ],
    original_filename: Annotated[
        str,
        Header(alias="X-SmartCoat-Filename", min_length=1, max_length=512),
    ],
    organization_id: Annotated[
        str,
        Header(alias="X-SmartCoat-Organization-ID", min_length=1, max_length=128),
    ],
    registry: Annotated[LocalEvidenceRegistry, Depends(get_local_evidence_registry)],
    importer: Annotated[LabProjectExcelImporter, Depends(get_lab_project_excel_importer)],
) -> WorkbookImportReport:
    if content_type.partition(";")[0].strip().casefold() != XLSX_MEDIA_TYPE:
        raise HTTPException(status_code=415, detail="Excel import requires XLSX content")
    try:
        evidence = await registry.register_async(
            request.stream(),
            organization_id=organization_id,
            original_filename=original_filename,
            media_type=content_type,
        )
        with registry.open_content(
            organization_id=organization_id,
            sha256=evidence.sha256,
        ) as stream:
            return importer.import_workbook(
                stream,
                organization_id=organization_id,
                evidence=evidence,
            )
    except EvidenceRegistryError as error:
        if error.code == "media_signature_mismatch":
            raise HTTPException(
                status_code=422,
                detail="Workbook is not a valid XLSX file",
            ) from error
        raise _registry_error(error) from error
    except ExcelImportError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


__all__ = [
    "get_lab_project_excel_importer",
    "get_local_evidence_registry",
    "router",
]
