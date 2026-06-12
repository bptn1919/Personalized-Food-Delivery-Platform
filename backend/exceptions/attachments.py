from http import HTTPStatus

from utils.router.exception import APIException


class AttachmentNotFound(APIException):
    error_code = HTTPStatus.NOT_FOUND
    message_code = "ATTACHMENT_NOT_FOUND"
    message = "Attachment not found"


class AttachmentAlreadyCompleted(APIException):
    error_code = HTTPStatus.BAD_REQUEST
    message_code = "ATTACHMENT_ALREADY_COMPLETED"
    message = "Attachment already completed"

class AttachmentIsNotCompleted(APIException):
    error_code = HTTPStatus.BAD_REQUEST
    message_code = "ATTACHMENT_IS_NOT_COMPLETED"
    message = "Attachment upload chưa hoàn tất. Vui lòng gọi PUT /attachments/{uid}/completed trước."