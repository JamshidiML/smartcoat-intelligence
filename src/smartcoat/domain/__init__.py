"""Domain models for SmartCoat canonical enterprise objects."""

from importlib import import_module
from typing import TYPE_CHECKING, Any

from smartcoat.domain.context_references import (
    ContextIdKind,
    ContextReference,
    ContextType,
    KnowledgeContext,
)
from smartcoat.domain.decision_objects import DecisionObject
from smartcoat.domain.events import EnterpriseEvent
from smartcoat.domain.knowledge_objects import KnowledgeObject

if TYPE_CHECKING:
    from smartcoat.domain.knowledge_objects_v2 import (
        ConfidentialityLevel,
        DecisionObjectRelationship,
        KnowledgeObjectRelationship,
        KnowledgeObjectUpdateError,
        KnowledgeObjectV2CoreRecord,
        KnowledgeObjectV2CreateCommand,
        KnowledgeObjectV2MutableState,
        KnowledgeObjectV2PersistedStateSnapshot,
        KnowledgeObjectV2UpdateCommand,
        LegacyCompatibilityBlocker,
        LegacyKnowledgeObjectCompatibilityAssessment,
        OwnerReference,
        UncertaintyDeclaration,
        UncertaintyKind,
        UpdateDisposition,
        assess_legacy_knowledge_object,
        evaluate_knowledge_object_update,
    )

_V2_EXPORTS = {
    "ConfidentialityLevel",
    "DecisionObjectRelationship",
    "KnowledgeObjectRelationship",
    "KnowledgeObjectUpdateError",
    "KnowledgeObjectV2CoreRecord",
    "KnowledgeObjectV2CreateCommand",
    "KnowledgeObjectV2MutableState",
    "KnowledgeObjectV2PersistedStateSnapshot",
    "KnowledgeObjectV2UpdateCommand",
    "LegacyCompatibilityBlocker",
    "LegacyKnowledgeObjectCompatibilityAssessment",
    "OwnerReference",
    "UncertaintyDeclaration",
    "UncertaintyKind",
    "UpdateDisposition",
    "assess_legacy_knowledge_object",
    "evaluate_knowledge_object_update",
}

__all__ = [
    "ContextIdKind",
    "ContextReference",
    "ContextType",
    "DecisionObject",
    "EnterpriseEvent",
    "KnowledgeContext",
    "KnowledgeObject",
    "ConfidentialityLevel",
    "DecisionObjectRelationship",
    "KnowledgeObjectRelationship",
    "KnowledgeObjectUpdateError",
    "KnowledgeObjectV2CoreRecord",
    "KnowledgeObjectV2CreateCommand",
    "KnowledgeObjectV2MutableState",
    "KnowledgeObjectV2PersistedStateSnapshot",
    "KnowledgeObjectV2UpdateCommand",
    "LegacyCompatibilityBlocker",
    "LegacyKnowledgeObjectCompatibilityAssessment",
    "OwnerReference",
    "UncertaintyDeclaration",
    "UncertaintyKind",
    "UpdateDisposition",
    "assess_legacy_knowledge_object",
    "evaluate_knowledge_object_update",
]


def __getattr__(name: str) -> Any:
    """Load v2 exports only when requested so Release 1.7 API imports stay isolated."""

    if name not in _V2_EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module("smartcoat.domain.knowledge_objects_v2")
    value = getattr(module, name)
    globals()[name] = value
    return value
