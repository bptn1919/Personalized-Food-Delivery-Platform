from typing import List

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.mail.backends.smtp import EmailBackend

from ..base import BaseService


class EmailClient(BaseService):
    def __init__(
        self,
        port_number=int(settings.EMAIL_PORT),
        timeout=float(settings.EMAIL_TIMEOUT),
        use_tls=bool(settings.EMAIL_USE_TLS),
        username=settings.EMAIL_HOST_USER,
        password=settings.EMAIL_HOST_PASSWORD,
        host=settings.EMAIL_HOST,
    ):
        self._sender = EmailBackend(
            host=host,
            username=username,
            password=password,
            port=port_number,
            use_tls=use_tls,
            timeout=timeout,
        )

    def send(self, messages: List[EmailMultiAlternatives]):
        try:
            self.logger.info("Sending email")
            self._sender.send_messages(messages)
            self.logger.info("Email sent successfully")
        except Exception as e:
            self.logger.error(e)
