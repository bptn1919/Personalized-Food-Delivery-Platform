from enum import Enum,unique

from django.db.models import TextChoices


@unique
class UserTypeEnum(TextChoices):
    """Enum cho loại user (group)"""
    CUSTOMER = "CUSTOMER", "Customer"
    CHEF = "CHEF", "Chef"
    ADMIN = "ADMIN", "Admin"

@unique
class OtpPurposeEnum(TextChoices):
    SIGNUP = "SIGNUP", "Sign Up"
    RESET_PASSWORD = "RESET_PASSWORD", "Reset Password"
    EMAIL_CHANGE = "EMAIL_CHANGE", "Email Change"
    BANK_VERIFY = "BANK_VERIFY", "Bank Account Verify"
    WITHDRAW_VERIFY = "WITHDRAW_VERIFY", "Withdraw Verify"
    
@unique
class DishCategoryEnum(TextChoices):
    FOOD = "FOOD", "Food"
    BEVERAGES = "BEVERAGES", "Beverages"
    DESSERT = "DESSERT", "Dessert"
    
@unique
class DishStatusEnum(TextChoices):
    AVAILABLE = "AVAILABLE", "Available"
    OUT_OF_STOCK = "OUT_OF_STOCK", "Out of Stock"   

@unique
class DishLocationTypeEnum(TextChoices):
    REGION = "REGION", "Region"
    SUBREGION = "SUBREGION", "Subregion"
    COUNTRY = "COUNTRY", "Country"
    
@unique
class IngredientCategoryEnum(TextChoices):
    GRAIN = "GRAIN", "Grain"
    PROTEIN = "PROTEIN", "Protein"
    VEGETABLE = "VEGETABLE", "Vegetable"
    FRUIT = "FRUIT", "Fruit"
    OILFATBUTTER = "OILFATBUTTER", "OilFatButter"
    SPICE = "SPICE", "Spice"
    MILK = "MILK", "Milk"
    
@unique
class MenuStatusEnum(TextChoices):
    ACTIVE = "ACTIVE", "Active"
    INACTIVE = "INACTIVE", "Inactive"   
    DRAFT = "DRAFT", "Draft"
@unique
class SortTypeEnum(Enum):
    ASC = "asc"
    DESC = "desc"

@unique
class OrderStatusEnum(TextChoices):
    """Order Status State Machine:

    States:
    - DRAFT: Order created, not yet placed
    - PENDING: Placed, waiting for payment (COD only)
    - CONFIRMED_SYSTEM: Payment successful, auto-confirmed by system (PayOS)
    - CONFIRMED_SHOP: Chef/Shop manually confirmed the order
    - PROCESSING: Chef is preparing the food
    - DELIVERING: Order is being delivered
    - COMPLETED: Order successfully completed
    - CANCELLED: Order cancelled by customer/shop
    """
    DRAFT = "DRAFT", "Draft"   
    PENDING = "PENDING", "Pending"  # COD: Chờ xác nhận
    CONFIRMED_SYSTEM = "CONFIRMED_SYSTEM", "Confirmed by System"  # PayOS: Đã thanh toán
    CONFIRMED_SHOP = "CONFIRMED_SHOP", "Confirmed by Shop"  # Chef xác nhận
    PROCESSING = "PROCESSING", "Processing"
    DELIVERING = "DELIVERING", "Delivering"
    COMPLETED = "COMPLETED", "Completed"
    CANCELLED = "CANCELLED", "Cancelled"
    
@unique
class PaymentMethodEnum(TextChoices):
    COD = "COD", "Cash on Delivery"
    PAYOS = "PAYOS", "PayOS"

@unique
class PaymentStatus(TextChoices):
    PENDING = "PENDING", "Pending"
    SUCCESS = "SUCCESS", "Success"
    HOLDING = "HOLDING", "Holding"
    RELEASED = "RELEASED", "Released"

    REFUND_PENDING = "REFUND_PENDING", "Refund pending"
    REFUNDED = "REFUNDED", "Refunded"

    FAILED = "FAILED", "Failed"
    CANCELLED = "CANCELLED", "Cancelled" 

@unique
class WalletTransactionTypeEnum(TextChoices):
    HOLD = "HOLD", "Hold"
    RELEASE = "RELEASE", "Release from escrow"
    REFUND = "REFUND", "Refund to customer"
    PAYOUT = "PAYOUT", "Payout to chef"

@unique
class WalletTransactionStatusEnum(TextChoices):
    PENDING = "PENDING", "Pending"
    SUCCESS = "SUCCESS", "Success"
    FAILED = "FAILED", "Failed"

