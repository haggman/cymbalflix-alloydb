# =============================================================================
# CymbalFlix Discover - AlloyDB Infrastructure (SOLUTION)
# =============================================================================
# This is the complete Terraform configuration including the AlloyDB cluster.
# Use this as a reference if you need help with the TODO section.
# =============================================================================

# -----------------------------------------------------------------------------
# Terraform Configuration
# -----------------------------------------------------------------------------
terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# -----------------------------------------------------------------------------
# Enable Required APIs
# -----------------------------------------------------------------------------
locals {
  required_apis = [
    "alloydb.googleapis.com",
    "compute.googleapis.com",
    "servicenetworking.googleapis.com",
    "aiplatform.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "iam.googleapis.com",
  ]
}

resource "google_project_service" "apis" {
  for_each           = toset(local.required_apis)
  service            = each.value
  disable_on_destroy = false
}

# -----------------------------------------------------------------------------
# Get Current User Identity
# -----------------------------------------------------------------------------
data "google_client_openid_userinfo" "current" {}

# -----------------------------------------------------------------------------
# VPC Network
# -----------------------------------------------------------------------------
resource "google_compute_network" "main" {
  name                    = var.network_name
  auto_create_subnetworks = false

  depends_on = [google_project_service.apis]
}

resource "google_compute_subnetwork" "main" {
  name          = "${var.network_name}-subnet"
  ip_cidr_range = "10.0.0.0/24"
  network       = google_compute_network.main.id
  region        = var.region
}

# -----------------------------------------------------------------------------
# Private Service Access
# -----------------------------------------------------------------------------
resource "google_compute_global_address" "private_ip_range" {
  name          = "cymbalflix-private-ip"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.main.id

  depends_on = [google_project_service.apis]
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.main.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_range.name]

  depends_on = [google_project_service.apis]
}

# -----------------------------------------------------------------------------
# Service Accounts
# -----------------------------------------------------------------------------
resource "google_service_account" "alloydb" {
  account_id   = "cymbalflix-alloydb"
  display_name = "CymbalFlix AlloyDB Service Account"

  depends_on = [google_project_service.apis]
}

resource "google_project_iam_member" "alloydb_vertex_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.alloydb.email}"
}

resource "google_service_account" "app" {
  account_id   = "cymbalflix-app"
  display_name = "CymbalFlix Application Service Account"

  depends_on = [google_project_service.apis]
}

resource "google_project_iam_member" "app_alloydb_client" {
  project = var.project_id
  role    = "roles/alloydb.client"
  member  = "serviceAccount:${google_service_account.app.email}"
}

# -----------------------------------------------------------------------------
# IAM Database Authentication
# -----------------------------------------------------------------------------
# Grant the current user permission to connect to AlloyDB using IAM auth
resource "google_project_iam_member" "user_alloydb_client" {
  project = var.project_id
  role    = "roles/alloydb.databaseUser"
  member  = "user:${data.google_client_openid_userinfo.current.email}"
}

resource "google_project_iam_member" "user_alloydb_admin" {
  project = var.project_id
  role    = "roles/alloydb.admin"
  member  = "user:${data.google_client_openid_userinfo.current.email}"
}


# =============================================================================
# AlloyDB Cluster Configuration
# =============================================================================

# The AlloyDB Cluster - this is the logical container for your database
resource "google_alloydb_cluster" "main" {
  cluster_id = var.cluster_id
  location   = var.region

  # Network configuration - AlloyDB lives inside your VPC
  network_config {
    network = google_compute_network.main.id
  }

  # Note: No initial_user block! We're using IAM authentication instead.
  # This is more secure - no passwords to manage or accidentally expose.

  # This ensures the private service connection exists before creating the cluster
  depends_on = [google_service_networking_connection.private_vpc_connection]
}

