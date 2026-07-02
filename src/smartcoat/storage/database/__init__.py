"""Database infrastructure for SmartCoat."""

from smartcoat.storage.database.base import Base
from smartcoat.storage.database.session import get_session, session_scope

__all__ = ["Base", "get_session", "session_scope"]
