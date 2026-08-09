from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

STATIC_PAGE = Path(__file__).resolve().parents[1] / "static" / "lab_project_capture.html"

router = APIRouter(tags=["lab-project-capture-ui"])


@router.get("/lab-project-capture", include_in_schema=False)
def lab_project_capture_page() -> FileResponse:
    if not STATIC_PAGE.is_file():
        raise HTTPException(500, "Lab project capture page is unavailable")
    return FileResponse(
        path=STATIC_PAGE,
        media_type="text/html; charset=utf-8",
        headers={"Cache-Control": "no-store"},
    )