# The Primary Instance - handles all write operations
resource "google_alloydb_instance" "primary" {
  cluster       = google_alloydb_cluster.main.name
  instance_id   = var.primary_instance_id
  instance_type = "PRIMARY"

  # Machine configuration - 2 vCPUs is the minimum for AlloyDB
  machine_config {
    cpu_count = 2
  }

  # Enable public IP for easier connectivity from Cloud Shell
  network_config {
    enable_public_ip = true
  }

  # Database flags to enable the columnar engine for analytics
  # This is what makes AlloyDB so fast for analytical queries!
  database_flags = {
    "google_columnar_engine.enabled"                     = "on"
    "google_columnar_engine.enable_auto_columnarization" = "on"
  }

  depends_on = [google_alloydb_cluster.main]
}

# The Read Pool - handles read operations and can scale independently
resource "google_alloydb_instance" "read_pool" {
  cluster       = google_alloydb_cluster.main.name
  instance_id   = var.read_pool_id
  instance_type = "READ_POOL"

  # Read pool configuration
  read_pool_config {
    node_count = 1
  }

  machine_config {
    cpu_count = 2
  }

  # Enable public IP on read pool as well
  network_config {
    enable_public_ip = true
  }

  # Columnar engine on read pool for analytical queries
  database_flags = {
    "google_columnar_engine.enabled"                     = "on"
    "google_columnar_engine.enable_auto_columnarization" = "on"
  }

  depends_on = [google_alloydb_instance.primary]
}

# -----------------------------------------------------------------------------
# IAM Database User
# -----------------------------------------------------------------------------
# Create a database user that authenticates via IAM
# This maps your Google Cloud identity to a PostgreSQL user
resource "google_alloydb_user" "iam_user" {
  cluster        = google_alloydb_cluster.main.name
  user_id        = data.google_client_openid_userinfo.current.email
  user_type      = "ALLOYDB_IAM_USER"
  database_roles = ["alloydbsuperuser"]

  depends_on = [google_alloydb_instance.primary]
}


# -----------------------------------------------------------------------------
# Outputs
# -----------------------------------------------------------------------------
output "project_id" {
  description = "The project ID"
  value       = var.project_id
}

output "region" {
  description = "The region where AlloyDB is deployed"
  value       = var.region
}

output "network_name" {
  description = "The VPC network name"
  value       = google_compute_network.main.name
}

output "alloydb_service_account" {
  description = "The AlloyDB service account email"
  value       = google_service_account.alloydb.email
}

output "app_service_account" {
  description = "The application service account email"
  value       = google_service_account.app.email
}

output "current_user_email" {
  description = "Your email (granted IAM database access)"
  value       = data.google_client_openid_userinfo.current.email
}

output "cluster_id" {
  description = "The AlloyDB cluster ID"
  value       = google_alloydb_cluster.main.cluster_id
}

output "cluster_name" {
  description = "The AlloyDB cluster full name"
  value       = google_alloydb_cluster.main.name
}

output "primary_instance_name" {
  description = "The primary instance full name"
  value       = google_alloydb_instance.primary.name
}

output "primary_instance_ip" {
  description = "The primary instance public IP address"
  value       = google_alloydb_instance.primary.public_ip_address
}

output "read_pool_instance_ip" {
  description = "The read pool public IP address"
  value       = google_alloydb_instance.read_pool.public_ip_address
}

output "connection_info" {
  description = "Connection information for the AlloyDB cluster"
  value       = <<-EOT
    
    ============================================
    AlloyDB Connection Information
    ============================================
    
    Cluster ID:      ${google_alloydb_cluster.main.cluster_id}
    Region:          ${var.region}
    
    Primary Instance:
      Public IP:     ${google_alloydb_instance.primary.public_ip_address}
    
    Read Pool:
      Public IP:     ${google_alloydb_instance.read_pool.public_ip_address}
    
    IAM Database User:
      Email:         ${data.google_client_openid_userinfo.current.email}
    
    To connect via Auth Proxy with IAM authentication:
      alloydb-auth-proxy ${var.project_id}:${var.region}:${var.cluster_id} \
        --auto-iam-authn
    
    Then connect with psql:
      psql "host=127.0.0.1 port=5432 dbname=postgres user=${data.google_client_openid_userinfo.current.email} sslmode=disable"
    
    ============================================
  EOT
}
