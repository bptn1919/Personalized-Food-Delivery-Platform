from http import HTTPStatus

from utils.router.exception import APIException


class OrderNotFoundException(APIException):
    error_code = HTTPStatus.NOT_FOUND
    message_code = "ORDER_NOT_FOUND"
    message = "Order not found"
