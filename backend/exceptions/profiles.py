from http import HTTPStatus

from utils.router.exception import APIException


class ProfileDoesNotExist(APIException):
    error_code = HTTPStatus.NOT_FOUND
    message_code = "PROFILE_DOES_NOT_EXIST"
    message = "Profile does not exist"

class CustomerAddressNotFoundException(APIException):
    error_code = HTTPStatus.NOT_FOUND
    message_code = "CUSTOMER_ADDRESS_NOT_FOUND"
    message = "Customer address not found"  
    
class FavouriteDishDoesNotExist(APIException):
    error_code = HTTPStatus.NOT_FOUND
    message_code = "FAVORITE_DISH_NOT_FOUND"
    message = "Favorite dish not found"
    