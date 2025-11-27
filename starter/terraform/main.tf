# =============================================================================
# CymbalFlix Discover - AlloyDB Infrastructure
# =============================================================================
# This Terraform configuration provisions the infrastructure for CymbalFlix
# Discover, an AI-powered movie discovery application built on AlloyDB.
#
# WHAT'S ALREADY CONFIGURED:
# - Google Cloud APIs
# - VPC networking with Private Service Access
# - Service accounts for AlloyDB and the application
# - IAM bindings for secure, passwordless authentication
#
# YOUR TASK:
# - Add the AlloyDB cluster configuration (see TODO section below)
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
# AlloyDB requires several APIs to be enabled. We use a loop here so it's
# easy to add more APIs as needed throughout the lab.

locals {
  required_apis = [
    "alloydb.googleapis.com",           # AlloyDB API
    "compute.googleapis.com",           # Compute Engine (networking)
    "servicenetworking.googleapis.com", # Private Service Access
    "aiplatform.googleapis.com",        # Vertex AI (for embeddings)
    "cloudresourcemanager.googleapis.com", # Resource management
    "iam.googleapis.com",               # IAM (for database authentication)
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
# We'll use this to grant database access via IAM - no passwords needed!

data "google_client_openid_userinfo" "current" {}

# -----------------------------------------------------------------------------
# VPC Network
# -----------------------------------------------------------------------------
# AlloyDB is a VPC-native service, meaning every cluster lives inside a VPC.
# We create a dedicated network for CymbalFlix to keep things organized.

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
# AlloyDB uses Private Service Access (PSA) to securely connect to Google's
# managed services. This allocates a private IP range and creates the peering
# connection that AlloyDB needs.

resource "google_compute_global_address" "private_ip_range" {
  name          = "cymbalflix-private-ip"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 20
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
# We create dedicated service accounts following the principle of least
# privilege. Each component gets its own identity with only the permissions
# it needs.

# Service account for AlloyDB - needs Vertex AI access for AI features
resource "google_service_account" "alloydb" {
  account_id   = "cymbalflix-alloydb"
  display_name = "CymbalFlix AlloyDB Service Account"

  depends_on = [google_project_service.apis]
}

# Grant AlloyDB service account access to Vertex AI for embeddings
resource "google_project_iam_member" "alloydb_vertex_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.alloydb.email}"
}

# Service account for the Cloud Run application
resource "google_service_account" "app" {
  account_id   = "cymbalflix-app"
  display_name = "CymbalFlix Application Service Account"

  depends_on = [google_project_service.apis]
}

# Grant app service account access to connect to AlloyDB
resource "google_project_iam_member" "app_alloydb_client" {
  project = var.project_id
  role    = "roles/alloydb.client"
  member  = "serviceAccount:${google_service_account.app.email}"
}

# -----------------------------------------------------------------------------
# AlloyDB User Registration
# -----------------------------------------------------------------------------
# This registers the student's email as a user INSIDE the database engine,
# allowing them to login via IAM.

resource "google_alloydb_user" "iam_user" {
  cluster   = google_alloydb_cluster.main.id
  user_id   = var.user_email
  user_type = "ALLOYDB_IAM_USER"
  
  # This specific line is what makes them a DB Admin
  database_roles = ["alloydbsuperuser"] 

  depends_on = [google_alloydb_instance.primary]
}

# -----------------------------------------------------------------------------
# Workaround: Mandatory Initial Password
# -----------------------------------------------------------------------------
# Even with IAM Auth, AlloyDB requires an initial password for the default 
# 'postgres' user. We generate a random one here to satisfy the requirement, 
# then simply ignore it (since we will be leveraging IAM).
resource "random_password" "alloydb_initial_password" {
  length           = 16
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}


# =============================================================================
# TODO: ADD YOUR ALLOYDB CLUSTER CONFIGURATION BELOW
# =============================================================================

# YOUR CODE HERE - Use Gemini Code Assist with the prompt above




# =============================================================================
# END TODO SECTION
# =============================================================================


# -----------------------------------------------------------------------------
# Outputs
# -----------------------------------------------------------------------------
# These outputs provide the information you'll need to connect to your
# AlloyDB cluster after it's created.

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
  value       = var.user_email # <--- Reference the variable instead
}

# Uncomment these outputs after adding your AlloyDB cluster:
#
# output "cluster_id" {
#   description = "The AlloyDB cluster ID"
#   value       = google_alloydb_cluster.main.cluster_id
# }
#
# output "primary_instance_ip" {
#   description = "The primary instance public IP address"
#   value       = google_alloydb_instance.primary.public_ip_address
# }
