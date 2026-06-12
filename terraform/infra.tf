# Key pair
resource "tls_private_key" "app_key" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "aws_key_pair" "app_key" {
  key_name   = "amomeal-tech-key"
  public_key = tls_private_key.app_key.public_key_openssh
}

# Lưu local (khi chạy terraform local)
resource "local_file" "private_key" {
  content         = tls_private_key.app_key.private_key_pem
  filename        = "${path.module}/amomeal-tech-key.pem"
  file_permission = "0400"
}

# Lưu S3 (khi chạy qua pipeline)
resource "aws_s3_object" "private_key_s3" {
  bucket = "phuc-amomeal-tech-terraform-state"
  key    = "keys/amomeal-tech-key.pem"
  content = tls_private_key.app_key.private_key_pem
  server_side_encryption = "AES256"
}

# Secrets Manager
resource "aws_secretsmanager_secret" "backend_secret" {
  name                    = "amomeal-tech-backend-secret"
  recovery_window_in_days = 0
  
  tags = {
    Name = "amomeal-tech-backend-secret"
  }
}

resource "aws_secretsmanager_secret_version" "backend_secret_value" {
  secret_id = aws_secretsmanager_secret.backend_secret.id
  secret_string = jsonencode({
    # Auth & Security
    SECRET_KEY                       = var.secret_key
    AUTHENTICATE_TOKEN_EXPIRES_IN    = var.authenticate_token_expires_in
    
    # Database
    DATABASE_URL                     = var.database_url
    POSTGRES_DB                      = var.postgres_db
    POSTGRES_HOST                    = var.postgres_host
    POSTGRES_PASSWORD                = var.postgres_password
    POSTGRES_PORT                    = var.postgres_port
    POSTGRES_USER                    = var.postgres_user
    
    # Email Configuration
    EMAIL_BACKEND                    = var.email_backend
    EMAIL_HOST                       = var.email_host
    EMAIL_HOST_USER                  = var.email_host_user
    EMAIL_HOST_PASSWORD              = var.email_host_password
    EMAIL_PORT                       = var.email_port
    EMAIL_USE_TLS                    = var.email_use_tls
    EMAIL_USE_SSL                    = var.email_use_ssl
    EMAIL_TIMEOUT                    = var.email_timeout
    
    # PAYOS Payment
    PAYOS_API_KEY                    = var.payos_api_key
    PAYOS_API_URL                    = var.payos_api_url
    PAYOS_CHECKSUM_KEY               = var.payos_checksum_key
    PAYOS_CLIENT_ID                  = var.payos_client_id
    PAYOS_RETURN_URL                 = var.payos_return_url
    PAYOS_CANCEL_URL                 = var.payos_cancel_url
    
    # AWS S3 for file storage
    USE_S3                           = var.use_s3
    AWS_ACCESS_KEY_ID                = var.aws_access_key_id
    AWS_SECRET_ACCESS_KEY            = var.aws_secret_access_key
    AWS_STORAGE_BUCKET_NAME          = var.aws_storage_bucket_name
    AWS_S3_REGION_NAME               = var.aws_s3_region_name
    
    # Alternative S3 config
    S3_ACCESS_KEY_ID                 = var.s3_access_key_id
    S3_SECRET_ACCESS_KEY             = var.s3_secret_access_key
    S3_BUCKET_NAME                   = var.s3_bucket_name
    S3_REGION                        = var.s3_region
    S3_EXPIRES_IN                    = var.s3_expires_in
    S3_PUBLIC_URL                    = var.s3_public_url
    
    # Debug (chỉ bật ở môi trường dev)
    DEBUG                            = var.debug

    # New Auth & JWT keys
    AUTH_JWT_ALGORITHM               = var.auth_jwt_algorithm
    AUTH_JWT_SECRET                  = var.auth_jwt_secret
    AUTH_REFRESH_TOKEN_EXPIRES_IN    = var.auth_refresh_token_expires_in
    AUTH_REFRESH_TOKEN_PEPPER        = var.auth_refresh_token_pepper
    
    # Gemini AI integration
    GEMINI_API_KEY                   = var.gemini_api_key
    
    # OTP expiration configs
    OTP_BANK_EXPIRE_MINUTES           = var.otp_bank_expire_minutes
    OTP_RESET_PASSWORD_EXPIRE_MINUTES = var.otp_reset_password_expire_minutes
    OTP_SIGNUP_EXPIRE_MINUTES         = var.otp_signup_expire_minutes
    OTP_WITHDRAW_EXPIRE_MINUTES       = var.otp_withdraw_expire_minutes
    
    # Deployment configs
    PAYMENT_ONLY_DEPLOY              = var.payment_only_deploy
    
    # PAYOS Payouts
    PAYOS_PAYOUT_API_KEY             = var.payos_payout_api_key
    PAYOS_PAYOUT_CHECKSUM_KEY        = var.payos_payout_checksum_key
    PAYOS_PAYOUT_CLIENT_ID           = var.payos_payout_client_id
    
    # Wallet secrets
    WALLET_CHAIN_SECRET              = var.wallet_chain_secret
  })
}

