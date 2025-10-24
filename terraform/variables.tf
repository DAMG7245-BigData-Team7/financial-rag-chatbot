# Project Configuration
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region for resources"
  type        = string
  default     = "us-east1"
}

variable "zone" {
  description = "GCP zone for resources"
  type        = string
  default     = "us-east1-b"
}

# Application Configuration
variable "app_name" {
  description = "Application name prefix"
  type        = string
  default     = "aurelia"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

# Cloud Storage
variable "bucket_name" {
  description = "GCS bucket name for data storage"
  type        = string
  default     = "aurelia-financial-data"
}

# Cloud SQL
variable "db_instance_name" {
  description = "Cloud SQL instance name"
  type        = string
  default     = "aurelia-postgres"
}

variable "db_name" {
  description = "PostgreSQL database name"
  type        = string
  default     = "aurelia_db"
}

variable "db_user" {
  description = "PostgreSQL user"
  type        = string
  default     = "aurelia_user"
}

variable "db_password" {
  description = "PostgreSQL password"
  type        = string
  sensitive   = true
}

# Cloud Composer (Airflow)
variable "composer_env_name" {
  description = "Cloud Composer environment name"
  type        = string
  default     = "aurelia-airflow"
}

variable "composer_machine_type" {
  description = "Machine type for Composer"
  type        = string
  default     = "n1-standard-1"  # Cheapest option
}

# API Keys (from environment variables, not stored in Terraform)
variable "pinecone_api_key" {
  description = "Pinecone API key"
  type        = string
  sensitive   = true
}

variable "openai_api_key" {
  description = "OpenAI API key"
  type        = string
  sensitive   = true
}

# Cloud Run
variable "fastapi_image" {
  description = "FastAPI Docker image"
  type        = string
  default     = "gcr.io/PROJECT_ID/fastapi-service:latest"
}

variable "streamlit_image" {
  description = "Streamlit Docker image"
  type        = string
  default     = "gcr.io/PROJECT_ID/streamlit-app:latest"
}

variable "fastapi_memory" {
  description = "Memory allocation for FastAPI service"
  type        = string
  default     = "2Gi"
}

variable "fastapi_cpu" {
  description = "CPU allocation for FastAPI service"
  type        = string
  default     = "2"
}

variable "streamlit_memory" {
  description = "Memory allocation for Streamlit service"
  type        = string
  default     = "1Gi"
}

variable "streamlit_cpu" {
  description = "CPU allocation for Streamlit service"
  type        = string
  default     = "1"
}