from http import HTTPStatus

from utils.router.exception import APIException


class VerificationSessionNotFound(APIException):
    error_code = HTTPStatus.NOT_FOUND
    message_code = "VERIFICATION_SESSION_NOT_FOUND"
    message = "Không tìm thấy phiên xác minh. Vui lòng bắt đầu lại."


class DocumentNotCompleted(APIException):
    error_code = HTTPStatus.BAD_REQUEST
    message_code = "DOCUMENT_NOT_COMPLETED"
    message = "File chưa được upload hoàn tất. Vui lòng gọi PUT /attachments/{uid}/completed trước."


class DocumentNotReadyToConfirm(APIException):
    error_code = HTTPStatus.BAD_REQUEST
    message_code = "DOCUMENT_NOT_READY_TO_CONFIRM"
    message = "Tài liệu chưa được phân tích thành công hoặc đã được xác nhận rồi."


class CrossValidationNotReady(APIException):
    error_code = HTTPStatus.BAD_REQUEST
    message_code = "CROSS_VALIDATION_NOT_READY"
    message = "Vui lòng hoàn tất và xác nhận cả 3 tài liệu trước khi kiểm tra chéo."


class SelfieCodeNotGenerated(APIException):
    error_code = HTTPStatus.BAD_REQUEST
    message_code = "SELFIE_CODE_NOT_GENERATED"
    message = "Chưa có mã xác thực. Vui lòng gọi GET /verification/selfie/code trước."


class SelfieCodeExpired(APIException):
    error_code = HTTPStatus.BAD_REQUEST
    message_code = "SELFIE_CODE_EXPIRED"
    message = "Mã xác thực đã hết hạn. Vui lòng yêu cầu mã mới."


class SelfieCodeMismatch(APIException):
    error_code = HTTPStatus.UNPROCESSABLE_ENTITY
    message_code = "SELFIE_CODE_MISMATCH"
    message = "Mã xác thực trong ảnh selfie không khớp. Vui lòng chụp lại."


class VerificationDocumentError(APIException):
    """Raised when Gemini Vision detects document-level errors (blurry, unreadable, etc.)."""
    error_code = HTTPStatus.UNPROCESSABLE_ENTITY
    message_code = "DOCUMENT_ANALYSIS_ERROR"
    message = "Không thể phân tích tài liệu."

    def __init__(self, errors: list[dict]):
        super().__init__(detail=errors)


class VerificationAlreadyCompleted(APIException):
    error_code = HTTPStatus.CONFLICT
    message_code = "VERIFICATION_ALREADY_COMPLETED"
    message = "Phiên xác minh đã hoàn tất. Không thể thực hiện lại."


class CrossValidationFailed(APIException):
    """Raised when cross-document information does not match."""
    error_code = HTTPStatus.UNPROCESSABLE_ENTITY
    message_code = "CROSS_VALIDATION_FAILED"
    message = "Thông tin giữa các giấy tờ không khớp nhau."

    def __init__(self, errors: list[dict]):
        super().__init__(detail=errors)
