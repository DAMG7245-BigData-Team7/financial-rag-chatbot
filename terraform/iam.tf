# IAM - Service Accounts and Permissions

# Service account for FastAPI
resource "google_service_account" "fastapi_sa" {
  account_id   = "${var.app_name}-fastapi-sa"
  display_name = "AURELIA FastAPI Service Account"
  description  = "Service account for FastAPI Cloud Run service"
}

# Service account for Streamlit
resource "google_service_account" "streamlit_sa" {
  account_id   = "${var.app_name}-streamlit-sa"
  display_name = "AURELIA Streamlit Service Account"
  description  = "Service account for Streamlit Cloud Run service"
}

# Service account for Airflow (Cloud Composer)
resource "google_service_account" "composer_sa" {
  account_id   = "${var.app_name}-composer-sa"
  display_name = "AURELIA Cloud Composer Service Account"
  description  = "Service account for Cloud Composer (Airflow)"
}

# Grant permissions to FastAPI service account
resource "google_project_iam_member" "fastapi_permissions" {
  for_each = toset([
    "roles/cloudsql.client",      # Access Cloud SQL
    "roles/storage.objectAdmin",   # Read/write GCS
    "roles/logging.logWriter",     # Write logs
  ])
  
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.fastapi_sa.email}"
}

# Grant permissions to Streamlit service account
resource "google_project_iam_member" "streamlit_permissions" {
  for_each = toset([
    "roles/logging.logWriter",     # Write logs
  ])
  
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.streamlit_sa.email}"
}

# Grant permissions to Composer service account
resource "google_project_iam_member" "composer_permissions" {
  for_each = toset([
    "roles/composer.worker",       # Run Airflow tasks
    "roles/storage.objectAdmin",   # Read/write GCS
    "roles/cloudsql.client",       # Access Cloud SQL
    "roles/logging.logWriter",     # Write logs
  ])
  
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.composer_sa.email}"
}

# Grant Cloud Composer Service Agent permissions
resource "google_project_iam_member" "composer_service_agent" {
  project = var.project_id
  role    = "roles/composer.ServiceAgentV2Ext"
  member  = "serviceAccount:service-393163457785@cloudcomposer-accounts.iam.gserviceaccount.com"
  
  depends_on = [google_project_service.required_apis]
}

# Output service account emails
output "fastapi_service_account" {
  value       = google_service_account.fastapi_sa.email
  description = "FastAPI service account email"
}

output "composer_service_account" {
  value       = google_service_account.composer_sa.email
  description = "Composer service account email"
}