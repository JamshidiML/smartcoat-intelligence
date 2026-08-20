from fastapi import FastAPI

from smartcoat.api.routes import (
    decisions,
    events,
    health,
    knowledge,
    lab_capture_ai,
    lab_observation_ui,
    lab_observations,
    lab_project_capture_ui,
    lab_project_captures,
    lab_project_imports,
    qc_observations,
)
from smartcoat.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="SmartCoat Knowledge Capture MVP API",
)

app.include_router(health.router)
app.include_router(knowledge.router)
app.include_router(lab_observations.router)
app.include_router(qc_observations.router)
app.include_router(lab_observation_ui.router)
app.include_router(lab_project_captures.router)
app.include_router(lab_capture_ai.router)
app.include_router(lab_project_imports.router)
app.include_router(lab_project_capture_ui.router)
app.include_router(decisions.router)
app.include_router(events.router)
