variable "secret_key" {
  description = "Django secret key"
  type        = string
  sensitive   = true
}

variable "authenticate_token_expires_in" {
  description = "Token expiration time"
  type        = string
  default     = "3600"
}

variable "database_url" {
  description = "Database connection URL"
  type        = string
  sensitive   = true
}

variable "postgres_db" {
  description = "Postgres database name"
  type        = string
}

variable "postgres_host" {
  description = "Postgres host"
  type        = string
}

variable "postgres_password" {
  description = "Postgres password"
  type        = string
  sensitive   = true
}

variable "postgres_port" {
  description = "Postgres port"
  type        = string
  default     = "5432"
}

variable "postgres_user" {
  description = "Postgres user"
  type        = string
}

# Email variables
variable "email_backend" {
  description = "Email backend class"
  type        = string
  default     = "django.core.mail.backends.smtp.EmailBackend"
}

variable "email_host" {
  description = "Email SMTP host"
  type        = string
}

variable "email_host_user" {
  description = "Email SMTP username"
  type        = string
}

variable "email_host_password" {
  description = "Email SMTP password"
  type        = string
  sensitive   = true
}

variable "email_port" {
  description = "Email SMTP port"
  type        = number
  default     = 587
}

variable "email_use_tls" {
  description = "Use TLS for email"
  type        = string
  default     = true
}

variable "email_use_ssl" {
  description = "Use SSL for email"
  type        = string
  default     = false
}

variable "email_timeout" {
  description = "Email timeout in seconds"
  type        = number
  default     = 30
}

# PAYOS variables
variable "payos_api_key" {
  description = "PAYOS API key"
  type        = string
  sensitive   = true
}

variable "payos_api_url" {
  description = "PAYOS API URL"
  type        = string
}

variable "payos_checksum_key" {
  description = "PAYOS checksum key"
  type        = string
  sensitive   = true
}

variable "payos_client_id" {
  description = "PAYOS client ID"
  type        = string
}

variable "payos_return_url" {
  description = "PAYOS return URL after payment"
  type        = string
}

variable "payos_cancel_url" {
  description = "PAYOS cancel URL"
  type        = string
}

# S3 variables
variable "use_s3" {
  description = "Use S3 for file storage"
  type        = string
  default     = false
}

variable "aws_access_key_id" {
  description = "AWS access key ID for S3"
  type        = string
  sensitive   = true
  default     = ""
}

variable "aws_secret_access_key" {
  description = "AWS secret access key for S3"
  type        = string
  sensitive   = true
  default     = ""
}

variable "aws_storage_bucket_name" {
  description = "AWS S3 bucket name for storage"
  type        = string
  default     = ""
}

variable "aws_s3_region_name" {
  description = "AWS S3 region"
  type        = string
  default     = "us-east-1"
}

variable "s3_access_key_id" {
  description = "Alternative S3 access key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "s3_secret_access_key" {
  description = "Alternative S3 secret key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "s3_bucket_name" {
  description = "Alternative S3 bucket name"
  type        = string
  default     = ""
}

variable "s3_region" {
  description = "Alternative S3 region"
  type        = string
  default     = "us-east-1"
}

variable "s3_expires_in" {
  description = "S3 URL expiration time"
  type        = string
  default     = "3600"
}

variable "s3_public_url" {
  description = "S3 public URL"
  type        = string
  default     = ""
}

variable "debug" {
  description = "Debug mode"
  type        = string
  default     = false
}
variable "redis_password" {
  description = "Redis password"
  type        = string
  sensitive   = true
  default     = ""
}

# New Auth & JWT variables
variable "auth_jwt_algorithm" {
  description = "Auth JWT signature algorithm"
  type        = string
  default     = "HS256"
}

variable "auth_jwt_secret" {
  description = "Auth JWT secret key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "auth_refresh_token_expires_in" {
  description = "Expiration time for refresh tokens in seconds"
  type        = string
  default     = "2592000"
}

variable "auth_refresh_token_pepper" {
  description = "Auth refresh token pepper key"
  type        = string
  sensitive   = true
  default     = ""
}

# Gemini API Integration
variable "gemini_api_key" {
  description = "Gemini AI API key"
  type        = string
  sensitive   = true
  default     = ""
}

# OTP Expire Minutes
variable "otp_bank_expire_minutes" {
  description = "OTP expiration time in minutes for bank registration"
  type        = string
  default     = "5"
}

variable "otp_reset_password_expire_minutes" {
  description = "OTP expiration time in minutes for password resets"
  type        = string
  default     = "10"
}

variable "otp_signup_expire_minutes" {
  description = "OTP expiration time in minutes for account signups"
  type        = string
  default     = "5"
}

variable "otp_withdraw_expire_minutes" {
  description = "OTP expiration time in minutes for withdrawals"
  type        = string
  default     = "5"
}

# Deployment mode settings
variable "payment_only_deploy" {
  description = "Deploy with payment integration only"
  type        = string
  default     = "false"
}

# PAYOS Payout integration
variable "payos_payout_api_key" {
  description = "PAYOS Payout API key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "payos_payout_checksum_key" {
  description = "PAYOS Payout checksum key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "payos_payout_client_id" {
  description = "PAYOS Payout client ID"
  type        = string
  default     = ""
}

# Wallet Chain Settings
variable "wallet_chain_secret" {
  description = "Wallet chain secret key"
  type        = string
  sensitive   = true
  default     = ""
}