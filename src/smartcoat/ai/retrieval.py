from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievalResult:
    source_id: str
    title: str
    content: str
    score: float | None = None


class RetrievalService:
    """Placeholder retrieval service for future semantic search and RAG."""

    def search(self, query: str) -> list[RetrievalResult]:
        if not query.strip():
            return []
        return [
            RetrievalResult(
                source_id="placeholder",
                title="Retrieval placeholder",
                content="Semantic retrieval will be implemented in a later release.",
                score=0.0,
            )
        ]
