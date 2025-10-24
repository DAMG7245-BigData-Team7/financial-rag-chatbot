#!/usr/bin/env python3
"""
Unified Configuration for AURELIA DAGs and Scripts
"""

import os
from pathlib import Path

# ============= DAG Configuration =============
# GCP Configuration
GCP_PROJECT_ID = os.getenv("GCP_PROJECT", "aurelia-rag-pipeline")
GCS_BUCKET = os.getenv("AURELIA_GCS_BUCKET", "aurelia-aurelia-rag-pipeline-data")
REGION = "us-east1"

# API Keys
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Database
DB_CONNECTION = os.getenv("AURELIA_DB_CONNECTION")
DB_USER = os.getenv("AURELIA_DB_USER", "aurelia_user")
DB_PASSWORD = os.getenv("AURELIA_DB_PASSWORD")
DB_NAME = os.getenv("AURELIA_DB_NAME", "aurelia_db")

# Concept list for seeding
FINANCIAL_CONCEPTS = [
    "Duration", "Sharpe Ratio", "Black-Scholes Model",
    "Internal Rate of Return", "Net Present Value",
    "Portfolio Optimization", "Yield Curve", "Option Greeks",
    "Monte Carlo Simulation", "Value at Risk",
    "Efficient Frontier", "CAPM", "Bond Convexity", "Modified Duration",
]

# ============= Chunking Strategy Configuration =============
# For running in Airflow, use /tmp directories
PROJECT_ROOT = Path("/home/airflow/gcs/dags")
DATA_DIR = Path("/tmp/data")

# Data subdirectories
RAW_DIR = DATA_DIR / "raw"
MARKDOWN_DIR = Path("/tmp/markdown")  # From convert task
PARSED_DIR = Path("/tmp/parsed")      # From parse task
PROCESSED_DIR = DATA_DIR / "processed"
LOGS_DIR = DATA_DIR / "logs"

# File paths
PARSED_JSONL = PARSED_DIR / "markdown_enhanced.jsonl"
LANGCHAIN_PKL = PROCESSED_DIR / "langchain_documents.pkl"
BM25_ENCODER_PKL = PROCESSED_DIR / "bm25_encoder.pkl"
LANGCHAIN_SUMMARY = PROCESSED_DIR / "langchain_documents_summary.json"

# Pinecone Configuration
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "fintbx-hybrid-3072")
PINECONE_DIMENSION = 3072  # text-embedding-3-large

# Validate API keys
def validate_config():
    """Validate that required configuration is present"""
    errors = []
    
    if not PINECONE_API_KEY:
        errors.append("PINECONE_API_KEY not found in environment")
    if not OPENAI_API_KEY:
        errors.append("OPENAI_API_KEY not found in environment")
    
    if errors:
        raise ValueError(
            "Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors)
        )
    
    return True