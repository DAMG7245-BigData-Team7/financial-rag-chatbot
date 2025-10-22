# Terraform Outputs - Important values after deployment

# ============================================
# STORAGE
# ============================================

output "data_bucket_name" {
  value       = google_storage_bucket.data_bucket.name
  description = "GCS bucket name for data storage"
}

output "data_bucket_url" {
  value       = google_storage_bucket.data_bucket.url
  description = "GCS bucket URL"
}

output "terraform_state_bucket" {
  value       = google_storage_bucket.terraform_state.name
  description = "GCS bucket for Terraform state"
}

# ============================================
# DATABASE
# ============================================

output "db_instance_name" {
  value       = google_sql_database_instance.postgres.name
  description = "Cloud SQL instance name"
}

output "db_connection_name" {
  value       = google_sql_database_instance.postgres.connection_name
  description = "Cloud SQL connection name (for Cloud Run socket connection)"
}

output "db_public_ip" {
  value       = google_sql_database_instance.postgres.public_ip_address
  description = "Database public IP address"
}

output "db_private_ip" {
  value       = google_sql_database_instance.postgres.private_ip_address
  description = "Database private IP address (if configured)"
}

output "db_connection_string" {
  value       = "postgresql://${var.db_user}:${var.db_password}@${google_sql_database_instance.postgres.public_ip_address}:5432/${var.db_name}"
  sensitive   = true
  description = "PostgreSQL connection string (sensitive)"
}

output "db_user" {
  value       = var.db_user
  description = "Database username"
}

output "db_name" {
  value       = var.db_name
  description = "Database name"
}

# ============================================
# AIRFLOW (CLOUD COMPOSER)
# ============================================

output "airflow_environment_name" {
  value       = google_composer_environment.airflow.name
  description = "Cloud Composer environment name"
}

output "airflow_ui_url" {
  value       = google_composer_environment.airflow.config[0].airflow_uri
  description = "Airflow web UI URL (click to access)"
}

output "airflow_gcs_bucket" {
  value       = google_composer_environment.airflow.config[0].dag_gcs_prefix
  description = "GCS path for uploading Airflow DAGs"
}

output "airflow_region" {
  value       = google_composer_environment.airflow.region
  description = "Airflow environment region"
}

# ============================================
# SERVICE ACCOUNTS
# ============================================

output "fastapi_service_account" {
  value       = google_service_account.fastapi_sa.email
  description = "FastAPI service account email"
}

output "streamlit_service_account" {
  value       = google_service_account.streamlit_sa.email
  description = "Streamlit service account email"
}

output "composer_service_account" {
  value       = google_service_account.composer_sa.email
  description = "Composer service account email"
}

# ============================================
# CLOUD RUN (Will be populated after manual deployment)
# ============================================

# Note: These outputs won't exist until Cloud Run services are deployed
# They're commented out since we're deploying Cloud Run via GitHub Actions

# output "fastapi_url" {
#   value       = google_cloud_run_service.fastapi.status[0].url
#   description = "FastAPI service URL (for API calls)"
# }

# output "streamlit_url" {
#   value       = google_cloud_run_service.streamlit.status[0].url
#   description = "Streamlit app URL (open in browser)"
# }

# ============================================
# PROJECT INFO
# ============================================

output "project_id" {
  value       = var.project_id
  description = "GCP Project ID"
}

output "region" {
  value       = var.region
  description = "GCP region"
}

# ============================================
# DEPLOYMENT SUMMARY
# ============================================

output "deployment_summary" {
  value = <<-EOT
  
  ============================================================
  🎉 AURELIA INFRASTRUCTURE DEPLOYED SUCCESSFULLY!
  ============================================================
  
  📦 STORAGE
     Bucket Name: ${google_storage_bucket.data_bucket.name}
     Bucket URL:  ${google_storage_bucket.data_bucket.url}
  
  🗄️  DATABASE
     Instance:    ${google_sql_database_instance.postgres.name}
     Connection:  ${google_sql_database_instance.postgres.connection_name}
     Public IP:   ${google_sql_database_instance.postgres.public_ip_address}
     Database:    ${var.db_name}
     User:        ${var.db_user}
  
  ✈️  AIRFLOW
     Environment: ${google_composer_environment.airflow.name}
     Web UI:      ${google_composer_environment.airflow.config[0].airflow_uri}
     DAG Bucket:  ${google_composer_environment.airflow.config[0].dag_gcs_prefix}
  
  👤 SERVICE ACCOUNTS
     FastAPI:     ${google_service_account.fastapi_sa.email}
     Streamlit:   ${google_service_account.streamlit_sa.email}
     Composer:    ${google_service_account.composer_sa.email}
  
  ============================================================
  📋 NEXT STEPS:
  ============================================================
  
  1. Add GitHub Secrets:
     - GCP_PROJECT_ID
     - GCP_SA_KEY
     - PINECONE_API_KEY
     - OPENAI_API_KEY
     - DB_PASSWORD
     - DB_HOST (${google_sql_database_instance.postgres.public_ip_address})
     - DB_CONNECTION_NAME (${google_sql_database_instance.postgres.connection_name})
  
  2. Create GitHub Actions workflows:
     - .github/workflows/deploy-backend.yml
     - .github/workflows/deploy-frontend.yml
     - .github/workflows/deploy-dags.yml
  
  3. Create Airflow DAGs:
     - dags/fintbx_ingest_dag.py
     - dags/concept_seed_dag.py
  
  4. Push to GitHub:
     - git push origin main
     - Watch workflows run automatically!
  
  5. Access your deployed services:
     - FastAPI: Will be deployed by GitHub Actions
     - Streamlit: Will be deployed by GitHub Actions
     - Airflow: ${google_composer_environment.airflow.config[0].airflow_uri}
  
  ============================================================
  📊 INFRASTRUCTURE COSTS (Estimated):
  ============================================================
  
  Cloud Composer:  ~$100-150/month
  Cloud SQL:       ~$10-20/month  
  Cloud Run:       ~$0-5/month (generous free tier)
  GCS:             ~$0-5/month
  
  Total: ~$115-180/month
  
  💡 TIP: Run 'terraform destroy' after demo to avoid charges!
  
  ============================================================
  
  EOT
  
  description = "Complete deployment summary with all URLs and next steps"
}

# ============================================
# QUICK REFERENCE OUTPUTS
# ============================================

output "quick_reference" {
  value = {
    project_id          = var.project_id
    region              = var.region
    data_bucket         = google_storage_bucket.data_bucket.name
    db_ip               = google_sql_database_instance.postgres.public_ip_address
    db_connection       = google_sql_database_instance.postgres.connection_name
    airflow_ui          = google_composer_environment.airflow.config[0].airflow_uri
    airflow_dags_bucket = google_composer_environment.airflow.config[0].dag_gcs_prefix
  }
  description = "Quick reference for commonly used values"
}