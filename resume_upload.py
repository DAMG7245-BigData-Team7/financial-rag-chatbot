#!/usr/bin/env python3
"""
Resume Pinecone Upload - Automatically continues from where it stopped
"""

import pickle
from pathlib import Path
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone

print("=" * 80)
print("RESUMING PINECONE UPLOAD")
print("=" * 80)

# Configuration
DOCUMENTS_PATH = "Data/chunked_semantic_test/langchain_documents.pkl"
INDEX_NAME = "fintbx-semantic-3072"
PINECONE_API_KEY = "pcsk_6sow6P_3XHg3HPsuGRcxHGZUSEB1VcM4D4Eedo4kQGvBMXiSUL5fhWAF4rNtnEL1m7cPtv"
OPENAI_API_KEY = "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"

# Load documents
print(f"\n📂 Loading documents...")
with open(DOCUMENTS_PATH, 'rb') as f:
    documents = pickle.load(f)

# Clean metadata (remove None values)
for doc in documents:
    doc.metadata = {k: v for k, v in doc.metadata.items() if v is not None}

print(f"✓ Loaded {len(documents):,} documents")

# Check current status
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(INDEX_NAME)
stats = index.describe_index_stats()
current_count = stats.total_vector_count

print(f"\n📊 Current Status:")
print(f"   Already uploaded: {current_count:,}")
print(f"   Total documents: {len(documents):,}")
print(f"   Remaining: {len(documents) - current_count:,}")

if current_count >= len(documents):
    print(f"\n✅ Upload already complete!")
    exit(0)

# Initialize embeddings
print(f"\n🤖 Initializing embeddings...")
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-large",
    api_key=OPENAI_API_KEY
)

# Connect to vector store
print(f"🔌 Connecting to Pinecone index: {INDEX_NAME}")
vector_store = PineconeVectorStore(
    index_name=INDEX_NAME,
    embedding=embeddings,
    pinecone_api_key=PINECONE_API_KEY
)

# Upload remaining documents in batches
print(f"\n📤 Uploading remaining documents...")
batch_size = 50  # Smaller batches to avoid timeouts
start_idx = current_count
remaining_docs = documents[start_idx:]

total_batches = (len(remaining_docs) + batch_size - 1) // batch_size

try:
    for i in range(0, len(remaining_docs), batch_size):
        batch = remaining_docs[i:i + batch_size]
        batch_num = i // batch_size + 1

        print(f"   Batch {batch_num}/{total_batches}: Uploading {len(batch)} documents...")

        # Add documents
        vector_store.add_documents(batch)

        # Show progress
        uploaded_so_far = start_idx + i + len(batch)
        progress = (uploaded_so_far / len(documents)) * 100
        print(f"   Progress: {uploaded_so_far:,}/{len(documents):,} ({progress:.1f}%)")

    print(f"\n✅ UPLOAD COMPLETE!")

    # Verify
    final_stats = index.describe_index_stats()
    print(f"\n📊 Final Statistics:")
    print(f"   Total vectors in index: {final_stats.total_vector_count:,}")
    print(f"   Expected: {len(documents):,}")

    if final_stats.total_vector_count >= len(documents) * 0.99:
        print(f"\n✅ SUCCESS - All documents uploaded!")
    else:
        print(f"\n⚠️  Some documents may be missing")

except Exception as e:
    print(f"\n❌ Error during upload: {e}")
    import traceback
    traceback.print_exc()

    # Show what was uploaded
    current_stats = index.describe_index_stats()
    print(f"\n📊 Uploaded so far: {current_stats.total_vector_count:,} vectors")
