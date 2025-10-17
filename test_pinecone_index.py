#!/usr/bin/env python3
"""
Test what's actually in the Pinecone index
"""

from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone

# API keys
PINECONE_API_KEY = "pcsk_6sow6P_3XHg3HPsuGRcxHGZUSEB1VcM4D4Eedo4kQGvBMXiSUL5fhWAF4rNtnEL1m7cPtv"
OPENAI_API_KEY = "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"
INDEX_NAME = "fintbx-semantic-3072"

print("=" * 80)
print(f"TESTING PINECONE INDEX: {INDEX_NAME}")
print("=" * 80)

# Initialize Pinecone client
print("\n1. Checking index stats...")
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(INDEX_NAME)
stats = index.describe_index_stats()

print(f"   Total vectors: {stats.total_vector_count}")
print(f"   Dimension: {stats.dimension}")

# Initialize embeddings and vector store
print("\n2. Initializing embeddings and vector store...")
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-large",
    api_key=OPENAI_API_KEY
)

vector_store = PineconeVectorStore(
    index_name=INDEX_NAME,
    embedding=embeddings,
    pinecone_api_key=PINECONE_API_KEY
)
print("   ✓ Connected to vector store")

# Test query for blsprice
print("\n3. Testing query: 'blsprice function'")
results = vector_store.similarity_search("blsprice function", k=5)

print(f"\n   Found {len(results)} results:")
for i, doc in enumerate(results, 1):
    print(f"\n   Result {i}:")
    print(f"   Page: {doc.metadata.get('page', 'N/A')}")
    print(f"   Type: {doc.metadata.get('type', 'N/A')}")
    print(f"   Section: {doc.metadata.get('section', 'N/A')}")
    print(f"   Content preview: {doc.page_content[:150]}...")

# Test query for Black-Scholes
print("\n\n4. Testing query: 'What is the Black-Scholes model'")
results = vector_store.similarity_search("What is the Black-Scholes model", k=5)

print(f"\n   Found {len(results)} results:")
for i, doc in enumerate(results, 1):
    print(f"\n   Result {i}:")
    print(f"   Page: {doc.metadata.get('page', 'N/A')}")
    print(f"   Type: {doc.metadata.get('type', 'N/A')}")
    print(f"   Section: {doc.metadata.get('section', 'N/A')}")
    print(f"   Content preview: {doc.page_content[:150]}...")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
