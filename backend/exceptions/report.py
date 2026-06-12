from http import HTTPStatus
from utils.router.exception import APIException


class ReportAlreadyExists(APIException):
    error_code = HTTPStatus.CONFLICT
    message_code = "REPORT_ALREADY_EXISTS"
    message = "Bạn đã gửi phản ánh cho đơn hàng này rồi."


class ReportOrderNotCompleted(APIException):
    error_code = HTTPStatus.BAD_REQUEST
    message_code = "REPORT_ORDER_NOT_COMPLETED"
    message = "Chỉ có thể phản ánh sau khi đơn hàng hoàn thành."


class ReportOrderNotOwned(APIException):
    error_code = HTTPStatus.FORBIDDEN
    message_code = "REPORT_ORDER_NOT_OWNED"
    message = "Bạn không phải chủ đơn hàng này."


class ReportRateLimitExceeded(APIException):
    error_code = HTTPStatus.TOO_MANY_REQUESTS
    message_code = "REPORT_RATE_LIMIT"
    message = "Bạn đã gửi quá nhiều phản ánh trong 24 giờ. Vui lòng thử lại sau."


class ReportTargetRequired(APIException):
    error_code = HTTPStatus.BAD_REQUEST
    message_code = "REPORT_TARGET_REQUIRED"
    message = "Phản ánh này cần order_uid hoặc chef_id/dish_uid hợp lệ."


class ReportTargetNotFound(APIException):
    error_code = HTTPStatus.NOT_FOUND
    message_code = "REPORT_TARGET_NOT_FOUND"
    message = "Không tìm thấy chef hoặc món ăn hợp lệ để phản ánh."


class ReportEvidenceRequired(APIException):
    error_code = HTTPStatus.BAD_REQUEST
    message_code = "REPORT_EVIDENCE_REQUIRED"
    message = "Phản ánh loại này yêu cầu ảnh bằng chứng."


class SuspensionNotFound(APIException):
    error_code = HTTPStatus.NOT_FOUND
    message_code = "SUSPENSION_NOT_FOUND"
    message = "Không tìm thấy lệnh khóa."


class AppealAlreadySubmitted(APIException):
    error_code = HTTPStatus.CONFLICT
    message_code = "APPEAL_ALREADY_SUBMITTED"
    message = "Bạn đã gửi giải trình cho lệnh khóa này rồi."


class AppealNotAllowed(APIException):
    error_code = HTTPStatus.BAD_REQUEST
    message_code = "APPEAL_NOT_ALLOWED"
    message = "Lệnh khóa này không ở trạng thái cho phép giải trình."


class ReportNotFound(APIException):
    error_code = HTTPStatus.NOT_FOUND
    message_code = "REPORT_NOT_FOUND"
    message = "Không tìm thấy phản ánh."
