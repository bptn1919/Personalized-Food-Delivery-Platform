provider "aws" {
  region = "us-east-1"
}

terraform {
  backend "s3" {
    bucket         = "phuc-amomeal-tech-terraform-state"
    key            = "amomeal-tech/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    use_lockfile   = true
  }
  required_providers {
    aws = {
      source = "hashicorp/aws"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
    local = {
      source = "hashicorp/local"
    }
  }
}

# S3 bucket cho Terraform state
resource "aws_s3_bucket" "terraform_state" {
  bucket = "phuc-amomeal-tech-terraform-state"
  tags = { Name = "terraform-state" }
  
  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_versioning" "terraform_state_versioning" {
  bucket = aws_s3_bucket.terraform_state.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state_encryption" {
  bucket = aws_s3_bucket.terraform_state.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "terraform_state_block" {
  bucket = aws_s3_bucket.terraform_state.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# GitHub OIDC provider
resource "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"
  client_id_list = ["sts.amazonaws.com"]
  thumbprint_list = ["ffffffffffffffffffffffffffffffffffffffff"]
  
  lifecycle {
    prevent_destroy = true
  }
}

# IAM Role cho GitHub Actions
resource "aws_iam_role" "github_actions_role" {
  name = "github-actions-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = { Federated = aws_iam_openid_connect_provider.github.arn }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringLike = {
            "token.actions.githubusercontent.com:sub" = "repo:AMOMEAL/DOANCHUYENNGANH:*"
          }
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "github_admin" {
  role       = aws_iam_role.github_actions_role.name
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
}

# Upload docker-compose.yml lên S3
resource "aws_s3_object" "docker_compose" {
  bucket = "phuc-amomeal-tech-terraform-state"
  key    = "docker-compose.yml"
  content = file("${path.module}/../compose/docker-compose.yml")
  etag = filemd5("${path.module}/../compose/docker-compose.yml")
  server_side_encryption = "AES256"
}

# ✅ Upload script deploy lên S3
resource "aws_s3_object" "deploy_script" {
  bucket = "phuc-amomeal-tech-terraform-state"
  key    = "scripts/deploy-production.sh"
  content = file("${path.module}/../scripts/deploy-production.sh")
  etag = filemd5("${path.module}/../scripts/deploy-production.sh")
  server_side_encryption = "AES256"
}