import ast
import inspect
from unittest.mock import Mock
from uuid import uuid4

from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session

from smartcoat.storage.repositories.knowledge_v2_repository import (
    KnowledgeObjectV2Repository,
)


def test_repository_source_has_no_commit_call() -> None:
    tree = ast.parse(inspect.getsource(KnowledgeObjectV2Repository))
    commit_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "commit"
    ]

    assert commit_calls == []


def test_cross_organization_lookup_uses_both_identity_predicates() -> None:
    session = Mock(spec=Session)
    session.scalar.return_value = None
    repository = KnowledgeObjectV2Repository(session)

    result = repository.get(
        object_id=uuid4(),
        organization_id="synthetic-org-a",
    )

    assert result is None
    statement = session.scalar.call_args.args[0]
    compiled = str(statement.compile(dialect=postgresql.dialect()))
    assert "knowledge_objects_v2.object_id" in compiled
    assert "knowledge_objects_v2.organization_id" in compiled


def test_mutation_surfaces_do_not_accept_generic_governance_fields() -> None:
    material_parameters = inspect.signature(
        KnowledgeObjectV2Repository.stage_material_update
    ).parameters
    lifecycle_parameters = inspect.signature(
        KnowledgeObjectV2Repository.stage_lifecycle_transition
    ).parameters

    assert "lifecycle_state" not in material_parameters
    assert "revision" not in material_parameters
    assert "plan" in lifecycle_parameters
    assert "lifecycle_state" not in lifecycle_parameters
