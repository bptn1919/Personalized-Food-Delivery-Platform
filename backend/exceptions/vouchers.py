from http import HTTPStatus
from utils.router.exception import APIException

class VoucherNotFoundException(APIException):
    error_code = HTTPStatus.NOT_FOUND
    message_code = "VOUCHER_NOT_FOUND"
    message = "Voucher không tồn tại"

class VoucherCodeAlreadyExistsException(APIException):
    """Mã voucher đã tồn tại"""
    error_code = HTTPStatus.BAD_REQUEST
    message_code = "VOUCHER_CODE_ALREADY_EXISTS"
    message = "Mã voucher đã tồn tại"


class VoucherInvalidException(APIException):
    """Voucher không hợp lệ"""
    error_code = HTTPStatus.BAD_REQUEST
    message_code = "VOUCHER_INVALID"
    message = "Voucher không hợp lệ"


class VoucherExpiredException(APIException):
    """Voucher đã hết hạn"""
    error_code = HTTPStatus.BAD_REQUEST
    message_code = "VOUCHER_EXPIRED"
    message = "Voucher đã hết hạn"


class VoucherMinOrderException(APIException):
    """Đơn hàng chưa đạt giá trị tối thiểu"""
    error_code = HTTPStatus.BAD_REQUEST
    message_code = "VOUCHER_MIN_ORDER"
    message = "Đơn hàng tối thiểu phải từ {min_amount:,.0f}đ"


class VoucherNotOwnedException(APIException):
    """Không có quyền thao tác voucher này"""
    error_code = HTTPStatus.FORBIDDEN
    message_code = "VOUCHER_NOT_OWNED"
    message = "Bạn không có quyền thao tác voucher này"


class VoucherChefMismatchException(APIException):
    """Voucher không thuộc chef của order"""
    error_code = HTTPStatus.BAD_REQUEST
    message_code = "VOUCHER_CHEF_MISMATCH"
    message = "Voucher này không áp dụng cho chef của đơn hàng"

class VoucherNotFoundException(APIException):
    error_code = HTTPStatus.NOT_FOUND
    message_code = "VOUCHER_NOT_FOUND"
    message = "Voucher không tồn tại"

class VoucherCodeAlreadyExistsException(APIException):
    """Mã voucher đã tồn tại"""
    error_code = HTTPStatus.BAD_REQUEST
    message_code = "VOUCHER_CODE_ALREADY_EXISTS"
    message = "Mã voucher đã tồn tại"


class VoucherInvalidException(APIException):
    """Voucher không hợp lệ"""
    error_code = HTTPStatus.BAD_REQUEST
    message_code = "VOUCHER_INVALID"
    message = "Voucher không hợp lệ"

class VoucherExpiredException(APIException):
    """Voucher đã hết hạn"""
    error_code = HTTPStatus.BAD_REQUEST
    message_code = "VOUCHER_EXPIRED"
    message = "Voucher đã hết hạn"


class VoucherUsageLimitException(APIException):
    """Voucher đã hết lượt sử dụng"""
    error_code = HTTPStatus.BAD_REQUEST
    message_code = "VOUCHER_USAGE_LIMIT"
    message = "Voucher đã hết lượt sử dụng"


class VoucherMinOrderException(APIException):
    """Đơn hàng chưa đạt giá trị tối thiểu"""
    error_code = HTTPStatus.BAD_REQUEST
    message_code = "VOUCHER_MIN_ORDER"
    message = "Đơn hàng tối thiểu phải từ {min_amount:,.0f}đ"


class VoucherNotOwnedException(APIException):
    """Không có quyền thao tác voucher này"""
    error_code = HTTPStatus.FORBIDDEN
    message_code = "VOUCHER_NOT_OWNED"
    message = "Bạn không có quyền thao tác voucher này"


class VoucherChefMismatchException(APIException):
    """Voucher không thuộc chef của order"""
    error_code = HTTPStatus.BAD_REQUEST
    message_code = "VOUCHER_CHEF_MISMATCH"
    message = "Voucher này không áp dụng cho chef của đơn hàng"