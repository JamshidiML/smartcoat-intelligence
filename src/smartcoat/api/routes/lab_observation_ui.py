from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

STATIC_PAGE = Path(__file__).resolve().parents[1] / "static" / "lab_observations.html"

router = APIRouter(tags=["lab-observation-ui"])


@router.get("/lab-observations", include_in_schema=False)
def lab_observation_page() -> FileResponse:
    if not STATIC_PAGE.is_file():
        raise HTTPException(500, "Lab observation page is unavailable")
    return FileResponse(
        path=STATIC_PAGE,
        media_type="text/html; charset=utf-8",
        headers={"Cache-Control": "no-store"},
    )
