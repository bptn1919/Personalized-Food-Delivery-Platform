from http import HTTPStatus

from utils.router.exception import APIException


class CertificateNotFoundException(APIException):
    error_code = HTTPStatus.NOT_FOUND
    message_code = "CERTIFICATE_NOT_FOUND"
    message = "Certificate not found"