# Cloud SQL PostgreSQL Database

# PostgreSQL instance
resource "google_sql_database_instance" "postgres" {
  name             = var.db_instance_name
  database_version = "POSTGRES_14"
  region           = var.region
  
  deletion_protection = false  # For dev - set to true in prod
  
  settings {
    tier = "db-f1-micro"  # Cheapest tier (shared CPU, 0.6GB RAM)
    # For production, use: db-custom-2-7680 (2 vCPU, 7.5GB RAM)
    
    disk_size = 10  # GB
    disk_type = "PD_SSD"
    
    # Backups
    backup_configuration {
      enabled            = true
      start_time         = "03:00"  # 3 AM daily backups
      point_in_time_recovery_enabled = true
    }
    
    # High availability (disable for dev to save cost)
    availability_type = "ZONAL"  # Change to "REGIONAL" for prod
    
    # IP configuration
    ip_configuration {
      ipv4_enabled    = true
       # Enable SSL in prod
      
      # Allow connections from Cloud Run
      authorized_networks {
        name  = "cloud-run"
        value = "0.0.0.0/0"  # In prod, restrict to Cloud Run IPs
      }
    }
    
    # Maintenance window
    maintenance_window {
      day  = 7  # Sunday
      hour = 4  # 4 AM
    }
  }
  
  depends_on = [google_project_service.required_apis]
}

# Create database
resource "google_sql_database" "database" {
  name     = var.db_name
  instance = google_sql_database_instance.postgres.name
}

# Create user
resource "google_sql_user" "user" {
  name     = var.db_user
  instance = google_sql_database_instance.postgres.name
  password = var.db_password
}

# Output connection details
output "db_connection_name" {
  value       = google_sql_database_instance.postgres.connection_name
  description = "Cloud SQL connection name"
}

output "db_public_ip" {
  value       = google_sql_database_instance.postgres.public_ip_address
  description = "Database public IP address"
}

output "db_connection_string" {
  value       = "postgresql://${var.db_user}:${var.db_password}@${google_sql_database_instance.postgres.public_ip_address}:5432/${var.db_name}"
  sensitive   = true
  description = "PostgreSQL connection string"
}