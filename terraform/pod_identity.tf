resource "aws_iam_role" "mlflow_pod" {
  name = "uzair-mlflowops-mlflow-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "pods.eks.amazonaws.com"
        }
        Action = [
          "sts:AssumeRole",
          "sts:TagSession"
        ]
      }
    ]
  })

  tags = {
    Project     = "MLFlowOps"
    Environment = "Development"
  }
}

resource "aws_iam_role_policy_attachment" "mlflow_s3" {
  role       = aws_iam_role.mlflow_pod.name
  policy_arn = aws_iam_policy.mlflow_s3_access.arn
}

resource "aws_eks_pod_identity_association" "mlflow" {
  cluster_name    = aws_eks_cluster.mlflowops.name
  namespace       = "mlflow"
  service_account = "mlflow-server"
  role_arn        = aws_iam_role.mlflow_pod.arn

  depends_on = [
    aws_iam_role_policy_attachment.mlflow_s3
  ]
}

output "mlflow_iam_role_arn" {
  value = aws_iam_role.mlflow_pod.arn
}
