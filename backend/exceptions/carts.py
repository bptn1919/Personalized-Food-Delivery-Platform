from http import HTTPStatus

from utils.router.exception import APIException


class CartNotFoundException(APIException):
    error_code = HTTPStatus.NOT_FOUND
    message_code = "CART_NOT_FOUND"
    message = "Cart not found"
    
class CartItemNotFoundException(APIException):
    error_code = HTTPStatus.NOT_FOUND
    message_code = "CART_ITEM_NOT_FOUND"
    message = "Cart item not found"

class InvalidDeliveryDateException(APIException):
    error_code = HTTPStatus.BAD_REQUEST
    message_code = "INVALID_DELIVERY_DATE"
    message = "Không thể đặt món cho ngày trong quá khứ"