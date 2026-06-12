from http import HTTPStatus

from utils.router.exception import APIException

class IngredientNameAlreadyExists(APIException):
    error_code = HTTPStatus.BAD_REQUEST
    message_code = "INGREDIENT_NAME_ALREADY_EXISTS"
    message = "Ingredient with the same name already exists"
    
class IngredientDoesNotExist(APIException):
    error_code = HTTPStatus.NOT_FOUND
    message_code = "INGREDIENT_NOT_FOUND"
    message = "Ingredient not found"


class IngredientIsReferenced(APIException):
    error_code = HTTPStatus.FORBIDDEN
    message_code = "INGREDIENT_IS_REFERENCED"
    message = "Ingredient is referenced"


class IngredientIsNotDeleted(APIException):
    error_code = HTTPStatus.BAD_REQUEST
    message_code = "INGREDIENT_NOT_DELETED"
    message = "Ingredient is not deleted"


class IngredientImportFileRequired(APIException):
    error_code = HTTPStatus.BAD_REQUEST
    message_code = "INGREDIENT_IMPORT_FILE_REQUIRED"
    message = "Excel file is required"


class IngredientImportFileInvalid(APIException):
    error_code = HTTPStatus.BAD_REQUEST
    message_code = "INGREDIENT_IMPORT_FILE_INVALID"
    message = "Invalid Excel file format"


class IngredientSuggestionNotFound(APIException):
    error_code = HTTPStatus.NOT_FOUND
    message_code = "INGREDIENT_SUGGESTION_NOT_FOUND"
    message = "Ingredient suggestion not found"

class IngredientIsNotPending(APIException):
    error_code = HTTPStatus.BAD_REQUEST
    message_code = "INGREDIENT_IS_NOT_PENDING"
    message = "Ingredient suggestion is not in PENDING status"

class IngredientAliasNotFound(APIException):
    error_code = HTTPStatus.NOT_FOUND
    message_code = "INGREDIENT_ALIAS_NOT_FOUND"
    message = "Ingredient alias not found"

class NutritionValidationException(APIException):
    status_code = 400
    default_code = "NUTRITION_INVALID"

    def __init__(self, message, field, severity=1.0):
        self.field = field
        self.severity = severity
        super().__init__(detail={
            "message": message,
            "field": field,
            "severity": severity,
        })