@unique
class VietnamBankEnum(TextChoices):
    """Enum cho các ngân hàng Việt Nam"""
    VIETCOMBANK = "Vietcombank", "Vietcombank"
    VCB = "VCB", "VCB"
    TECHCOMBANK = "Techcombank", "Techcombank"
    TCB = "TCB", "TCB"
    VPBANK = "VPBank", "VPBank"
    BIDV = "BIDV", "BIDV"
    AGRIBANK = "Agribank", "Agribank"
    MBBANK = "MBBank", "MBBank"
    ACB = "ACB", "ACB"
    SACOMBANK = "Sacombank", "Sacombank"
    VIETINBANK = "VietinBank", "VietinBank"
    TPBANK = "TPBank", "TPBank"
    HDBANK = "HDBank", "HDBank"
    SHB = "SHB", "SHB"
    OCB = "OCB", "OCB"
    MSB = "MSB", "MSB"
    VIB = "VIB", "VIB"
    LIENVIETPOSTBANK = "LienVietPostBank", "LienVietPostBank"
    SEABANK = "SeABank", "SeABank"
    BACABANK = "BacABank", "BacABank"
    PVCOMBANK = "PVcomBank", "PVcomBank"
    KIENLONGBANK = "KienLongBank", "KienLongBank"
    NCB = "NCB", "NCB"

class VoucherReservationStatus(TextChoices):
    """Trạng thái reservation của voucher"""
    RESERVED = "RESERVED", "Reserved (pending checkout)"
    USED = "USED", "Used (order placed)"
    CANCELLED = "CANCELLED", "Cancelled (checkout cancelled)"
    EXPIRED = "EXPIRED", "Expired (reservation timeout)"

class VoucherDiscountTypeEnum(TextChoices):
    """Loại voucher"""
    PERCENTAGE = "PERCENTAGE", "Percentage"
    FIXED_AMOUNT = "FIXED_AMOUNT", "Fixed Amount"

class VoucherTypeEnum(TextChoices):
    SHOP_VOUCHER = "SHOP_VOUCHER", "Shop Voucher (dành cho chef tạo)"
    PLATFORM_SUBTOTAL = "PLATFORM_SUBTOTAL", "Platform Voucher (dành cho admin tạo)"
    PLATFORM_SHIPPING = "PLATFORM_SHIPPING", "Platform Shipping Voucher (dành cho admin tạo, chỉ giảm phí ship)"

class CertificateTypeEnum(TextChoices):
    FOOD_SAFETY = "FOOD_SAFETY", "Food Safety Certificate"
    BUSINESS_LICENSE = "BUSINESS_LICENSE", "Business License"

class CertificateStatusEnum(TextChoices):
    PENDING = "PENDING", "Pending"
    ACTIVE = "ACTIVE", "Active"
    EXPIRED = "EXPIRED", "Expired"
    REVOKED = "REVOKED", "Revoked"

class IngredientImportStatusEnum(TextChoices):
    PENDING = "PENDING", "Pending"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"

class IngredientSourceEnum(TextChoices):
    CHEF_SUGGESTION = "CHEF_SUGGESTION", "Chef Suggestion"
    USDA = "USDA", "USDA Database"

class DietModeEnum(TextChoices):
    NONE = "NONE", "None"
    BALANCED = "BALANCED", "Balanced"
    LOW_CARB = "LOW_CARB", "Low Carb"
    HIGH_PROTEIN = "HIGH_PROTEIN", "High Protein"
    LOW_FAT = "LOW_FAT", "Low Fat"
    LIGHT = "LIGHT", "Light / Healthy eating"

class DietLevelEnum(TextChoices):
    NONE = "NONE", "None"
    SOFT = "SOFT", "Soft Influence"
    MEDIUM = "MEDIUM", "Medium Influence"
    STRONG = "STRONG", "Strong Influence"
    
class AllergyModeEnum(TextChoices):
    WARN = "WARN", "Warn"
    HIDE = "HIDE", "Hide"

class GenderEnum(TextChoices):
    FEMALE = "FEMALE", "Female"
    MALE = "MALE", "Male"
    OTHER = "OTHER", "Other"

class ActivityLevelEnum(TextChoices):
    SEDENTARY = "SEDENTARY", "Sedentary"
    LIGHT = "LIGHT", "Light"
    MODERATE = "MODERATE", "Moderate"
    ACTIVE = "ACTIVE", "Active"
    VERY_ACTIVE = "VERY_ACTIVE", "Very Active"

class GoalEnum(TextChoices):
    MAINTAIN = "MAINTAIN", "Maintain Weight"
    LOSE = "LOSE", "Lose Weight"
    GAIN = "GAIN", "Gain Weight"

class MealTimeEnum(TextChoices):
    BREAKFAST = "BREAKFAST", "Breakfast"
    LUNCH = "LUNCH", "Lunch"
    DINNER = "DINNER", "Dinner"
    SNACK = "SNACK", "Snack"
    UNKNOWN = "UNKNOWN", "Unknown"

