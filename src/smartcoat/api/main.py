from fastapi import FastAPI

from smartcoat.api.routes import (
    decisions,
    events,
    health,
    knowledge,
    lab_observation_ui,
    lab_observations,
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
app.include_router(decisions.router)
app.include_router(events.router)
