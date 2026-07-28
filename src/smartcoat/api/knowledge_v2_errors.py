"""Correlation handling and safe deterministic errors for the v2 API."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, PlainTextResponse, Response
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

CORRELATION_HEADER = "X-Correlation-ID"
V2_PATH_PREFIX = "/api/v2/knowledge"


@dataclass(frozen=True)
class PublicError:
    status_code: int
    code: str
    message: str


class KnowledgeV2APIError(RuntimeError):
    """Explicit route-level failure that still uses the shared error envelope."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


_ERRORS: dict[str, PublicError] = {
    "knowledge_object_not_found": PublicError(
        404,
        "knowledge_object_not_found",
        "Knowledge Object not found at the supplied organization boundary.",
    ),
    "knowledge_history_not_found": PublicError(
        404,
        "knowledge_history_not_found",
        "Knowledge Object history not found at the supplied organization boundary.",
    ),
    "stale_revision": PublicError(
        409,
        "stale_revision",
        "The expected revision is no longer current.",
    ),
    "knowledge_object_target_mismatch": PublicError(
        409,
        "knowledge_object_target_mismatch",
        "The requested operation conflicts with the current object.",
    ),
    "knowledge_update_lifecycle_forbidden": PublicError(
        409,
        "knowledge_update_lifecycle_forbidden",
        "Knowledge Object updates are permitted only while lifecycle is draft.",
    ),
    "invalid_lifecycle_transition": PublicError(
        409,
        "invalid_lifecycle_transition",
        "The lifecycle action is not valid from the current state.",
    ),
    "lifecycle_role_mismatch": PublicError(
        409,
        "lifecycle_role_mismatch",
        "The declared role does not satisfy the lifecycle action contract.",
    ),
    "knowledge_capture_incomplete": PublicError(
        409,
        "knowledge_capture_incomplete",
        "The draft does not satisfy the capture preconditions.",
    ),
    "lifecycle_plan_source_mismatch": PublicError(
        409,
        "lifecycle_plan_source_mismatch",
        "The lifecycle source state changed before persistence.",
    ),
    "draft_delete_ineligible": PublicError(
        409,
        "draft_delete_ineligible",
        "The draft is not eligible for hard deletion.",
    ),
    "trusted_record_hard_delete_forbidden": PublicError(
        409,
        "trusted_record_hard_delete_forbidden",
        "The current lifecycle does not permit hard deletion.",
    ),
    "inbound_reference_blocks_deletion": PublicError(
        409,
        "inbound_reference_blocks_deletion",
        "A governed inbound reference blocks deletion.",
    ),
    "replacement_evidence_required": PublicError(
        409,
        "replacement_evidence_required",
        "Changed evidence identities require complete structured evidence.",
    ),
    "aggregate_read_retry_exhausted": PublicError(
        409,
        "aggregate_read_retry_exhausted",
        "The Knowledge Object changed during the bounded read.",
    ),
    "knowledge_query_cursor_malformed": PublicError(
        400,
        "knowledge_query_cursor_malformed",
        "The cursor is malformed.",
    ),
    "knowledge_query_cursor_signature_invalid": PublicError(
        400,
        "knowledge_query_cursor_signature_invalid",
        "The cursor signature is invalid.",
    ),
    "knowledge_query_cursor_version_unsupported": PublicError(
        400,
        "knowledge_query_cursor_version_unsupported",
        "The cursor version is unsupported.",
    ),
    "knowledge_query_cursor_query_mismatch": PublicError(
        400,
        "knowledge_query_cursor_query_mismatch",
        "The cursor does not match the current query boundary.",
    ),
    "knowledge_query_cursor_position_invalid": PublicError(
        400,
        "knowledge_query_cursor_position_invalid",
        "The cursor position is invalid.",
    ),
    "knowledge_cursor_signing_key_unavailable": PublicError(
        500,
        "server_configuration_error",
        "The service is not configured for this operation.",
    ),
    "organization_id_invalid": PublicError(
        400,
        "organization_id_invalid",
        "X-SmartCoat-Organization-ID must not be blank.",
    ),
    "context_filter_incomplete": PublicError(
        400,
        "context_filter_incomplete",
        "Context filters require type, ID kind, and reference ID.",
    ),
}

_CONFLICT_CODES = frozenset(
    {
        "evidence_exact_duplicate",
        "evidence_id_conflict",
        "evidence_identity_mismatch",
        "evidence_objects_extra",
        "evidence_objects_missing",
        "evidence_order_mismatch",
        "knowledge_v2_relationship_exact_duplicate",
        "knowledge_v2_relationship_revision_conflict",
    }
)


def _is_v2(request: Request) -> bool:
    return request.url.path.startswith(V2_PATH_PREFIX)


