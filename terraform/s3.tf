resource "aws_s3_bucket" "mlflow_artifacts" {
  bucket = "uzair-mlflowops-artifacts-686699774218-eu-central-1"

  tags = {
    Name        = "MLFlowOps Artifacts"
    Environment = "Development"
    ManagedBy   = "Terraform"
    Project     = "MLFlowOps"
  }
}

resource "aws_s3_bucket_public_access_block" "mlflow_artifacts" {
  bucket = aws_s3_bucket.mlflow_artifacts.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "mlflow_artifacts" {
  bucket = aws_s3_bucket.mlflow_artifacts.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_versioning" "mlflow_artifacts" {
  bucket = aws_s3_bucket.mlflow_artifacts.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "mlflow_artifacts" {
  bucket = aws_s3_bucket.mlflow_artifacts.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_iam_policy" "mlflow_s3_access" {
  name        = "uzair-mlflowops-s3-artifacts"
  description = "Allow MLFlowOps workloads to access model artifacts in S3"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket",
          "s3:ListBucketMultipartUploads"
        ]
        Resource = aws_s3_bucket.mlflow_artifacts.arn
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:AbortMultipartUpload",
          "s3:ListMultipartUploadParts"
        ]
        Resource = "${aws_s3_bucket.mlflow_artifacts.arn}/*"
      }
    ]
  })
}

output "mlflow_artifacts_bucket" {
  value = aws_s3_bucket.mlflow_artifacts.bucket
}

output "mlflow_artifacts_bucket_arn" {
  value = aws_s3_bucket.mlflow_artifacts.arn
}

output "mlflow_s3_policy_arn" {
  value = aws_iam_policy.mlflow_s3_access.arn
}
