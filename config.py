# config.py
"""
Centralized configuration for AURELIA project
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project structure
PROJECT_ROOT = Path(__file__).parent.absolute()
CHUNKING_STRATEGY_DIR = PROJECT_ROOT / "chunking_strategy"
DATA_DIR = PROJECT_ROOT / "Data"

# Data subdirectories
RAW_DIR = DATA_DIR / "raw"
MARKDOWN_DIR = DATA_DIR / "markdown_files"
PARSED_DIR = DATA_DIR / "parsed"
PROCESSED_DIR = DATA_DIR / "processed"
LOGS_DIR = DATA_DIR / "logs"

# Create directories if they don't exist
for directory in [RAW_DIR, MARKDOWN_DIR, PARSED_DIR, PROCESSED_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# File paths
PARSED_JSONL = PARSED_DIR / "markdown_files_enhanced.jsonl"
LANGCHAIN_PKL = PROCESSED_DIR / "langchain_documents.pkl"
BM25_ENCODER_PKL = PROCESSED_DIR / "bm25_encoder.pkl"
LANGCHAIN_SUMMARY = PROCESSED_DIR / "langchain_documents_summary.json"

# API Keys
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Pinecone Configuration
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "fintbx-hybrid-3072")
PINECONE_DIMENSION = 3072  # text-embedding-3-large

# Validate API keys
def validate_config():
    """Validate that required configuration is present"""
    errors = []
    
    if not PINECONE_API_KEY:
        errors.append("PINECONE_API_KEY not found in .env file")
    if not OPENAI_API_KEY:
        errors.append("OPENAI_API_KEY not found in .env file")
    
    if errors:
        raise ValueError(
            "Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors) +
            "\n\nPlease create a .env file in the project root with required keys."
        )
    
    return True

# Print configuration on import (optional)
if __name__ == "__main__":
    print("AURELIA Project Configuration")
    print("=" * 50)
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Data Directory: {DATA_DIR}")
    print(f"Parsed JSONL: {PARSED_JSONL}")
    print(f"LangChain PKL: {LANGCHAIN_PKL}")
    print(f"BM25 Encoder: {BM25_ENCODER_PKL}")
    print(f"Pinecone Index: {PINECONE_INDEX_NAME}")
    print("=" * 50)