import logging
from collections import defaultdict
from datetime import datetime
from functools import partial
from http import HTTPStatus
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Literal,
    Optional,
    Type,
    TypeVar,
    Union,
    cast,
)

from django.db import DatabaseError
from django.http import HttpRequest, JsonResponse
from ninja import NinjaAPI, Schema
from ninja.errors import AuthenticationError, HttpError, ValidationError
from pydantic import BaseModel
import traceback

logger = logging.getLogger("django")


_E = TypeVar("_E", bound=Exception)
TExc = Union[_E, Type[_E]]
TExcHandler = Callable[[_E], JsonResponse]
TDetail = Union[Dict[str, List[str]], str]


def create_response(
    message: str,
    message_code: str,
    error_code: int = 500,
    detail: Optional[TDetail] = None,
):
    return {
        "data": detail,
        "message_code": message_code,
        "message": message,
        "error_code": error_code,
        "current_time": datetime.now(),
    }


class APIException(Exception):
    error_code: HTTPStatus = HTTPStatus.INTERNAL_SERVER_ERROR
    message_code = "INTERNAL_SERVER_ERROR"
    message = "Internal server error"

    def __init__(self, detail: Any = []) -> None:
        self.detail = detail

    def __str__(self) -> str:
        return f"{self.message_code}: {self.message}"

    def __repr__(self) -> str:
        return f"{self.message_code}: {self.message}"


def logger_wrapper(
    func: TExcHandler[_E],
) -> Callable[[HttpRequest, _E, NinjaAPI], JsonResponse]:
    def wrapper(request: HttpRequest, exc: _E, api: NinjaAPI):
        if isinstance(exc, APIException):
            logger.error(exc)
        else:
            logger.error(exc)
        traceback.print_exc()
        
        response_data = func(exc)
        status_code = response_data.get("error_code", 500)
        
        # Ensure status_code is a valid HTTP status (int)
        if hasattr(status_code, 'value'):
            status_code = status_code.value
            
        return JsonResponse(response_data, status=status_code)

    return wrapper


@logger_wrapper
def _default_exception_handler(exc: Exception):
    return create_response(
        message="Contact admin for support",
        message_code="CONTACT_ADMIN_FOR_SUPPORT",
        error_code=500,
    )


@logger_wrapper
def _authentication_error_handler(exc: AuthenticationError):
    return create_response(
        message="Unauthorized", message_code="UNAUTHORIZED", error_code=401
    )


@logger_wrapper
def _validation_error_handler(exc: ValidationError):
    detail: Dict[str, List[str]] = defaultdict(list)
    for error in exc.errors:
        if "loc" in error and "msg" in error and len(error["loc"]) > 0:
            field: str = error["loc"][-1]
            detail[field].append(error["msg"])

    return create_response(
        message="Validation error",
        message_code="VALIDATION_ERROR",
        error_code=401,
        detail=detail,
    )


@logger_wrapper
def _default_http_error(exc: HttpError):
    return create_response(
        message="Http error",
        message_code="HTTP_ERROR",
        error_code=exc.status_code,
        detail=str(exc),
    )


@logger_wrapper
def _custom_exception_handler(exc: APIException):
    return create_response(
        message=exc.message,
        message_code=exc.message_code,
        error_code=exc.error_code,
        detail=exc.detail,
    )


def get_handlers(api: NinjaAPI):
    return {
        ValidationError: partial(_validation_error_handler, api=api),
        AuthenticationError: partial(_authentication_error_handler, api=api),
        HttpError: partial(_default_http_error, api=api),
        DatabaseError: partial(_default_exception_handler, api=api),
        APIException: partial(_custom_exception_handler, api=api),
        Exception: partial(_default_exception_handler, api=api),
    }


T = TypeVar("T", bound=APIException)
TSchema = TypeVar("TSchema", bound=Union[Schema, BaseModel])


def generate_exception_response(
    response: Type[TSchema], *exceptions: Type[T]
) -> Dict[HTTPStatus, Any]:
    grouped: Dict[HTTPStatus, List[Type[TSchema]]] = {}

    for exc in exceptions:
        if not all(
            hasattr(exc, attr) for attr in ("message", "message_code", "error_code")
        ):
            continue

        schema = type(
            exc.__name__ + "Schema",
            (Schema,),
            {
                "__annotations__": {
                    "message": Literal[exc.message],
                    "message_code": Literal[exc.message_code],
                },
            },
        )

        schema_typed = cast(Type[TSchema], schema)
        grouped.setdefault(HTTPStatus(exc.error_code), []).append(schema_typed)

    # Convert lists of schemas to Unions
    return {
        HTTPStatus.OK: response,
        **{
            code: Union[tuple(schemas)] if len(schemas) > 1 else schemas[0]
            for code, schemas in grouped.items()
        },
    }


__all__ = ["get_handlers", "APIException", "generate_exception_response"]
