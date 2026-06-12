#!/bin/bash
set -e  # Exit on error
set -u  # Exit on undefined variable

TAG=$1
MODE=$2
INSTANCE_ID=$3

echo "========================================="
echo "Deploying mode: $MODE with tag: $TAG"
echo "Instance ID: $INSTANCE_ID"
echo "========================================="

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo "jq not found, installing..."
    sudo yum install -y jq
fi

# Tạo thư mục làm việc
sudo mkdir -p /opt/amomeal

# Tải docker-compose.yml từ S3
echo "📥 Downloading docker-compose.yml from S3..."
sudo aws s3 cp s3://phuc-amomeal-tech-terraform-state/docker-compose.yml /opt/amomeal/docker-compose.yml --region us-east-1

# Lấy secrets từ AWS Secrets Manager
echo "🔐 Fetching secrets from AWS Secrets Manager..."
SECRET=$(aws secretsmanager get-secret-value --secret-id amomeal-tech-backend-secret --query SecretString --output text)

if [ -z "$SECRET" ]; then
    echo "❌ Failed to get secret from AWS Secrets Manager"
    exit 1
fi

# Tạo file .env cho docker-compose
echo "📋 Creating .env file for docker-compose..."
cd /opt/amomeal

cat > .env <<EOL
# Tags
TAG=$TAG

# JWT & Auth
SECRET_KEY=$(echo $SECRET | jq -r .SECRET_KEY)
AUTHENTICATE_TOKEN_EXPIRES_IN=$(echo $SECRET | jq -r .AUTHENTICATE_TOKEN_EXPIRES_IN)
DEBUG=$(echo $SECRET | jq -r .DEBUG)

# Database
DATABASE_URL=$(echo $SECRET | jq -r .DATABASE_URL)
POSTGRES_DB=$(echo $SECRET | jq -r .POSTGRES_DB)
POSTGRES_HOST=$(echo $SECRET | jq -r .POSTGRES_HOST)
POSTGRES_PASSWORD=$(echo $SECRET | jq -r .POSTGRES_PASSWORD)
POSTGRES_PORT=$(echo $SECRET | jq -r .POSTGRES_PORT)
POSTGRES_USER=$(echo $SECRET | jq -r .POSTGRES_USER)

# Email
EMAIL_BACKEND=$(echo $SECRET | jq -r .EMAIL_BACKEND)
EMAIL_HOST=$(echo $SECRET | jq -r .EMAIL_HOST)
EMAIL_HOST_USER=$(echo $SECRET | jq -r .EMAIL_HOST_USER)
EMAIL_HOST_PASSWORD=$(echo $SECRET | jq -r .EMAIL_HOST_PASSWORD)
EMAIL_PORT=$(echo $SECRET | jq -r .EMAIL_PORT)
EMAIL_USE_TLS=$(echo $SECRET | jq -r .EMAIL_USE_TLS)
EMAIL_USE_SSL=$(echo $SECRET | jq -r .EMAIL_USE_SSL)
EMAIL_TIMEOUT=$(echo $SECRET | jq -r .EMAIL_TIMEOUT)

# PAYOS
PAYOS_API_KEY=$(echo $SECRET | jq -r .PAYOS_API_KEY)
PAYOS_API_URL=$(echo $SECRET | jq -r .PAYOS_API_URL)
PAYOS_CHECKSUM_KEY=$(echo $SECRET | jq -r .PAYOS_CHECKSUM_KEY)
PAYOS_CLIENT_ID=$(echo $SECRET | jq -r .PAYOS_CLIENT_ID)
PAYOS_RETURN_URL=$(echo $SECRET | jq -r .PAYOS_RETURN_URL)
PAYOS_CANCEL_URL=$(echo $SECRET | jq -r .PAYOS_CANCEL_URL)

# Redis
REDIS_PASSWORD=$(echo $SECRET | jq -r .REDIS_PASSWORD 2>/dev/null || echo "")

# S3
USE_S3=$(echo $SECRET | jq -r .USE_S3)
AWS_ACCESS_KEY_ID=$(echo $SECRET | jq -r .AWS_ACCESS_KEY_ID)
AWS_SECRET_ACCESS_KEY=$(echo $SECRET | jq -r .AWS_SECRET_ACCESS_KEY)
AWS_STORAGE_BUCKET_NAME=$(echo $SECRET | jq -r .AWS_STORAGE_BUCKET_NAME)
AWS_S3_REGION_NAME=$(echo $SECRET | jq -r .AWS_S3_REGION_NAME)
S3_ACCESS_KEY_ID=$(echo $SECRET | jq -r .S3_ACCESS_KEY_ID)
S3_SECRET_ACCESS_KEY=$(echo $SECRET | jq -r .S3_SECRET_ACCESS_KEY)
S3_BUCKET_NAME=$(echo $SECRET | jq -r .S3_BUCKET_NAME)
S3_REGION=$(echo $SECRET | jq -r .S3_REGION)
S3_EXPIRES_IN=$(echo $SECRET | jq -r .S3_EXPIRES_IN)
S3_PUBLIC_URL=$(echo $SECRET | jq -r .S3_PUBLIC_URL)

# New Auth & JWT keys
AUTH_JWT_ALGORITHM=$(echo $SECRET | jq -r .AUTH_JWT_ALGORITHM)
AUTH_JWT_SECRET=$(echo $SECRET | jq -r .AUTH_JWT_SECRET)
AUTH_REFRESH_TOKEN_EXPIRES_IN=$(echo $SECRET | jq -r .AUTH_REFRESH_TOKEN_EXPIRES_IN)
AUTH_REFRESH_TOKEN_PEPPER=$(echo $SECRET | jq -r .AUTH_REFRESH_TOKEN_PEPPER)

