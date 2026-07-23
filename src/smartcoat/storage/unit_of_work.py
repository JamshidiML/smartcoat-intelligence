from __future__ import annotations

from collections.abc import Callable, Sequence
from types import TracebackType
from typing import Protocol, Self

from sqlalchemy.orm import Session

from smartcoat.storage.repositories.knowledge_v2_repository import KnowledgeObjectV2Repository


class TransactionParticipant(Protocol):
    """Narrow same-session port; T07 remains responsible for audit semantics."""

    def flush(self, session: Session) -> None:
        """Stage and flush one participant's work or raise to abort the transaction."""


class UnitOfWorkStateError(RuntimeError):
    pass


class KnowledgeUnitOfWork:
    """Own exactly one session, one terminal commit, rollback, and close."""

    def __init__(
        self,
        session_factory: Callable[[], Session],
        *,
        participants: Sequence[TransactionParticipant] = (),
    ) -> None:
        self._session_factory = session_factory
        self._participants = tuple(participants)
        self._session: Session | None = None
        self._repository: KnowledgeObjectV2Repository | None = None
        self._finished = False
        self._closed = False

    def __enter__(self) -> Self:
        if self._session is not None or self._closed:
            raise UnitOfWorkStateError("the Unit of Work cannot be entered more than once")
        self._session = self._session_factory()
        self._repository = KnowledgeObjectV2Repository(self._session)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        try:
            if exc_type is not None and not self._finished:
                self.rollback()
            elif not self._finished:
                self.rollback()
        finally:
            self.close()

    @property
    def session(self) -> Session:
        self._require_active()
        assert self._session is not None
        return self._session

    @property
    def knowledge_objects(self) -> KnowledgeObjectV2Repository:
        self._require_active()
        assert self._repository is not None
        return self._repository

    def commit(self) -> None:
        self._require_active()
        assert self._session is not None
        try:
            self._session.flush()
            for participant in self._participants:
                participant.flush(self._session)
            self._session.flush()
            self._session.commit()
        except Exception:
            self._session.rollback()
            self._finished = True
            raise
        self._finished = True

    def rollback(self) -> None:
        self._require_active()
        assert self._session is not None
        self._session.rollback()
        self._finished = True

    def close(self) -> None:
        if self._closed:
            return
        if self._session is not None:
            if not self._finished:
                self._session.rollback()
                self._finished = True
            self._session.close()
        self._closed = True

    def _require_active(self) -> None:
        if self._closed:
            raise UnitOfWorkStateError("the Unit of Work is closed")
        if self._session is None:
            raise UnitOfWorkStateError("the Unit of Work must be entered before use")
        if self._finished:
            raise UnitOfWorkStateError("the Unit of Work transaction is already finished")
