"""Bounded read-only composition service for Knowledge Object v2 detail."""

from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from sqlalchemy.orm import Session

from smartcoat.domain.evidence_provenance import KnowledgeObjectV2EvidenceComposition
from smartcoat.storage.repositories.knowledge_v2_repository import (
    KnowledgeObjectV2Repository,
)


class KnowledgeObjectV2ReadService:
    """Read one canonical composition without mutation or Unit of Work."""

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def get(
        self,
        *,
        object_id: UUID,
        organization_id: str,
    ) -> KnowledgeObjectV2EvidenceComposition | None:
        with self._session_factory() as session:
            return KnowledgeObjectV2Repository(session).get(
                object_id=object_id,
                organization_id=organization_id,
            )
