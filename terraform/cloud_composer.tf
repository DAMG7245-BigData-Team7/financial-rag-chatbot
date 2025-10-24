# Cloud Composer (Managed Airflow) - Composer 2.x compatible

resource "google_composer_environment" "airflow" {
  name   = var.composer_env_name
  region = var.region
  
  config {
    # Environment size (replaces machine type configs in Composer 2.x)
    environment_size = "ENVIRONMENT_SIZE_SMALL"
    
    # Software configuration
    software_config {
      image_version = "composer-2-airflow-2"
      
      pypi_packages = {
        "langchain"              = ">=0.1.0"
        "langchain-openai"       = ">=0.0.5"
        "langchain-pinecone"     = ">=0.0.3"
        "langchain-community"    = ">=0.0.20"
        "pinecone-client"        = ">=3.0.0"
        "pinecone-text"          = ">=0.7.0"
        "openai"                 = ">=1.0.0"
        "google-cloud-storage"   = ">=2.10.0"
        "pymupdf"                = ">=1.23.0"
        "requests"               = ">=2.31.0"
        "instructor"             = ">=0.4.0"
        "wikipedia"              = ">=1.4.0"
        "psycopg2-binary"        = ">=2.9.9"
      }
      
      env_variables = {
        PINECONE_API_KEY         = var.pinecone_api_key
        OPENAI_API_KEY           = var.openai_api_key
        PINECONE_INDEX_NAME      = "fintbx-hybrid-3072"  # ← ADD THIS LINE
        AURELIA_GCS_BUCKET       = google_storage_bucket.data_bucket.name
        AURELIA_DB_CONNECTION    = google_sql_database_instance.postgres.connection_name
        AURELIA_DB_USER          = var.db_user
        AURELIA_DB_PASSWORD      = var.db_password
        AURELIA_DB_NAME          = var.db_name
        AURELIA_PROJECT_ID              = var.project_id  # ← ADD THIS LINE TOO
        }
    }
    
    # Workloads configuration
    workloads_config {
      scheduler {
        cpu        = 0.5
        memory_gb  = 1.875
        storage_gb = 1
        count      = 1
      }
      
      web_server {
        cpu        = 0.5
        memory_gb  = 1.875
        storage_gb = 1
      }
      
      worker {
        cpu        = 0.5
        memory_gb  = 1.875
        storage_gb = 1
        min_count  = 1
        max_count  = 3
      }
    }
    
    # ADD THIS: Node configuration with service account
    node_config {
      service_account = google_service_account.composer_sa.email
    }
  }
  
  labels = {
    environment = var.environment
    app         = var.app_name
    managed_by  = "terraform"
  }
  
  depends_on = [
    google_project_service.required_apis,
    google_service_account.composer_sa
  ]
  
  timeouts {
    create = "90m"
    update = "60m"
    delete = "60m"
  }
}

/**output "airflow_ui_url" {
  value       = google_composer_environment.airflow.config[0].airflow_uri
  description = "Airflow web UI URL"
}

output "airflow_gcs_bucket" {
  value       = google_composer_environment.airflow.config[0].dag_gcs_prefix
  description = "GCS bucket for Airflow DAGs"
}**/