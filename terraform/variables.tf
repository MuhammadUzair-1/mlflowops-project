variable "aws_region" {
  type    = string
  default = "eu-central-1"
}

variable "cluster_name" {
  type    = string
  default = "uzair-mlflowops-eks"
}

variable "kubernetes_version" {
  type    = string
  default = "1.37"
}

variable "vpc_cidr" {
  type    = string
  default = "10.50.0.0/16"
}

variable "instance_type" {
  type    = string
  default = "t3.medium"
}

variable "admin_cidr" {
  description = "Public IP allowed to access the EKS API"
  type        = string
}
