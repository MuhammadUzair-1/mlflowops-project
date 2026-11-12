output "cluster_name" {
  value = aws_eks_cluster.mlflowops.name
}

output "cluster_endpoint" {
  value = aws_eks_cluster.mlflowops.endpoint
}

output "vpc_id" {
  value = aws_vpc.mlflowops.id
}

output "public_subnet_ids" {
  value = aws_subnet.public[*].id
}

output "node_group_name" {
  value = aws_eks_node_group.mlflowops.node_group_name
}
