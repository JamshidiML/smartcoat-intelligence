from fastapi import FastAPI

from smartcoat.api.routes import decisions, health, knowledge
from smartcoat.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="SmartCoat Knowledge Capture MVP API",
)

app.include_router(health.router)
app.include_router(knowledge.router)
app.include_router(decisions.router)
