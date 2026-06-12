"""
PayOS Payment Provider
Documentation: https://payos.vn/docs/
"""
import hashlib
import hmac
import json
import os
import requests  # type: ignore
from typing import Dict, Optional
from datetime import datetime
from urllib.parse import quote
from urllib.parse import urlencode
from payos import PayOS  # type: ignore
from payos.types import PayoutRequest  # type: ignore
class PayOSPaymentProvider:
    """Provider for PayOS payment gateway integration"""
    
    def __init__(self):
        self.client_id = os.getenv("PAYOS_CLIENT_ID")
        self.api_key = os.getenv("PAYOS_API_KEY")
        self.checksum_key = os.getenv("PAYOS_CHECKSUM_KEY")
        self.payout_client_id = os.getenv("PAYOS_PAYOUT_CLIENT_ID") or self.client_id
        self.payout_api_key = os.getenv("PAYOS_PAYOUT_API_KEY") or self.api_key
        self.payout_checksum_key = os.getenv("PAYOS_PAYOUT_CHECKSUM_KEY") or self.checksum_key
        self.api_url = os.getenv("PAYOS_API_URL", "https://api-merchant.payos.vn")
        self.return_url = os.getenv("PAYOS_RETURN_URL")
        self.cancel_url = os.getenv("PAYOS_CANCEL_URL")
        
        # Initialize PayOS SDK for payout operations (handles signatures automatically)
        self.payos_sdk = PayOS(
            client_id=self.payout_client_id,
            api_key=self.payout_api_key,
            checksum_key=self.payout_checksum_key
        )
        
        if not all([self.client_id, self.api_key, self.checksum_key]):
            raise ValueError("Missing PayOS configuration. Check environment variables.")

    def _resolve_credentials(self, use_payout_credentials: bool = False) -> tuple[str, str, str]:
        if use_payout_credentials:
            client_id = self.payout_client_id
            api_key = self.payout_api_key
            checksum_key = self.payout_checksum_key
            scope = "payout"
        else:
            client_id = self.client_id
            api_key = self.api_key
            checksum_key = self.checksum_key
            scope = "payment"

        if not all([client_id, api_key, checksum_key]):
            raise ValueError(f"Missing PayOS {scope} configuration. Check environment variables.")

        return client_id, api_key, checksum_key
    
    def create_payment(
        self,
        order_code: int,
        amount: int,
        description: str,
        buyer_name: Optional[str] = None,
        buyer_email: Optional[str] = None,
        buyer_phone: Optional[str] = None,
        buyer_address: Optional[str] = None,
        buyer_company_name: Optional[str] = None,
        buyer_tax_code: Optional[str] = None,
        items: Optional[list] = None,
        invoice: Optional[dict] = None,
        expired_at: Optional[int] = None
    ) -> Dict:
        """
        Create PayOS payment link - Đúng 100% theo docs PayOS
        
        Args:
            order_code: Mã đơn hàng (unique integer) - REQUIRED
            amount: Số tiền (VNĐ) - integer - REQUIRED
            description: Mô tả thanh toán - REQUIRED
            buyer_name: Tên người mua (optional)
            buyer_email: Email người mua (optional)
            buyer_phone: Số điện thoại (optional)
            buyer_address: Địa chỉ người mua (optional)
            buyer_company_name: Tên công ty (optional)
            buyer_tax_code: Mã số thuế (optional)
            items: Danh sách sản phẩm (optional) - List[Dict]
                   [{"name": "...", "quantity": 1, "price": 100, "unit": "...", "taxPercentage": 0}]
            invoice: Thông tin hóa đơn (optional) - Dict
                     {"buyerNotGetInvoice": true, "taxPercentage": 0}
            expired_at: Thời gian hết hạn - Unix timestamp (optional)
            
        Returns:
            Dict with checkoutUrl, qrCode, and payment info
        """
        # ✅ 1. Tạo payload đúng docs PayOS
        # Các trường REQUIRED
        payment_data = {
            "orderCode": order_code,
            "amount": amount,
            "description": description,
            "cancelUrl": self.cancel_url,
            "returnUrl": self.return_url
        }
        
        # ✅ 2. Thêm các trường OPTIONAL (chỉ thêm nếu có giá trị)
        if buyer_name:
            payment_data["buyerName"] = buyer_name
        if buyer_email:
            payment_data["buyerEmail"] = buyer_email
        if buyer_phone:
            payment_data["buyerPhone"] = buyer_phone
        if buyer_address:
            payment_data["buyerAddress"] = buyer_address
        if buyer_company_name:
            payment_data["buyerCompanyName"] = buyer_company_name
        if buyer_tax_code:
            payment_data["buyerTaxCode"] = buyer_tax_code
        if items:
            payment_data["items"] = items
        if invoice:
            payment_data["invoice"] = invoice
        if expired_at:
            payment_data["expiredAt"] = expired_at
        
        # ✅ 3. Tạo signature theo format: amount=$amount&cancelUrl=$cancelUrl&description=$description&orderCode=$orderCode&returnUrl=$returnUrl
        client_id, api_key, checksum_key = self._resolve_credentials()
        signature = self._create_signature(payment_data, checksum_key)
        payment_data["signature"] = signature
        
        # ✅ 4. Gọi API PayOS với headers chuẩn
        headers = {
            "x-client-id": client_id,
            "x-api-key": api_key,
            "Content-Type": "application/json"
        }
        
        try:
            # ✅ 5. POST request đến endpoint PayOS
            response = requests.post(
                f"{self.api_url}/v2/payment-requests",
                headers=headers,
                json=payment_data,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            # ✅ 6. Parse response theo docs PayOS
            if result.get("code") == "00":
                # Response thành công
                return {
                    "success": True,
                    "checkout_url": result["data"]["checkoutUrl"],
                    "qr_code": result["data"]["qrCode"],
                    "payment_link_id": result["data"]["paymentLinkId"],
                    "order_code": result["data"]["orderCode"],
                    "amount": result["data"]["amount"],
                    "account_number": result["data"].get("accountNumber"),
                    "account_name": result["data"].get("accountName"),
                    "bin": result["data"].get("bin"),
                    "currency": result["data"].get("currency", "VND"),
                    "status": result["data"]["status"],
                    "description": result["data"].get("description")
                }
            else:
                # Response lỗi
                return {
                    "success": False,
                    "error": result.get("desc", "Unknown error"),
                    "code": result.get("code")
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to create payment"
            }
    
    def get_payment_info(self, order_code: int) -> Dict:
        """
        Get payment link information
        
        Args:
            order_code: Mã đơn hàng hoặc payment link ID
            
        Returns:
            Dict with payment information
        """
        headers = {
            "x-client-id": self.client_id,
            "x-api-key": self.api_key
        }
        
        try:
            response = requests.get(
                f"{self.api_url}/v2/payment-requests/{order_code}",
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get("code") == "00":
                data = result["data"]
                return {
                    "success": True,
                    "payment_link_id": data.get("id"),
                    "order_code": data["orderCode"],
                    "amount": data["amount"],
                    "amount_paid": data.get("amountPaid", 0),
                    "amount_remaining": data.get("amountRemaining", 0),
                    "status": data["status"],
                    "created_at": data.get("createdAt"),
                    "transactions": data.get("transactions", [])
                }
            else:
                return {
                    "success": False,
                    "error": result.get("desc", "Unknown error")
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def cancel_payment(self, order_code: int, reason: Optional[str] = None) -> Dict:
        """
        Cancel payment link
        
        Args:
            order_code: Mã đơn hàng
            reason: Lý do hủy (optional)
            
        Returns:
            Dict with cancellation result
        """
        headers = {
            "x-client-id": self.client_id,
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        body = {}
        if reason:
            body["cancellationReason"] = reason
        
        try:
            response = requests.post(
                f"{self.api_url}/v2/payment-requests/{order_code}/cancel",
                headers=headers,
                json=body,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get("code") == "00":
                return {
                    "success": True,
                    "status": result["data"]["status"],
                    "cancelled_at": result["data"].get("canceledAt")
                }
            else:
                return {
                    "success": False,
                    "error": result.get("desc", "Unknown error")
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def verify_webhook_data(self, webhook_data: Dict) -> Dict:
        """
        Verify PayOS webhook data with signature
        
        Args:
            webhook_data: Dict containing webhook data with signature
            
        Returns:
            Dict with verification result
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            received_signature = webhook_data.get("signature", "")
            data = webhook_data.get("data", {})
            
            if not data:
                logger.error(f"Missing 'data' field in webhook: {webhook_data}")
                return {
                    "is_valid": False,
                    "is_success": False,
                    "code": "99",
                    "desc": "Missing data field",
                    "order_code": None,
                    "amount": None,
                    "payment_link_id": None
                }
            
            # Create signature from data
            calculated_signature = self._create_signature(data)
            
            logger.info(f"Received signature: {received_signature[:20]}...")
            logger.info(f"Calculated signature: {calculated_signature[:20]}...")
            
            # Verify signature
            is_valid = calculated_signature.lower() == received_signature.lower()
            
            # Check success status
            is_success = (
                webhook_data.get("code") == "00" and
                webhook_data.get("success") == True and
                data.get("code") == "00"
            )
            
            logger.info(f"Signature valid: {is_valid}, Payment success: {is_success}")
            
            return {
                "is_valid": is_valid,
                "is_success": is_success,
                "code": webhook_data.get("code", ""),
                "desc": webhook_data.get("desc", ""),
                "order_code": data.get("orderCode"),
                "amount": data.get("amount"),
                "description": data.get("description"),
                "account_number": data.get("accountNumber"),
                "reference": data.get("reference"),
                "transaction_datetime": data.get("transactionDateTime"),
                "payment_link_id": data.get("paymentLinkId"),
                "currency": data.get("currency", "VND")
            }
        except Exception as e:
            logger.error(f"Error in verify_webhook_data: {str(e)}", exc_info=True)
            return {
                "is_valid": False,
                "is_success": False,
                "code": "99",
                "desc": f"Verification error: {str(e)}",
                "order_code": None,
                "amount": None,
                "payment_link_id": None
            }
    
    def _create_signature(self, data: Dict, checksum_key: Optional[str] = None) -> str:
        """
        Create HMAC SHA256 signature for PayOS

        PayOS signature format (theo DOCS chính thức):
        - Chỉ include 5 trường: amount, cancelUrl, description, orderCode, returnUrl
        - Sort keys alphabetically
        - Format: amount=$amount&cancelUrl=$cancelUrl&description=$description&orderCode=$orderCode&returnUrl=$returnUrl
        - Use HMAC SHA256 with checksum key
        """
        # ✅ For payment creation, ONLY include these 5 fields (theo docs PayOS)
        if "orderCode" in data and "cancelUrl" in data:
            # Payment creation signature - CHỈ 5 trường này
            signature_data = {
                "amount": data.get("amount"),
                "cancelUrl": data.get("cancelUrl"),
                "description": data.get("description"),
                "orderCode": data.get("orderCode"),
                "returnUrl": data.get("returnUrl")
            }
        else:
            # Webhook verification signature - use all data
            signature_data = data.copy()
        
        # ✅ Sort keys alphabetically (BẮT BUỘC)
        sorted_keys = sorted(signature_data.keys())
        
        # ✅ Create query string: key1=value1&key2=value2
        parts = []
        for key in sorted_keys:
            value = signature_data[key]
            
            # Handle None values
            if value is None or value == "null" or value == "undefined":
                value = ""
            
            # Convert to string
            parts.append(f"{key}={value}")
        
        data_string = "&".join(parts)
        
        # ✅ Create HMAC SHA256 signature with checksum key
        signature_key = checksum_key or self.checksum_key
        # signature_key = self.payout_checksum_key  
        signature = hmac.new(
            signature_key.encode('utf-8'),
            data_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature

    # def _create_payout_signature(self, data: Dict, checksum_key: Optional[str] = None) -> str:
    #     """
    #     Create HMAC SHA256 signature for payout requests following PayOS docs.

    #     Exact order required by PayOS: amount,description,referenceId,toBin,toAccountNumber
    #     """
    #     keys = ["amount", "description", "referenceId", "toBin", "toAccountNumber"]
    #     parts: list[str] = []
    #     for key in keys:
    #         value = data.get(key)
    #         if value is None or value == "null" or value == "undefined":
    #             value = ""
    #         parts.append(f"{key}={value}")

    #     data_string = "&".join(parts)
    #     signature_key = checksum_key or self.payout_checksum_key or self.checksum_key
    #     signature = hmac.new(
    #         signature_key.encode('utf-8'),
    #         data_string.encode('utf-8'),
    #         hashlib.sha256
    #     ).hexdigest()
    #     return signature


    def get_payment_invoices(self, order_code: int) -> Dict:
        """
        Get payment link invoices
        
        Args:
            order_code: Mã đơn hàng hoặc payment link ID
            
        Returns:
            Dict with invoices information
        """
        headers = {
            "x-client-id": self.client_id,
            "x-api-key": self.api_key
        }
        
        try:
            response = requests.get(
                f"{self.api_url}/v2/payment-requests/{order_code}/invoices",
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get("code") == "00":
                return {
                    "success": True,
                    "invoices": result["data"].get("invoices", [])
                }
            else:
                return {
                    "success": False,
                    "error": result.get("desc", "Unknown error")
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def download_invoice(self, order_code: int, invoice_id: str) -> Dict:
        """
        Download payment invoice
        
        Args:
            order_code: Mã đơn hàng hoặc payment link ID
            invoice_id: Mã hóa đơn
            
        Returns:
            Dict with download URL or PDF content
        """
        headers = {
            "x-client-id": self.client_id,
            "x-api-key": self.api_key
        }
        
        try:
            response = requests.get(
                f"{self.api_url}/v2/payment-requests/{order_code}/invoices/{invoice_id}/download",
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            
            # Return PDF content
            return {
                "success": True,
                "content": response.content,
                "content_type": response.headers.get("Content-Type", "application/pdf")
            }
                
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def confirm_webhook_url(self, webhook_url: str) -> Dict:
        """
        Confirm and update webhook URL for payment channel
        
        Args:
            webhook_url: URL nhận webhook từ PayOS
            
        Returns:
            Dict with confirmation result
        """
        headers = {
            "x-client-id": self.client_id,
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        body = {
            "webhookUrl": webhook_url
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/confirm-webhook",
                headers=headers,
                json=body,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get("code") == "00":
                data = result["data"]
                return {
                    "success": True,
                    "webhook_url": data.get("webhookUrl"),
                    "account_number": data.get("accountNumber"),
                    "account_name": data.get("accountName"),
                    "name": data.get("name"),
                    "short_name": data.get("shortName")
                }
            else:
                return {
                    "success": False,
                    "error": result.get("desc", "Unknown error"),
                    "code": result.get("code")
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_status_message(self, status: str) -> str:
        """Get Vietnamese message for payment status"""
        messages = {
            "PENDING": "Đang chờ thanh toán",
            "PROCESSING": "Đang xử lý",
            "PAID": "Đã thanh toán",
            "CANCELLED": "Đã hủy",
            "EXPIRED": "Đã hết hạn"
        }
        return messages.get(status, "Không xác định")
    
    def create_payout(
        self,
        reference_id: str,
        amount: int,
        description: str,
        to_bin: str,
        to_account_number: str,
        idempotency_key: str,
        category: Optional[list] = None
    ) -> Dict:
        """
        Create single payout using official PayOS SDK.
        Docs: https://payos.vn/docs/api/#tag/payout/operation/create-single-payout
        
        Args:
            reference_id: Mã tham chiếu của lệnh chi (unique)
            amount: Số tiền chi (VNĐ) - integer
            description: Mô tả thanh toán
            to_bin: Mã ngân hàng đích (ví dụ: "970415" cho VietinBank)
            to_account_number: Số tài khoản đích
            idempotency_key: Khóa đảm bảo tính duy nhất của request (SDK handles)
            category: Danh mục thanh toán (internal; NOT sent to PayOS)
            
        Returns:
            Dict with payout result
        """
        try:
            # Ensure description length meets PayOS limit (max 25 characters)
            if description and len(description) > 25:
                description = description[:25]

            # Create payout request using PayOS SDK type with snake_case fields
            payout_request = PayoutRequest(
                reference_id=reference_id,
                amount=amount,
                description=description,
                to_bin=to_bin,
                to_account_number=to_account_number,
                category=category
            )
            
            # SDK handles signature creation automatically via payos_sdk.payouts.create()
            # Returns a Payout object on success, raises PayOSError on failure
            result = self.payos_sdk.payouts.create(payout_request, idempotency_key=idempotency_key)
            
            # Parse SDK response - result is a Payout object
            raw_transactions = result.transactions if hasattr(result, 'transactions') else []
            serializable_transactions = []
            for tx in (raw_transactions or []):
                if isinstance(tx, dict):
                    serializable_transactions.append(tx)
                elif hasattr(tx, '__dict__'):
                    serializable_transactions.append({
                        k: v for k, v in vars(tx).items()
                        if not k.startswith('_')
                    })
                else:
                    serializable_transactions.append(str(tx))

            created_at = result.created_at if hasattr(result, 'created_at') else None
            if hasattr(created_at, 'isoformat'):
                created_at = created_at.isoformat()

            return {
                "success": True,
                "payout_id": result.id,
                "reference_id": result.reference_id,
                "transactions": serializable_transactions,
                "approval_state": result.approval_state if hasattr(result, 'approval_state') else None,
                "created_at": created_at,
                "message": "Payout created successfully"
            }
                
        except Exception as e:
            # SDK raises PayOSError and subclasses on failure
            error_msg = str(e)
            status_code = None
            
            # Extract status code if available
            if hasattr(e, 'status_code'):
                status_code = e.status_code
            
            return {
                "success": False,
                "error": error_msg,
                "status_code": status_code,
                "message": "Failed to create payout"
            }
    
    def get_payout_info(self, payout_id: str) -> Dict:
        """
        Get payout information (Lấy thông tin lệnh chi)
        
        Args:
            payout_id: ID của lệnh chi
            
        Returns:
            Dict with payout information
        """
        client_id, api_key, _ = self._resolve_credentials(use_payout_credentials=True)
        headers = {
            "x-client-id": client_id,
            "x-api-key": api_key
        }
        
        try:
            response = requests.get(
                f"{self.api_url}/v1/payouts/{payout_id}",
                headers=headers,
                timeout=30
            )
            try:
                result = response.json()
            except ValueError:
                result = {"raw": response.text}

            if response.status_code >= 400:
                return {
                    "success": False,
                    "error": result.get("desc") or result.get("message") or response.text,
                    "code": result.get("code"),
                    "status_code": response.status_code,
                    "details": result,
                }
            
            if result.get("code") == "00":
                return {
                    "success": True,
                    "data": result["data"]
                }
            else:
                return {
                    "success": False,
                    "error": result.get("desc", "Unknown error"),
                    "code": result.get("code"),
                    "status_code": response.status_code,
                    "details": result,
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e)
            }
