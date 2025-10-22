# Cloud Run - FastAPI Service and Streamlit Frontend

# FastAPI Service
/**
resource "google_cloud_run_service" "fastapi" {
  name     = "${var.app_name}-api"
  location = var.region
  
  template {
    spec {
      service_account_name = google_service_account.fastapi_sa.email
      
      containers {
        image = var.fastapi_image
        
        resources {
          limits = {
            cpu    = var.fastapi_cpu
            memory = var.fastapi_memory
          }
        }
        
        # Environment variables
        env {
          name  = "PINECONE_API_KEY"
          value = var.pinecone_api_key
        }
        
        env {
          name  = "OPENAI_API_KEY"
          value = var.openai_api_key
        }
        
        env {
          name  = "GCS_BUCKET"
          value = google_storage_bucket.data_bucket.name
        }
        
        env {
          name  = "DB_HOST"
          value = google_sql_database_instance.postgres.public_ip_address
        }
        
        env {
          name  = "DB_USER"
          value = var.db_user
        }
        
        env {
          name  = "DB_PASSWORD"
          value = var.db_password
        }
        
        env {
          name  = "DB_NAME"
          value = var.db_name
        }
        
        env {
          name  = "PINECONE_INDEX_NAME"
          value = "fintbx-hybrid-3072"
        }
        
        # Port
        ports {
          container_port = 8080
        }
      }
    }
    
    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale" = "0"  # Scale to zero when idle
        "autoscaling.knative.dev/maxScale" = "10"
        "run.googleapis.com/cloudsql-instances" = google_sql_database_instance.postgres.connection_name
      }
    }
  }
  
  traffic {
    percent         = 100
    latest_revision = true
  }
  
  depends_on = [
    google_project_service.required_apis,
    google_sql_database.database
  ]
}

# Make FastAPI publicly accessible
resource "google_cloud_run_service_iam_member" "fastapi_public" {
  service  = google_cloud_run_service.fastapi.name
  location = google_cloud_run_service.fastapi.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Streamlit Frontend
resource "google_cloud_run_service" "streamlit" {
  name     = "${var.app_name}-frontend"
  location = var.region
  
  template {
    spec {
      service_account_name = google_service_account.streamlit_sa.email
      
      containers {
        image = var.streamlit_image
        
        resources {
          limits = {
            cpu    = var.streamlit_cpu
            memory = var.streamlit_memory
          }
        }
        
        # Environment variables
        env {
          name  = "FASTAPI_URL"
          value = google_cloud_run_service.fastapi.status[0].url
        }
        
        # Port
        ports {
          container_port = 8501  # Streamlit default port
        }
      }
    }
    
    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale" = "0"
        "autoscaling.knative.dev/maxScale" = "5"
      }
    }
  }
  
  traffic {
    percent         = 100
    latest_revision = true
  }
  
  depends_on = [
    google_cloud_run_service.fastapi
  ]
}

# Make Streamlit publicly accessible
resource "google_cloud_run_service_iam_member" "streamlit_public" {
  service  = google_cloud_run_service.streamlit.name
  location = google_cloud_run_service.streamlit.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Outputs
output "fastapi_url" {
  value       = google_cloud_run_service.fastapi.status[0].url
  description = "FastAPI service URL"
}

output "streamlit_url" {
  value       = google_cloud_run_service.streamlit.status[0].url
  description = "Streamlit frontend URL"
}
**/