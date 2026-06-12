from http import HTTPStatus

from utils.router.exception import APIException


class DishNotFoundException(APIException):
    error_code = HTTPStatus.NOT_FOUND
    message_code = "DISH_NOT_FOUND"
    message = "Dish not found"

class DishNotFoundInOrderException(APIException):
    error_code = HTTPStatus.NOT_FOUND
    message_code = "DISH_NOT_FOUND_IN_ORDER"
    message = "Dish not found in order"

class DishIsReferenced(APIException):
    error_code = HTTPStatus.FORBIDDEN
    message_code = "DISH_IS_REFERENCED"
    message = "Dish is referenced"


class DishIngredientAlreadyExists(APIException):
    error_code = HTTPStatus.BAD_REQUEST
    message_code = "DISH_INGREDIENT_ALREADY_EXISTS"
    message = "Ingredient already exists in dish"

class DishIngredientNotFoundException(APIException):
    error_code = HTTPStatus.NOT_FOUND
    message_code = "DISH_INGREDIENT_NOT_FOUND"
    message = "Dish ingredient not found"

class DishIsNotDeleted(APIException):
    error_code = HTTPStatus.BAD_REQUEST
    message_code = "DISH_NOT_DELETED"


class DishPermissionDenied(APIException):
    error_code = HTTPStatus.FORBIDDEN
    message_code = "DISH_PERMISSION_DENIED"
    message = "You can only modify your own dishes"
    message = "Dish is not deleted"

class DishLocationNotFoundException(APIException):
    error_code = HTTPStatus.NOT_FOUND
    message_code = "DISH_LOCATION_NOT_FOUND"
    message = "Dish location not found"


class DishLocationHasChildrenException(APIException):
    error_code = HTTPStatus.BAD_REQUEST
    message_code = "DISH_LOCATION_HAS_CHILDREN"
    message = "Cannot delete location that still has children"

class DishIngredientSuggestionAlreadyExists(APIException):
    error_code = HTTPStatus.BAD_REQUEST
    message_code = "DISH_INGREDIENT_SUGGESTION_ALREADY_EXISTS"
    message = "You have already suggested an ingredient with the same name for this dish"