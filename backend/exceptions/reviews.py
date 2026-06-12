from http import HTTPStatus

from utils.router.exception import APIException


class ReviewNotFoundException(APIException):
    status_code = HTTPStatus.NOT_FOUND
    message_code = "REVIEW_DOES_NOT_EXIST"
    message = "Review does not exist"


class DishNotOrderedException(APIException):
    status_code = HTTPStatus.BAD_REQUEST
    message_code = "DISH_NOT_ORDERED"
    message = "Dish was not ordered, cannot review"


class DuplicateReviewException(APIException):
    status_code = HTTPStatus.BAD_REQUEST
    message_code = "DUPLICATE_REVIEW"
    message = "You have already reviewed this dish in this order"


class OrderNotCompletedException(APIException):
    status_code = HTTPStatus.BAD_REQUEST
    message_code = "ORDER_NOT_COMPLETED"
    message = "Order is not completed, cannot review"


class InvalidRatingException(APIException):
    status_code = HTTPStatus.BAD_REQUEST
    message_code = "INVALID_RATING"
    message = "Rating must be an integer between 1 and 5"


class ReviewReplyNotFoundException(APIException):
    status_code = HTTPStatus.NOT_FOUND
    message_code = "REVIEW_REPLY_NOT_FOUND"
    message = "Review reply does not exist"


class ReviewReplyAlreadyExistsException(APIException):
    status_code = HTTPStatus.BAD_REQUEST
    message_code = "REVIEW_REPLY_ALREADY_EXISTS"
    message = "This review already has a reply"


class NotDishOwnerException(APIException):
    status_code = HTTPStatus.FORBIDDEN
    message_code = "NOT_DISH_OWNER"
    message = "Only the dish owner (chef) can reply to reviews"


class AIModelUnavailableException(APIException):
    status_code = HTTPStatus.SERVICE_UNAVAILABLE
    message_code = "AI_MODEL_UNAVAILABLE"
    message = "AI model service is unavailable"


class AIModelInvalidResponseException(APIException):
    status_code = HTTPStatus.BAD_GATEWAY
    message_code = "AI_MODEL_INVALID_RESPONSE"
    message = "AI model returned an invalid response"
