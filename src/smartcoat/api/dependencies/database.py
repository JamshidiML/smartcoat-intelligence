from collections.abc import Generator

from sqlalchemy.orm import Session

from smartcoat.storage.database.session import get_session


def get_db_session() -> Generator[Session, None, None]:
    """Provide a database session to API routes."""

    yield from get_session()
