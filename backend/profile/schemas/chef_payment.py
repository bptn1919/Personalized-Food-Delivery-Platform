from ninja import Schema
from typing import Optional
import re
from pydantic import field_validator
from utils.enums import VietnamBankEnum


class ChefPaymentInfoRequest(Schema):
    """Request schema for creating/updating chef payment info"""
    bank_name: VietnamBankEnum
    bank_code: str
    bank_account_number: str
    bank_account_name: str
    bank_branch: Optional[str] = None
    citizen_id: Optional[str] = None
    tax_code: Optional[str] = None

    @field_validator('bank_code')
    def validate_bank_code(cls, v):
        """BIN/bank code: 6-8 digits"""
        v = v.strip().replace(' ', '')
        if not re.match(r'^\d{6,8}$', v):
            raise ValueError("Bank code must be 6-8 digits")
        return v
    
    @field_validator('bank_account_number')
    def validate_account_number(cls, v):
        """Số tài khoản: 6-19 chữ số, không có ký tự đặc biệt"""
        # Remove spaces if any
        v = v.replace(' ', '').replace('-', '')
        
        # Check if only digits, 6-19 characters
        if not re.match(r'^\d{6,19}$', v):
            raise ValueError("Account number must be 6-19 digits only (no letters or special characters)")
        
        return v
    
    @field_validator('bank_account_name')
    def validate_account_name(cls, v):
        """Tên chủ tài khoản: CHỮ HOA KHÔNG DẤU, phải khớp với tên trên CCCD"""
        # Must be uppercase without accents
        if not re.match(r'^[A-Z\s]+$', v):
            raise ValueError("Account name must be UPPERCASE letters without accents (A-Z and spaces only). Example: NGUYEN VAN A")
        
        # No leading/trailing spaces
        v = v.strip()
        
        # No multiple consecutive spaces
        v = re.sub(r'\s+', ' ', v)
        
        if len(v) < 2:
            raise ValueError("Account name too short")
        
        return v
    
    @field_validator('citizen_id')
    def validate_citizen_id(cls, v):
        """CCCD/CMND: 9-12 chữ số"""
        if v and not re.match(r'^\d{9,12}$', v):
            raise ValueError("Citizen ID must be 9-12 digits")
        return v
    
    @field_validator('tax_code')
    def validate_tax_code(cls, v):
        """Mã số thuế: 10-13 chữ số"""
        if v and not re.match(r'^\d{10,13}$', v):
            raise ValueError("Tax code must be 10-13 digits")
        return v


class ChefPaymentInfoResponse(Schema):
    """Response schema for chef payment info"""
    bank_name: str
    bank_code: str
    bank_account_number: str  # Will be masked
    bank_account_name: str
    bank_branch: Optional[str] = None
    is_verified: bool
    verified_at: Optional[str] = None
    created_at: str
    updated_at: str
