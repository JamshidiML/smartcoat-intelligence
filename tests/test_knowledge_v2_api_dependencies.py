from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest
from pydantic import SecretStr

from smartcoat.api.dependencies.knowledge_v2 import (
    _cursor_key_bytes,
    get_knowledge_query_service,
    get_organization_id,
)
from smartcoat.api.knowledge_v2_errors import KnowledgeV2APIError
from smartcoat.api.main import create_app
from smartcoat.core.config import Settings
from smartcoat.services.knowledge_v2_read_service import KnowledgeObjectV2ReadService

SYNTHETIC_KEY = "synthetic-t09-cursor-key-at-least-32-bytes"


class GuardSession:
    def __init__(self) -> None:
        self.entered = False
        self.exited = False

    def __enter__(self) -> GuardSession:
        self.entered = True
        return self

    def __exit__(self, *_args: object) -> None:
        self.exited = True

    def commit(self) -> None:
        raise AssertionError("read service must not commit")

    def flush(self) -> None:
        raise AssertionError("read service must not flush")

    def add(self, _value: object) -> None:
        raise AssertionError("read service must not add")

    def delete(self, _value: object) -> None:
        raise AssertionError("read service must not delete")


class CountingSessionFactory:
    def __init__(self) -> None:
        self.calls = 0
        self.sessions: list[GuardSession] = []

    def __call__(self) -> GuardSession:
        self.calls += 1
        session = GuardSession()
        self.sessions.append(session)
        return session


class StubReadRepository:
    calls: list[dict[str, Any]] = []

    def __init__(self, session: object) -> None:
        self.session = session

    def get(self, **kwargs: Any) -> None:
        self.calls.append(kwargs)
        return None


def _settings(key: str | None) -> Settings:
    return Settings(
        _env_file=None,
        knowledge_cursor_signing_key=(SecretStr(key) if key is not None else None),
    )


def test_cursor_key_is_secret_has_no_default_and_requires_32_encoded_bytes() -> None:
    missing = _settings(None)
    short = _settings("short")
    valid = _settings(SYNTHETIC_KEY)

    assert missing.knowledge_cursor_signing_key is None
    assert SYNTHETIC_KEY not in repr(valid)
    with pytest.raises(KnowledgeV2APIError) as missing_error:
        _cursor_key_bytes(missing.knowledge_cursor_signing_key)
    with pytest.raises(KnowledgeV2APIError) as short_error:
        _cursor_key_bytes(short.knowledge_cursor_signing_key)
    assert missing_error.value.code == "knowledge_cursor_signing_key_unavailable"
    assert short_error.value.code == "knowledge_cursor_signing_key_unavailable"
    assert _cursor_key_bytes(valid.knowledge_cursor_signing_key) == SYNTHETIC_KEY.encode()


@pytest.mark.parametrize("key", [None, "too-short"])
def test_missing_or_short_cursor_key_fails_before_session_creation(
    key: str | None,
) -> None:
    sessions = CountingSessionFactory()

    with pytest.raises(KnowledgeV2APIError) as error:
        get_knowledge_query_service(
            sessions,  # type: ignore[arg-type]
            _settings(key),
        )

    assert error.value.code == "knowledge_cursor_signing_key_unavailable"
    assert sessions.calls == 0


def test_valid_cursor_key_builds_service_without_opening_session() -> None:
    sessions = CountingSessionFactory()

    service = get_knowledge_query_service(
        sessions,  # type: ignore[arg-type]
        _settings(SYNTHETIC_KEY),
    )

    assert service is not None
    assert sessions.calls == 0


def test_organization_header_is_trimmed_bounded_metadata() -> None:
    assert get_organization_id(" synthetic-org ") == "synthetic-org"

    with pytest.raises(KnowledgeV2APIError) as error:
        get_organization_id("   ")
    assert error.value.code == "organization_id_invalid"


def test_read_service_opens_one_read_session_and_only_calls_get(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sessions = CountingSessionFactory()
    StubReadRepository.calls = []
    monkeypatch.setattr(
        "smartcoat.services.knowledge_v2_read_service.KnowledgeObjectV2Repository",
        StubReadRepository,
    )
    service = KnowledgeObjectV2ReadService(
        sessions,  # type: ignore[arg-type]
    )
    object_id = uuid4()

    result = service.get(
        object_id=object_id,
        organization_id="synthetic-org",
    )

    assert result is None
    assert sessions.calls == 1
    assert sessions.sessions[0].entered is True
    assert sessions.sessions[0].exited is True
    assert StubReadRepository.calls == [
        {
            "object_id": object_id,
            "organization_id": "synthetic-org",
        }
    ]


def test_application_factory_openapi_opens_no_session_or_cursor_dependency(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden_session_factory() -> object:
        raise AssertionError("OpenAPI must not open a database session")

    monkeypatch.setattr(
        "smartcoat.api.dependencies.knowledge_v2.get_knowledge_v2_session_factory",
        forbidden_session_factory,
    )
    application = create_app()

    schema = application.openapi()

    assert "/api/v2/knowledge" in schema["paths"]
    assert "/knowledge" in schema["paths"]