class MealSourceEnum(TextChoices):
    APP = "APP", "App"
    PARSED = "PARSED", "Parsed"
    USDA = "USDA", "USDA"
    MANUAL = "MANUAL", "Manual"

class SortByEnum(TextChoices):
    RATING_DESC = "RATING_DESC", "Rating Descending"
    RATING_ASC = "RATING_ASC", "Rating Ascending"
    PRICE_DESC = "PRICE_DESC", "Price Descending"
    PRICE_ASC = "PRICE_ASC", "Price Ascending"
    SOLD_ASC = "SOLD_ASC", "Sold Count Ascending"
    SOLD_DESC = "SOLD_DESC", "Sold Count Descending"
    
class DeliveryTypeEnum(TextChoices):
    SELF_PICKUP = 'SELF_PICKUP', 'Tự đến lấy'
    THIRD_PARTY = 'THIRD_PARTY', 'Dịch vụ vận chuyển thứ 3'

class DocumentStepStatusEnum(TextChoices):
    PENDING = "PENDING", "Pending"
    EXTRACTED = "EXTRACTED", "Extracted"   # Gemini đọc thành công, chờ chef xác nhận
    CONFIRMED = "CONFIRMED", "Confirmed"   # Chef đã xác nhận

class VerificationSessionStatusEnum(TextChoices):
    IN_PROGRESS = "IN_PROGRESS", "In Progress"        # Đang upload & confirm tài liệu
    AWAITING_SELFIE = "AWAITING_SELFIE", "Awaiting Selfie"  # Cross-validate passed, chờ selfie
    COMPLETED = "COMPLETED", "Completed"              # Đã ra quyết định cuối

# ── Report & Suspension ────────────────────────────────────────────────────────

class ReportCategoryEnum(TextChoices):
    FOOD_SAFETY  = "FOOD_SAFETY",  "An toàn thực phẩm"
    FOOD_QUALITY = "FOOD_QUALITY", "Chất lượng thức ăn"
    WRONG_ITEM   = "WRONG_ITEM",   "Giao sai món"
    MISSING_ITEM = "MISSING_ITEM", "Giao thiếu món"
    HYGIENE      = "HYGIENE",      "Vệ sinh"
    FINANCIAL    = "FINANCIAL",    "Vấn đề tài chính"
    PAYMENT_ISSUE = "PAYMENT_ISSUE", "Vấn đề thanh toán"
    REFUND_ISSUE  = "REFUND_ISSUE",  "Vấn đề hoàn tiền"
    IMPERSONATION = "IMPERSONATION", "Giả mạo danh tính"
    FAKE_BUSINESS = "FAKE_BUSINESS", "Giả mạo thương hiệu"
    INAPPROPRIATE = "INAPPROPRIATE", "Nội dung phản cảm"
    FRAUD         = "FRAUD",         "Lừa đảo"
    POLICY_VIOLATION = "POLICY_VIOLATION", "Vi phạm chính sách"
    ILLEGAL_ACTIVITY = "ILLEGAL_ACTIVITY", "Vi phạm pháp luật"

class WarningTypeEnum(TextChoices):
    FOOD_QUALITY = "FOOD_QUALITY", "Chất lượng thức ăn"
    DELIVERY     = "DELIVERY",     "Giao hàng"
    FINANCIAL    = "FINANCIAL",    "Tài chính"

class SeverityLevelEnum(TextChoices):
    LOW      = "LOW",      "Thấp"
    MEDIUM   = "MEDIUM",   "Trung bình"
    HIGH     = "HIGH",     "Cao"
    CRITICAL = "CRITICAL", "Nghiêm trọng"

class ReportStatusEnum(TextChoices):
    PENDING   = "PENDING",   "Chờ xem xét"
    REVIEWED  = "REVIEWED",  "Đã xem xét"
    DISMISSED = "DISMISSED", "Đã bác bỏ"
    ACTED_ON  = "ACTED_ON",  "Đã xử lý"

class SuspensionTypeEnum(TextChoices):
    DISH_LOCK = "DISH_LOCK", "Khóa món ăn"
    FULL_LOCK = "FULL_LOCK", "Khóa toàn bộ chef"

class SuspensionStatusEnum(TextChoices):
    ACTIVE    = "ACTIVE",    "Đang khóa"
    APPEALING = "APPEALING", "Đang giải trình"
    LIFTED    = "LIFTED",    "Đã mở khóa"
    REJECTED  = "REJECTED",  "Giải trình bị bác bỏ"

class SuspensionTriggerEnum(TextChoices):
    SYSTEM = "SYSTEM", "Hệ thống tự động"
    ADMIN  = "ADMIN",  "Admin thủ công"

class ChefSuspensionLevelEnum(TextChoices):
    NONE      = "NONE",      "Bình thường"
    WARNING   = "WARNING",   "Cảnh báo"
    SUSPENDED = "SUSPENDED", "Đã khóa"