# Provider configuration for Google Cloud Platform
terraform {
  required_version = ">= 1.0"
  
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.0"
    }
  }
  
  # Optional: Use GCS backend for state (uncomment after first apply)
  # backend "gcs" {
  #   bucket = "aurelia-terraform-state"
  #   prefix = "terraform/state"
  # }
}

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "storage.googleapis.com",
    "run.googleapis.com",
    "composer.googleapis.com",
    "sqladmin.googleapis.com",
    "compute.googleapis.com",
    "artifactregistry.googleapis.com",
    "iam.googleapis.com",
    "cloudresourcemanager.googleapis.com"
  ])
  
  service = each.key
  
  disable_on_destroy = false
}

resource "null_resource" "cleanup_database" {
  triggers = {
    # Reference your database instance name here
    # Replace with your actual resource name if different
    instance_name = "aurelia-postgres"
  }

  provisioner "local-exec" {
    when    = destroy
    command = <<-EOT
      echo "🧹 Cleaning up database before destroy..."
      
      gcloud sql connect aurelia-postgres \
        --user=postgres \
        --database=aurelia_db \
        --quiet << 'SQL'
      DROP TABLE IF EXISTS concept_notes CASCADE;
      REASSIGN OWNED BY aurelia_user TO postgres;
      DROP OWNED BY aurelia_user;
      SQL
      
      echo "✅ Cleanup complete"
    EOT
    
    on_failure = continue
  }
}