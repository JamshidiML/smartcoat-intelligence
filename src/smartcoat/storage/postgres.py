from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from smartcoat.core.config import get_settings


def get_engine() -> Engine:
    """Create a SQLAlchemy engine from settings."""

    settings = get_settings()
    return create_engine(settings.database_url, pool_pre_ping=True)
