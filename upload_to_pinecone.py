#!/usr/bin/env python3
"""
Upload Semantic Chunks to Pinecone
Uploads the improved AURELIA documents with hierarchy to Pinecone vector store
"""

import os
import pickle
import sys
from pathlib import Path
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
import time

def upload_to_pinecone(
    documents_pkl_path: str,
    index_name: str,
    pinecone_api_key: str,
    openai_api_key: str,
    dimension: int = 3072,  # text-embedding-3-large dimension
    create_new_index: bool = False
):
    """
    Upload LangChain documents with semantic hierarchy to Pinecone

    Args:
        documents_pkl_path: Path to pickle file with LangChain documents
        index_name: Name of Pinecone index
        pinecone_api_key: Pinecone API key
        openai_api_key: OpenAI API key
        dimension: Embedding dimension (3072 for text-embedding-3-large)
        create_new_index: Whether to create a new index
    """

    print("=" * 80)
    print("UPLOADING SEMANTIC CHUNKS TO PINECONE")
    print("=" * 80)

    # Load documents
    print(f"\n📂 Loading documents from: {documents_pkl_path}")
    with open(documents_pkl_path, 'rb') as f:
        documents = pickle.load(f)
    print(f"✓ Loaded {len(documents)} documents")

    # Clean metadata - remove None values for Pinecone compatibility
    print(f"\n🧹 Cleaning metadata (removing None values)...")
    for doc in documents:
        doc.metadata = {k: v for k, v in doc.metadata.items() if v is not None}
    print(f"✓ Metadata cleaned")

    # Show sample metadata
    if documents:
        print(f"\n📋 Sample metadata fields:")
        sample_keys = list(documents[0].metadata.keys())
        print(f"   {', '.join(sample_keys[:10])}")
        if 'section_breadcrumb' in documents[0].metadata:
            print(f"   ✓ Hierarchy fields present: parent_id, section_path, section_breadcrumb")

    # Initialize Pinecone
    print(f"\n🔌 Initializing Pinecone...")
    pc = Pinecone(api_key=pinecone_api_key)

    # Check if index exists
    existing_indexes = pc.list_indexes().names()
    print(f"   Existing indexes: {existing_indexes}")

    if create_new_index:
        if index_name in existing_indexes:
            print(f"\n⚠️  Index '{index_name}' already exists!")
            print(f"   Deleting and recreating index '{index_name}'...")
            pc.delete_index(index_name)
            print(f"   ✓ Index deleted")
            time.sleep(5)  # Wait for deletion to complete

        if create_new_index:
            print(f"\n🆕 Creating new index: {index_name}")
            pc.create_index(
                name=index_name,
                dimension=dimension,
                metric='cosine',
                spec=ServerlessSpec(
                    cloud='aws',
                    region='us-east-1'
                )
            )
            print(f"   Waiting for index to be ready...")
            time.sleep(10)  # Wait for index to initialize

    # Initialize embeddings
    print(f"\n🤖 Initializing OpenAI embeddings (text-embedding-3-large)...")
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-large",
        api_key=openai_api_key
    )
    print(f"   ✓ Embeddings ready")

    # Upload documents to Pinecone
    print(f"\n📤 Uploading {len(documents)} documents to Pinecone...")
    print(f"   Index: {index_name}")
    print(f"   This may take several minutes...")

    try:
        # Upload in batches for better progress tracking
        batch_size = 100
        total_batches = (len(documents) + batch_size - 1) // batch_size

        vector_store = None
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            batch_num = i // batch_size + 1

            print(f"   Batch {batch_num}/{total_batches}: Uploading {len(batch)} documents...")

            if vector_store is None:
                # First batch - create vector store
                vector_store = PineconeVectorStore.from_documents(
                    documents=batch,
                    embedding=embeddings,
                    index_name=index_name,
                    pinecone_api_key=pinecone_api_key
                )
            else:
                # Subsequent batches - add to existing
                vector_store.add_documents(batch)

        print(f"\n✅ Upload complete!")

        # Verify upload
        index = pc.Index(index_name)
        stats = index.describe_index_stats()
        print(f"\n📊 Index Statistics:")
        print(f"   Total vectors: {stats.total_vector_count}")
        print(f"   Dimension: {stats.dimension}")

        # Test retrieval with hierarchy
        print(f"\n🔍 Testing retrieval with hierarchy metadata...")
        test_query = "How to calculate bond prices in MATLAB?"
        results = vector_store.similarity_search(test_query, k=3)

        print(f"\n   Query: '{test_query}'")
        print(f"   Top results:")
        for i, doc in enumerate(results[:3], 1):
            breadcrumb = doc.metadata.get('section_breadcrumb', 'N/A')
            parent = doc.metadata.get('parent_id', 'N/A')
            print(f"   {i}. Section: {breadcrumb[:60]}...")
            print(f"      Parent: {parent}")
            print(f"      Content: {doc.page_content[:80]}...")
            print()

        print("=" * 80)
        print("✅ UPLOAD SUCCESSFUL - READY FOR RAG!")
        print("=" * 80)
        print(f"\nYou can now use this index in your RAG system:")
        print(f"  Index name: {index_name}")
        print(f"  Total documents: {len(documents)}")
        print(f"  Hierarchy support: ✓")

        return vector_store

    except Exception as e:
        print(f"\n❌ Upload failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Main execution"""

    # Configuration
    DOCUMENTS_PATH = "Data/chunked_semantic_test/langchain_documents.pkl"
    INDEX_NAME = "fintbx-semantic-3072"  # New index name for semantic chunks

    # API Keys (from your existing script)
    PINECONE_API_KEY = "pcsk_6sow6P_3XHg3HPsuGRcxHGZUSEB1VcM4D4Eedo4kQGvBMXiSUL5fhWAF4rNtnEL1m7cPtv"
    OPENAI_API_KEY = "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"

    # Check if documents exist
    if not Path(DOCUMENTS_PATH).exists():
        print(f"❌ Documents not found: {DOCUMENTS_PATH}")
        print(f"   Please run aurelia_to_langchain.py first to create the documents")
        return

    # Check command line argument for create_new
    import sys
    create_new_index = len(sys.argv) > 1 and sys.argv[1] == '--create-new'

    print(f"\nIndex name: {INDEX_NAME}")
    if create_new_index:
        print(f"Mode: Creating new index")
    else:
        print(f"Mode: Using existing index (use --create-new to create)")

    # Upload
    vector_store = upload_to_pinecone(
        documents_pkl_path=DOCUMENTS_PATH,
        index_name=INDEX_NAME,
        pinecone_api_key=PINECONE_API_KEY,
        openai_api_key=OPENAI_API_KEY,
        dimension=3072,
        create_new_index=create_new_index
    )

    if vector_store:
        print(f"\n💡 Next steps:")
        print(f"   1. Update financial_qa_system.py to use index: '{INDEX_NAME}'")
        print(f"   2. Test queries with hierarchical context")
        print(f"   3. Compare results with old index")


if __name__ == "__main__":
    main()
