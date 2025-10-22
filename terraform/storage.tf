# Google Cloud Storage - Data Storage

# Main data bucket
resource "google_storage_bucket" "data_bucket" {
  name          = "${var.app_name}-${var.project_id}-data"
  location      = var.region
  force_destroy = true  # For dev - set to false in prod
  
  uniform_bucket_level_access = true
  
  versioning {
    enabled = true  # Keep version history
  }
  
  lifecycle_rule {
    condition {
      age = 90  # Delete files older than 90 days
    }
    action {
      type = "Delete"
    }
  }
  
  labels = {
    environment = var.environment
    app         = var.app_name
    managed_by  = "terraform"
  }
}

# Create folders (using objects)
resource "google_storage_bucket_object" "folders" {
  for_each = toset([
    "raw/",
    "markdown/",
    "parsed/",
    "processed/",
    "logs/"
  ])
  
  name    = each.key
  content = " "  # Empty placeholder
  bucket  = google_storage_bucket.data_bucket.name
}

# Bucket for Terraform state (optional - for team collaboration)
resource "google_storage_bucket" "terraform_state" {
  name          = "${var.app_name}-terraform-state"
  location      = var.region
  force_destroy = false
  
  uniform_bucket_level_access = true
  
  versioning {
    enabled = true
  }
  
  labels = {
    environment = var.environment
    app         = var.app_name
    purpose     = "terraform-state"
  }
}

# Output bucket name
/**output "data_bucket_name" {
  value       = google_storage_bucket.data_bucket.name
  description = "GCS bucket name for data storage"
}

output "data_bucket_url" {
  value       = google_storage_bucket.data_bucket.url
  description = "GCS bucket URL"
}**/