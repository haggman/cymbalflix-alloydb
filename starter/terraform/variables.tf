# =============================================================================
# CymbalFlix Discover - AlloyDB Infrastructure Variables
# =============================================================================
# These variables configure your AlloyDB cluster and supporting infrastructure.
# Most values have sensible defaults for this lab environment.
# =============================================================================

variable "project_id" {
  description = "The Google Cloud project ID where resources will be created"
  type        = string
}

variable "region" {
  description = "The Google Cloud region for AlloyDB and related resources"
  type        = string
  default     = "us-central1"
}

variable "user_email" {
  description = "The email address of the user running this lab (e.g., student-***@qwiklabs.net)"
  type        = string
}

variable "cluster_id" {
  description = "The identifier for the AlloyDB cluster"
  type        = string
  default     = "cymbalflix-cluster"
}

variable "primary_instance_id" {
  description = "The identifier for the primary AlloyDB instance"
  type        = string
  default     = "cymbalflix-primary"
}

variable "read_pool_id" {
  description = "The identifier for the AlloyDB read pool"
  type        = string
  default     = "cymbalflix-read-pool"
}

variable "network_name" {
  description = "Name of the VPC network to create"
  type        = string
  default     = "cymbalflix-network"
}
