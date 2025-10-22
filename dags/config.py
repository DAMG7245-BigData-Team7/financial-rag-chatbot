#!/usr/bin/env python3
"""
DAG Configuration
"""

import os

# GCP Configuration
GCP_PROJECT_ID = os.getenv("GCP_PROJECT", "aurelia-rag-pipeline")
GCS_BUCKET = os.getenv("AURELIA_GCS_BUCKET")
REGION = "us-east1"

# API Keys
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Database
DB_CONNECTION = os.getenv("AURELIA_DB_CONNECTION")
DB_USER = os.getenv("AURELIA_DB_USER")
DB_PASSWORD = os.getenv("AURELIA_DB_PASSWORD")
DB_NAME = os.getenv("AURELIA_DB_NAME")

# Concept list for seeding
FINANCIAL_CONCEPTS = [
    "Duration",
    "Sharpe Ratio",
    "Black-Scholes Model",
    "Internal Rate of Return",
    "Net Present Value",
    "Portfolio Optimization",
    "Yield Curve",
    "Option Greeks",
    "Monte Carlo Simulation",
    "Value at Risk",
    "Efficient Frontier",
    "CAPM",
    "Bond Convexity",
    "Modified Duration",
]