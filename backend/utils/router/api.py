import logging
import os
from datetime import datetime

from ninja.openapi.docs import Redoc
from ninja_extra import NinjaExtraAPI

from utils.router.authenticate import AuthBear
from utils.router.exception import get_handlers


logger = logging.getLogger("django")


class BaseAPI(NinjaExtraAPI):
    def __init__(self, *args, **kwargs) -> None:
        kwargs.setdefault("title", os.getenv("PRODUCT_NAME", ""))
        kwargs.setdefault("version", os.getenv("VERSION_NAME", ""))
        kwargs.setdefault("openapi_url", "openapi.json")
        kwargs.setdefault("docs_url", "docs")
        kwargs.setdefault("docs", Redoc())
        kwargs.setdefault("auth", AuthBear())
        super().__init__(*args, **kwargs)
        self._exception_handlers = get_handlers(self)

    def create_response(self, request, data, *, status=None, temporal_response=None):
        return super().create_response(
            request,
            {  # Custom response always has status 200
                "data": data,
                "message_code": "SUCCESS",
                "message": "Success",
                "error_code": status if (status != 200) else 0,
                "current_time": datetime.now(),
            },
            status=200,
            temporal_response=temporal_response,
        )
