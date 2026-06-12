import logging

from ninja_extra import (
    ControllerBase,
    api_controller,
    http_delete,
    http_get,
    http_post,
    http_put,
    http_patch,
)

from utils.router.utils import wrap_http_method


class Controller(ControllerBase):
    logger = logging.getLogger("django")


post = wrap_http_method(http_post)
get = wrap_http_method(http_get)
put = wrap_http_method(http_put)
delete = wrap_http_method(http_delete)
patch = wrap_http_method(http_patch) 
api = api_controller

__all__ = ["Controller", "post", "get", "put", "delete", "patch", "api"]
