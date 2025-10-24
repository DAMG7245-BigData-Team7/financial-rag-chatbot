#!/usr/bin/env python3
"""
Uploader wrapper that uses the full AURELIA converter and uploader
"""

import sys
import os
from pathlib import Path

# Add dags directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from aurelia_to_langchain import AureliaToLangChainConverter
from upload_to_pinecone_hybrid import upload_to_pinecone_hybrid


def upload_documents(jsonl_path: str = "/tmp/parsed/parsed_enhanced.jsonl"):
    """
    Convert JSONL to LangChain documents and upload to Pinecone
    
    Args:
        jsonl_path: Path to parsed JSONL file
    """
    import pickle
    import tempfile
    
    print(f"📤 Starting upload pipeline...")
    print(f"   JSONL input: {jsonl_path}")
    
    # Step 1: Convert JSONL to LangChain Documents
    print("\n🔄 Converting JSONL to LangChain Documents...")
    converter = AureliaToLangChainConverter()
    
    aurelia_elements = converter.load_aurelia_jsonl(jsonl_path)
    print(f"   Loaded {len(aurelia_elements)} AURELIA elements")
    
    documents = converter.convert_to_langchain_documents(aurelia_elements)
    print(f"   Converted to {len(documents)} LangChain Documents")
    
    # Step 2: Save to pickle temporarily
    temp_pkl = "/tmp/langchain_documents.pkl"
    with open(temp_pkl, 'wb') as f:
        pickle.dump(documents, f)
    print(f"   Saved to temporary pickle: {temp_pkl}")
    
    # Step 3: Upload to Pinecone using full uploader
    print("\n📤 Uploading to Pinecone...")
    
    index, bm25_encoder = upload_to_pinecone_hybrid(
        documents_pkl_path=temp_pkl,
        index_name=os.getenv("PINECONE_INDEX_NAME", "fintbx-hybrid-3072"),
        pinecone_api_key=os.getenv("PINECONE_API_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        dimension=3072,
        create_new_index=False,  # Assume index exists
        save_bm25_encoder=True,
        bm25_save_path="/tmp/bm25_encoder.pkl"
    )
    
    print(f"✅ Upload complete using full AURELIA pipeline!")
    
    # Cleanup temp pickle
    Path(temp_pkl).unlink(missing_ok=True)
    
    return index