# IAM Role cho EC2
resource "aws_iam_role" "ec2_role" {
  name = "amomeal-tech-ec2-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_policy" "read_secret_policy" {
  name = "read-secret-policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = ["secretsmanager:GetSecretValue"]
      Resource = aws_secretsmanager_secret.backend_secret.arn
    }]
  })
}

resource "aws_iam_role_policy_attachment" "attach_secret_policy" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = aws_iam_policy.read_secret_policy.arn
}

resource "aws_iam_role_policy_attachment" "ssm_policy" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "ec2_profile" {
  name = "amomeal-tech-instance-profile"
  role = aws_iam_role.ec2_role.name
}

# VPC
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags = { Name = "amomeal-tech-vpc" }
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id
}

# Subnets
resource "aws_subnet" "public_us_east_1a" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "us-east-1a"
  map_public_ip_on_launch = true
}

resource "aws_subnet" "public_us_east_1b" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.2.0/24"
  availability_zone       = "us-east-1b"
  map_public_ip_on_launch = true
}

resource "aws_subnet" "private_us_east_1a" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.3.0/24"
  availability_zone       = "us-east-1a"
  map_public_ip_on_launch = false
}

resource "aws_subnet" "private_us_east_1b" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.4.0/24"
  availability_zone       = "us-east-1b"
  map_public_ip_on_launch = false
}

# NAT Gateway
resource "aws_eip" "nat_eip" {
  domain = "vpc"
}

resource "aws_nat_gateway" "nat" {
  allocation_id = aws_eip.nat_eip.id
  subnet_id     = aws_subnet.public_us_east_1a.id
}

# Route Tables
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }
  tags = { Name = "amomeal-tech-public-rt" }
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat.id
  }
  tags = { Name = "amomeal-tech-private-rt" }
}

# Route Table Associations
resource "aws_route_table_association" "public" {
  for_each = {
    "a" = aws_subnet.public_us_east_1a.id
    "b" = aws_subnet.public_us_east_1b.id
  }
  subnet_id      = each.value
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private" {
  for_each = {
    "a" = aws_subnet.private_us_east_1a.id
    "b" = aws_subnet.private_us_east_1b.id
  }
  subnet_id      = each.value
  route_table_id = aws_route_table.private.id
}

# Security Groups
resource "aws_security_group" "alb_sg" {
  name        = "alb-sg"
  vpc_id      = aws_vpc.main.id
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "private_ec2_sg" {
  name        = "private-ec2-sg"
  vpc_id      = aws_vpc.main.id
  ingress {
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    security_groups = [aws_security_group.alb_sg.id]
  }
  # SSH removed - access via SSM Session Manager
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# ALB
resource "aws_lb" "app_alb" {
  name               = "app-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg.id]
  subnets            = [aws_subnet.public_us_east_1a.id, aws_subnet.public_us_east_1b.id]
  tags = { Name = "amomeal-tech-app-alb" }
}

# Target Group cho production (blue) - 95% traffic
resource "aws_lb_target_group" "app_tg" {
  name     = "app-tg"
  port     = 80
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id
  
  health_check {
    path                = "/"
    matcher             = "200-399"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 2
  }
  
  tags = {
    Name = "amomeal-tech-app-tg"
  }
}

# Target Group cho canary (green) - 5% traffic
resource "aws_lb_target_group" "app_tg_canary" {
  name     = "app-tg-canary"
  port     = 8080
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id
  
  health_check {
    path                = "/"
    matcher             = "200-399"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 2
  }
  
  tags = {
    Name = "amomeal-tech-app-tg-canary"
  }
}

# Listener với weighted forwarding
resource "aws_lb_listener" "app_listener" {
  load_balancer_arn = aws_lb.app_alb.arn
  port              = 80
  protocol          = "HTTP"
  
  default_action {
    type = "forward"
    
    forward {
      target_group {
        arn    = aws_lb_target_group.app_tg.arn
        weight = 95
      }
      
      target_group {
        arn    = aws_lb_target_group.app_tg_canary.arn
        weight = 5
      }
      
      stickiness {
        enabled  = false
        duration = 1
      }
    }
  }
}

# Outputs
output "alb_dns_name" {
  value = aws_lb.app_alb.dns_name
}

output "github_actions_role_arn" {
  value = aws_iam_role.github_actions_role.arn
}

# Policy cho phép ELB actions
resource "aws_iam_policy" "elb_policy" {
  name = "elb-policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "elasticloadbalancing:DescribeTargetGroups",
          "elasticloadbalancing:RegisterTargets",
          "elasticloadbalancing:DeregisterTargets"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "attach_elb_policy" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = aws_iam_policy.elb_policy.arn
}

# Policy cho phép EC2 đọc từ S3
resource "aws_iam_policy" "s3_read_policy" {
  name = "s3-read-policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::phuc-amomeal-tech-terraform-state",
          "arn:aws:s3:::phuc-amomeal-tech-terraform-state/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "attach_s3_read" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = aws_iam_policy.s3_read_policy.arn
}