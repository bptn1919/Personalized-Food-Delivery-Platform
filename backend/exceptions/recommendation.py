from http import HTTPStatus

from utils.router.exception import APIException


class PreferencesNotFoundException(APIException):
    status_code = HTTPStatus.NOT_FOUND
    message_code = "PREFERENCES_DOES_NOT_EXIST"
    message = "Preferences do not exist"


class DailyNutritionProfileNotFoundException(APIException):
    status_code = HTTPStatus.NOT_FOUND
    message_code = "DAILY_NUTRITION_PROFILE_NOT_FOUND"
    message = "Daily nutrition profile not found"
