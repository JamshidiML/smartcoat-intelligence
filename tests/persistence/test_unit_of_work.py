from unittest.mock import Mock

import pytest
from sqlalchemy.orm import Session

from smartcoat.storage.unit_of_work import (
    KnowledgeUnitOfWork,
    UnitOfWorkStateError,
)


class RecordingParticipant:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.sessions: list[Session] = []

    def flush(self, session: Session) -> None:
        self.sessions.append(session)
        if self.fail:
            raise RuntimeError("synthetic participant failure")


def _session() -> Mock:
    return Mock(spec=Session)


def test_unit_of_work_owns_one_commit_and_shared_session() -> None:
    session = _session()
    participant = RecordingParticipant()

    with KnowledgeUnitOfWork(lambda: session, participants=(participant,)) as unit:
        assert unit.session is session
        assert unit.knowledge_objects is unit.knowledge_objects
        unit.commit()

    assert participant.sessions == [session]
    assert session.flush.call_count == 2
    session.commit.assert_called_once_with()
    session.rollback.assert_not_called()
    session.close.assert_called_once_with()


def test_participant_failure_rolls_back_complete_transaction() -> None:
    session = _session()
    participant = RecordingParticipant(fail=True)

    with KnowledgeUnitOfWork(lambda: session, participants=(participant,)) as unit:
        with pytest.raises(RuntimeError, match="synthetic participant failure"):
            unit.commit()
        with pytest.raises(UnitOfWorkStateError, match="already finished"):
            unit.commit()

    session.commit.assert_not_called()
    session.rollback.assert_called_once_with()
    session.close.assert_called_once_with()


def test_uncommitted_context_rolls_back_and_use_after_close_is_rejected() -> None:
    session = _session()
    unit = KnowledgeUnitOfWork(lambda: session)

    with unit:
        assert unit.session is session

    session.rollback.assert_called_once_with()
    session.commit.assert_not_called()
    with pytest.raises(UnitOfWorkStateError, match="closed"):
        _ = unit.session


def test_unit_of_work_must_be_entered_and_cannot_be_reentered() -> None:
    session = _session()
    unit = KnowledgeUnitOfWork(lambda: session)

    with pytest.raises(UnitOfWorkStateError, match="entered"):
        unit.commit()
    with unit:
        with pytest.raises(UnitOfWorkStateError, match="more than once"):
            unit.__enter__()
