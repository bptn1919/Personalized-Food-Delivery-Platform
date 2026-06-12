from datetime import datetime

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from utils.types import TUser


class EmailTemplate:
    def __init__(self):
        self._base_url = settings.FRONTEND_URL

    def _sent_email(self, user: TUser, template_name: str, data: dict, subject: str, to_email: str | None = None):
        body = render_to_string(template_name, data)

        alternative = EmailMultiAlternatives(subject=subject, to=[to_email or user.email])
        alternative.attach_alternative(body, "text/html")

        return alternative
    
    def send_verification_email(self, user: TUser, otp: str, purpose: str, to_email: str | None = None):
        if purpose == "SIGNUP":
            template_name = "email/signup_verification.html"
            subject = "Verify your account / Xác thực tài khoản"
        elif purpose == "RESET_PASSWORD":
            template_name = "email/reset_password.html"
            subject = "Forgot password / Quên mật khẩu"
        elif purpose == "EMAIL_CHANGE":
            template_name = "email/signup_verification.html"
            subject = "Verify your new email / Xác thực email mới"
        elif purpose == "BANK_VERIFY":
            template_name = "email/signup_verification.html"
            subject = "Verify your bank account / Xác thực tài khoản ngân hàng"
        elif purpose == "WITHDRAW_VERIFY":
            template_name = "email/signup_verification.html"
            subject = "Confirm withdrawal / Xác nhận rút tiền"
        else:
            raise ValueError("Invalid verification purpose")

        return self._sent_email(
            user=user,
            template_name=template_name,
            data={
                "user_name": user.get_full_name(),
                "otp": otp,
            },
            subject=subject,
            to_email=to_email,
        )

    def change_password(self, user: TUser):
        return self._sent_email(
            user=user,
            template_name="email/change_password.html",
            data={
                "user_name": user.get_full_name(),
                "formatted_time": datetime.now().strftime("%H:%M - %d/%m/%Y"),
            },
            subject="Change password / Thay đổi mật khẩu",
        )

    def send_withdraw_failed_email(
        self,
        user: TUser,
        amount: str,
        reference_id: str,
        reason: str,
    ):
        return self._sent_email(
            user=user,
            template_name="email/withdraw_failed.html",
            data={
                "user_name": user.get_full_name(),
                "amount": amount,
                "reference_id": reference_id,
                "reason": reason,
            },
            subject="Withdrawal failed / Rut tien that bai",
        )

    def send_full_lock_email(
        self,
        user: TUser,
        suspension_uid: str,
        reason: str,
        metrics: dict,
    ):
        appeal_url = f"{self._base_url}/chef/suspension/{suspension_uid}/appeal"
        return self._sent_email(
            user=user,
            template_name="email/full_lock_notification.html",
            data={
                "user_name": user.get_full_name(),
                "reason": reason,
                "metrics": metrics,
                "appeal_url": appeal_url,
            },
            subject="Tài khoản Chef bị tạm khóa / Chef account suspended",
        )

    def send_dish_lock_email(
        self,
        user: TUser,
        dish_name: str,
        suspension_uid: str,
        reason: str,
        metrics: dict,
    ):
        appeal_url = f"{self._base_url}/chef/suspension/{suspension_uid}/appeal"
        return self._sent_email(
            user=user,
            template_name="email/dish_lock_notification.html",
            data={
                "user_name": user.get_full_name(),
                "dish_name": dish_name,
                "reason": reason,
                "metrics": metrics,
                "appeal_url": appeal_url,
            },
            subject=f"Món ăn '{dish_name}' bị tạm khóa / Dish suspended",
        )

    def send_chef_warning_email(
        self,
        user: TUser,
        dish_name: str | None,
        reason: str,
    ):
        return self._sent_email(
            user=user,
            template_name="email/chef_warning.html",
            data={
                "user_name": user.get_full_name(),
                "dish_name": dish_name,
                "reason": reason,
            },
            subject="Cảnh báo chất lượng thực phẩm / Food quality warning",
        )

    def send_delivery_warning_email(
        self,
        user: TUser,
        reason: str,
        metrics: dict,
        is_admin_alert: bool = False,
    ):
        subject = (
            "Cảnh báo nghiêm trọng: Tỷ lệ giao hàng sai/thiếu cao / Delivery issue alert"
            if is_admin_alert
            else "Cảnh báo giao hàng / Delivery warning"
        )
        return self._sent_email(
            user=user,
            template_name="email/delivery_warning.html",
            data={
                "user_name": user.get_full_name(),
                "reason": reason,
                "metrics": metrics,
                "is_admin_alert": is_admin_alert,
            },
            subject=subject,
        )

    def send_financial_report_ack_email(
        self,
        user: TUser,
        report_uid: str,
        order_id,
    ):
        return self._sent_email(
            user=user,
            template_name="email/financial_report_ack.html",
            data={
                "user_name": user.get_full_name(),
                "report_uid": report_uid,
                "order_id": order_id,
            },
            subject="Phản ánh tài chính đã được ghi nhận / Financial report received",
        )

    def send_financial_admin_alert_email(
        self,
        admin_email: str,
        chef_email: str,
        report_uid: str,
        order_id,
        description: str,
    ):
        from django.core.mail import EmailMultiAlternatives
        from django.template.loader import render_to_string
        body = render_to_string(
            "email/financial_admin_alert.html",
            {
                "chef_email": chef_email,
                "report_uid": report_uid,
                "order_id": order_id,
                "description": description,
            },
        )
        msg = EmailMultiAlternatives(
            subject=f"[ADMIN] Báo cáo tài chính cần xem xét — order #{order_id}",
            to=[admin_email],
        )
        msg.attach_alternative(body, "text/html")
        return msg

    def send_suspension_lifted_email(
        self,
        user: TUser,
        suspension_uid: str,
        lift_note: str,
        suspension_type: str,
        dish_name: str | None,
    ):
        return self._sent_email(
            user=user,
            template_name="email/suspension_lifted.html",
            data={
                "user_name": user.get_full_name(),
                "suspension_type": suspension_type,
                "dish_name": dish_name,
                "lift_note": lift_note,
            },
            subject="Tài khoản đã được mở khóa / Account unlocked",
        )
