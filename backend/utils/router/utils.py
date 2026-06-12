import logging

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest
from ninja.constants import NOT_SET
from ninja.openapi.views import openapi_view
from ninja_extra import NinjaExtraAPI

from utils.router.authenticate import AuthBear
from utils.router.exception import generate_exception_response
from utils.router.paginate import PaginatedResponseSchema


logger = logging.getLogger("django")


def get_openapi_view(api: NinjaExtraAPI):
    @login_required
    def openapi_view_with_login_required(request: HttpRequest):
        return openapi_view(request, api)

    return openapi_view_with_login_required


def wrap_http_method(base_method):
    def wrapper(
        path: str, *, response=None, auth=False, exceptions=(), paginate=False, **kwargs
    ):
        if paginate:
            return base_method(
                path,
                auth=AuthBear() if auth else NOT_SET,
                response=generate_exception_response(
                    PaginatedResponseSchema[response], *exceptions
                ),
                **kwargs,
            )
        return base_method(
            path,
            auth=AuthBear() if auth else NOT_SET,
            response=generate_exception_response(response, *exceptions),
            **kwargs,
        )

    return wrapper