# Gemini AI integration
GEMINI_API_KEY=$(echo $SECRET | jq -r .GEMINI_API_KEY)

# OTP expiration configs
OTP_BANK_EXPIRE_MINUTES=$(echo $SECRET | jq -r .OTP_BANK_EXPIRE_MINUTES)
OTP_RESET_PASSWORD_EXPIRE_MINUTES=$(echo $SECRET | jq -r .OTP_RESET_PASSWORD_EXPIRE_MINUTES)
OTP_SIGNUP_EXPIRE_MINUTES=$(echo $SECRET | jq -r .OTP_SIGNUP_EXPIRE_MINUTES)
OTP_WITHDRAW_EXPIRE_MINUTES=$(echo $SECRET | jq -r .OTP_WITHDRAW_EXPIRE_MINUTES)

# Deployment configs
PAYMENT_ONLY_DEPLOY=$(echo $SECRET | jq -r .PAYMENT_ONLY_DEPLOY)

# PAYOS Payouts
PAYOS_PAYOUT_API_KEY=$(echo $SECRET | jq -r .PAYOS_PAYOUT_API_KEY)
PAYOS_PAYOUT_CHECKSUM_KEY=$(echo $SECRET | jq -r .PAYOS_PAYOUT_CHECKSUM_KEY)
PAYOS_PAYOUT_CLIENT_ID=$(echo $SECRET | jq -r .PAYOS_PAYOUT_CLIENT_ID)

# Wallet secrets
WALLET_CHAIN_SECRET=$(echo $SECRET | jq -r .WALLET_CHAIN_SECRET)
EOL

echo "✅ .env file created successfully"
ls -la .env

if [ "$MODE" = "canary" ]; then
  echo "🚀 Deploying CANARY mode..."
  
  # Tạo file canary
  sudo cp /opt/amomeal/docker-compose.yml /opt/amomeal/docker-compose-canary.yml
  
  # Thay đổi ports cho canary (tránh conflict)
  sudo sed -i 's/8082:8082/8083:8082/g' /opt/amomeal/docker-compose-canary.yml
  sudo sed -i 's/3000:80/3001:80/g' /opt/amomeal/docker-compose-canary.yml
  sudo sed -i 's/container_name: backend/container_name: backend-canary/g' /opt/amomeal/docker-compose-canary.yml
  sudo sed -i 's/container_name: frontend/container_name: frontend-canary/g' /opt/amomeal/docker-compose-canary.yml
  sudo sed -i 's/container_name: mongodb/container_name: mongodb-canary/g' /opt/amomeal/docker-compose-canary.yml
  sudo sed -i 's/container_name: redis/container_name: redis-canary/g' /opt/amomeal/docker-compose-canary.yml
  sudo sed -i 's/container_name: ai-service/container_name: ai-service-canary/g' /opt/amomeal/docker-compose-canary.yml
  sudo sed -i 's/mongodb_data:/mongodb_canary_data:/g' /opt/amomeal/docker-compose-canary.yml
  sudo sed -i 's/redis_data:/redis_canary_data:/g' /opt/amomeal/docker-compose-canary.yml
  
  # Copy .env file to same directory
  sudo cp /opt/amomeal/.env /opt/amomeal/.env.canary 2>/dev/null || true
  
  # Deploy canary (docker compose v2)
  cd /opt/amomeal
  sudo docker compose -f docker-compose-canary.yml --env-file .env down 2>/dev/null || true
  sudo docker compose -f docker-compose-canary.yml --env-file .env up -d
  
  # Đăng ký instance vào target group canary
  echo "📝 Registering instance with canary target group..."
  TG_ARN=$(aws elbv2 describe-target-groups --names app-tg-canary --query 'TargetGroups[0].TargetGroupArn' --output text)
  aws elbv2 register-targets --target-group-arn $TG_ARN --targets Id=$INSTANCE_ID,Port=80
  
  echo "✅ Canary deployment completed!"
  
else
  echo "🚀 Deploying PRODUCTION mode..."
  
  cd /opt/amomeal
  
  # Deploy production (docker compose v2 with .env file)
  sudo docker compose --env-file .env down 2>/dev/null || true
  sudo docker compose --env-file .env up -d
  
  # Đăng ký instance vào target group production
  echo "📝 Registering instance with production target group..."
  TG_ARN=$(aws elbv2 describe-target-groups --names app-tg --query 'TargetGroups[0].TargetGroupArn' --output text)
  aws elbv2 register-targets --target-group-arn $TG_ARN --targets Id=$INSTANCE_ID,Port=80
  
  # Hủy đăng ký instance khỏi target group canary
  echo "📝 Deregistering instance from canary target group..."
  TG_CANARY_ARN=$(aws elbv2 describe-target-groups --names app-tg-canary --query 'TargetGroups[0].TargetGroupArn' --output text)
  aws elbv2 deregister-targets --target-group-arn $TG_CANARY_ARN --targets Id=$INSTANCE_ID 2>/dev/null || true
  
  # Xóa file canary
  sudo rm -f docker-compose-canary.yml
  
  echo "✅ Production deployment completed!"
fi

echo "========================================="
echo "Deployment completed for mode: $MODE"
echo "========================================="