def correlation_text(request: Request) -> str:
    value = getattr(request.state, "correlation_id_text", None)
    if isinstance(value, str):
        return value
    generated = str(uuid4())
    request.state.correlation_id = UUID(generated)
    request.state.correlation_id_text = generated
    return generated


def correlation_uuid(request: Request) -> UUID:
    correlation_text(request)
    return request.state.correlation_id


def error_response(request: Request, error: PublicError) -> JSONResponse:
    correlation_id = correlation_text(request)
    return JSONResponse(
        status_code=error.status_code,
        content={
            "error": {
                "code": error.code,
                "message": error.message,
                "correlation_id": correlation_id,
            }
        },
        headers={CORRELATION_HEADER: correlation_id},
    )


def _public_error_for_code(code: str) -> PublicError | None:
    if code in _ERRORS:
        return _ERRORS[code]
    if code in _CONFLICT_CODES:
        return PublicError(
            409,
            code,
            "The requested operation conflicts with the current Knowledge Object.",
        )
    return None


def _exception_code(error: Exception) -> str | None:
    value = getattr(error, "code", None)
    return value if isinstance(value, str) else None


async def _validation_handler(
    request: Request,
    error: Exception,
) -> Response:
    if not _is_v2(request):
        if isinstance(error, RequestValidationError):
            return await request_validation_exception_handler(request, error)
        return PlainTextResponse("Internal Server Error", status_code=500)
    return error_response(
        request,
        PublicError(
            422,
            "request_validation_error",
            "Request validation failed.",
        ),
    )


async def _http_handler(request: Request, error: Exception) -> Response:
    if not isinstance(error, HTTPException):
        return PlainTextResponse("Internal Server Error", status_code=500)
    if not _is_v2(request):
        return await http_exception_handler(request, error)
    if error.status_code == 404:
        return error_response(request, _ERRORS["knowledge_object_not_found"])
    return error_response(
        request,
        PublicError(error.status_code, "http_error", "The request could not be completed."),
    )


async def _known_handler(request: Request, error: Exception) -> Response:
    if not _is_v2(request):
        return PlainTextResponse("Internal Server Error", status_code=500)
    code = _exception_code(error)
    public_error = _public_error_for_code(code) if code is not None else None
    if public_error is None:
        public_error = PublicError(
            500,
            "internal_server_error",
            "An unexpected server error occurred.",
        )
    return error_response(request, public_error)


async def _database_handler(request: Request, error: Exception) -> Response:
    if not isinstance(error, SQLAlchemyError):
        return PlainTextResponse("Internal Server Error", status_code=500)
    if not _is_v2(request):
        return PlainTextResponse("Internal Server Error", status_code=500)
    return error_response(
        request,
        PublicError(
            500,
            "database_operation_failed",
            "The database operation could not be completed.",
        ),
    )


def install_knowledge_v2_error_handling(app: FastAPI) -> None:
    """Install one correlation value and safe v2 exception handlers."""

    @app.middleware("http")
    async def correlation_middleware(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        supplied = request.headers.get(CORRELATION_HEADER)
        if supplied is None:
            correlation_id = uuid4()
            correlation_id_text = str(correlation_id)
        else:
            correlation_id_text = supplied
            try:
                correlation_id = UUID(supplied)
            except (AttributeError, ValueError):
                generated = str(uuid4())
                request.state.correlation_id = UUID(generated)
                request.state.correlation_id_text = generated
                return error_response(
                    request,
                    PublicError(
                        400,
                        "correlation_id_invalid",
                        "X-Correlation-ID must be a valid UUID.",
                    ),
                )
        request.state.correlation_id = correlation_id
        request.state.correlation_id_text = correlation_id_text
        response = await call_next(request)
        response.headers[CORRELATION_HEADER] = correlation_id_text
        return response

    app.add_exception_handler(RequestValidationError, _validation_handler)
    app.add_exception_handler(ValidationError, _validation_handler)
    app.add_exception_handler(HTTPException, _http_handler)
    app.add_exception_handler(KnowledgeV2APIError, _known_handler)
    app.add_exception_handler(SQLAlchemyError, _database_handler)
    app.add_exception_handler(Exception, _known_handler)


def api_error_responses() -> dict[int | str, dict[str, Any]]:
    """Build declarations only when the versioned router is loaded."""

    from smartcoat.api.knowledge_v2_schemas import SmartCoatAPIErrorResponse

    return {
        status: {
            "model": SmartCoatAPIErrorResponse,
            "description": description,
        }
        for status, description in (
            (400, "Malformed request context, cursor, or semantic request."),
            (404, "Knowledge Object not found at the organization boundary."),
            (409, "Revision, lifecycle, deletion, or current-state conflict."),
            (422, "Safe request validation failure."),
            (500, "Sanitized server or configuration failure."),
        )
    }
