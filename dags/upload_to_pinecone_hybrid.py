#!/usr/bin/env python3
"""
Upload Documents to Pinecone with Hybrid Search Support
Generates both dense (semantic) and sparse (BM25) vectors for hybrid retrieval
"""

import os
import pickle
import sys
from pathlib import Path
from typing import List
from dotenv import load_dotenv
from tqdm import tqdm

# Load environment variables first
# For Airflow - use environment variables and inline paths
try:
    load_dotenv()
except:
    pass  # load_dotenv not needed in Airflow

# Try to import from config, fallback to environment variables
try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import (
        LANGCHAIN_PKL, BM25_ENCODER_PKL, PINECONE_API_KEY,
        OPENAI_API_KEY, PINECONE_INDEX_NAME, PINECONE_DIMENSION
    )
    try:
        from config import validate_config
        validate_config()
    except:
        pass
except:
    # Fallback for Airflow environment
    LANGCHAIN_PKL = Path("/tmp/processed/langchain_documents.pkl")
    BM25_ENCODER_PKL = Path("/tmp/processed/bm25_encoder.pkl")
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "fintbx-hybrid-3072")
    PINECONE_DIMENSION = 3072

from langchain_openai import OpenAIEmbeddings
from pinecone import Pinecone, ServerlessSpec
from pinecone_text.sparse import BM25Encoder
import time
from langchain.schema import Document


def prepare_hybrid_vectors(documents: List[Document], bm25_encoder: BM25Encoder):
    """
    Prepare documents with both dense and sparse vectors

    Args:
        documents: List of LangChain documents
        bm25_encoder: BM25 encoder for sparse vectors

    Returns:
        Tuple of (texts, dense_vectors, sparse_vectors, metadatas, ids)
    """
    print(f"\n🔄 Preparing hybrid vectors (dense + sparse)...")

    texts = [doc.page_content for doc in documents]
    metadatas = [doc.metadata for doc in documents]

    # Generate unique IDs
    ids = [f"doc_{i:06d}" for i in range(len(documents))]

    # Fit BM25 encoder on the corpus
    print(f"   Training BM25 encoder on {len(texts)} documents...")
    bm25_encoder.fit(texts)
    print(f"   ✓ BM25 encoder trained")

    # Encode texts to sparse vectors
    print(f"   Generating sparse vectors...")
    sparse_vectors = bm25_encoder.encode_documents(texts)
    print(f"   ✓ Generated {len(sparse_vectors)} sparse vectors")

    return texts, sparse_vectors, metadatas, ids


def upload_to_pinecone_hybrid(
    documents_pkl_path: str,
    index_name: str,
    pinecone_api_key: str,
    openai_api_key: str,
    dimension: int = 3072,  # text-embedding-3-large dimension
    create_new_index: bool = False,
    save_bm25_encoder: bool = True,
    bm25_save_path: str = None
):
    """
    Upload documents to Pinecone with hybrid search support

    Args:
        documents_pkl_path: Path to pickle file with LangChain documents
        index_name: Name of Pinecone index (will use hybrid)
        pinecone_api_key: Pinecone API key
        openai_api_key: OpenAI API key
        dimension: Embedding dimension
        create_new_index: Whether to create a new index
        save_bm25_encoder: Whether to save the fitted BM25 encoder
    """

    print("=" * 80)
    print("UPLOADING TO PINECONE WITH HYBRID SEARCH (DENSE + SPARSE)")
    print("=" * 80)

    # Load documents
    print(f"\n📂 Loading documents from: {documents_pkl_path}")
    with open(documents_pkl_path, 'rb') as f:
        documents = pickle.load(f)
    print(f"✓ Loaded {len(documents)} documents")

    # Clean metadata
    print(f"\n🧹 Cleaning metadata...")
    for doc in documents:
        doc.metadata = {k: v for k, v in doc.metadata.items() if v is not None}
    print(f"✓ Metadata cleaned")

    # Initialize Pinecone
    print(f"\n🔌 Initializing Pinecone...")
    pc = Pinecone(api_key=pinecone_api_key)

    # Check existing indexes
    existing_indexes = [idx.name for idx in pc.list_indexes()]
    print(f"   Existing indexes: {existing_indexes}")

    # Create or verify hybrid index
    if create_new_index:
        if index_name in existing_indexes:
            print(f"\n⚠️  Index '{index_name}' already exists!")
            print(f"   Using existing index (non-interactive mode)")
            create_new_index = False

        if create_new_index:
            print(f"\n🆕 Creating hybrid index: {index_name}")
            print(f"   Metric: dotproduct (required for sparse vectors)")
            print(f"   Dimension: {dimension}")

            pc.create_index(
                name=index_name,
                dimension=dimension,
                metric='dotproduct',  # Required for hybrid search
                spec=ServerlessSpec(
                    cloud='aws',
                    region='us-east-1'
                )
            )
            print(f"   ✓ Index created")
            print(f"   Waiting for index to be ready...")
            time.sleep(15)

    # Initialize embeddings
    print(f"\n🤖 Initializing OpenAI embeddings...")
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-large",
        api_key=openai_api_key
    )
    print(f"   ✓ Embeddings ready")

    # Initialize BM25 encoder
    print(f"\n📝 Initializing BM25 encoder for sparse vectors...")
    bm25_encoder = BM25Encoder()
    print(f"   ✓ BM25 encoder ready")

    # Prepare hybrid vectors
    texts, sparse_vectors, metadatas, ids = prepare_hybrid_vectors(documents, bm25_encoder)

    # Save BM25 encoder for query-time use
    if save_bm25_encoder:
        encoder_path = Path(bm25_save_path) if bm25_save_path else Path(documents_pkl_path).parent / "bm25_encoder.pkl"
        print(f"\nSaving BM25 encoder to: {encoder_path}")
        with open(encoder_path, 'wb') as f:
            pickle.dump(bm25_encoder, f)
        print(f"    BM25 encoder saved")
        print(f"   Location: {encoder_path}")
        print(f"   Use this path in financial_qa_system_hybrid.py")

    # Generate dense embeddings with memory management
    print(f"\n🔢 Generating dense embeddings with memory management...")
    print(f"   This may take several minutes for {len(texts)} documents...")

    batch_size = 25  # Reduced from 100 to 25 for better memory management
    dense_vectors = []

    import gc

    for i in tqdm(range(0, len(texts), batch_size), desc="Embedding"):
        batch_texts = texts[i:i + batch_size]
        
        try:
            # Generate embeddings for this batch
            batch_embeddings = embeddings.embed_documents(batch_texts)
            dense_vectors.extend(batch_embeddings)
            
            # Aggressive memory cleanup every 10 batches (~250 documents)
            if i > 0 and i % (batch_size * 10) == 0:
                gc.collect()  # Force garbage collection
                print(f"\n🧹 Memory cleanup at {len(dense_vectors)}/{len(texts)} vectors...")
                time.sleep(2)
            
            # Small delay to prevent overwhelming the worker
            time.sleep(0.5)
            
        except Exception as e:
            print(f"\n❌ Failed at batch {i//batch_size + 1}: {e}")
            print(f"   Processed {len(dense_vectors)}/{len(texts)} vectors before failure")
            raise

    print(f"   ✓ Generated {len(dense_vectors)} dense vectors")

    # Upload to Pinecone
    print(f"\n📤 Uploading {len(documents)} vectors to Pinecone (hybrid)...")
    print(f"   Index: {index_name}")

    index = pc.Index(index_name)

    # Prepare vectors for upsert
    upload_batch_size = 25
    total_batches = (len(ids) + upload_batch_size - 1) // upload_batch_size

    skipped_count = 0

    for i in tqdm(range(0, len(ids), upload_batch_size), total=total_batches, desc="Uploading"):
        batch_ids = ids[i:i + upload_batch_size]
        batch_dense = dense_vectors[i:i + upload_batch_size]
        batch_sparse = sparse_vectors[i:i + upload_batch_size]
        batch_metadata = metadatas[i:i + upload_batch_size]

        # Format vectors for Pinecone
        vectors_to_upsert = []
        for j in range(len(batch_ids)):
            # Skip documents with empty sparse vectors
            if len(batch_sparse[j]['indices']) == 0:
                skipped_count += 1
                continue

            # Add text content to metadata for retrieval
            metadata_with_text = batch_metadata[j].copy()
            metadata_with_text['text'] = texts[i + j]  # Add the text content

            vector_dict = {
                'id': batch_ids[j],
                'values': batch_dense[j],
                'sparse_values': {
                    'indices': batch_sparse[j]['indices'],
                    'values': batch_sparse[j]['values']
                },
                'metadata': metadata_with_text
            }
            vectors_to_upsert.append(vector_dict)

        # Upsert batch (only if not empty)
        if vectors_to_upsert:
            index.upsert(vectors=vectors_to_upsert)

    print(f"\n✅ Upload complete!")

    if skipped_count > 0:
        print(f"\n⚠️  Skipped {skipped_count} documents with empty sparse vectors")
        print(f"   (Documents containing only stopwords or too short)")

    # Verify upload
    time.sleep(2)  # Wait for index to update
    stats = index.describe_index_stats()
    print(f"\n📊 Index Statistics:")
    print(f"   Total vectors: {stats.total_vector_count}")
    print(f"   Documents uploaded: {len(ids) - skipped_count}/{len(ids)}")
    print(f"   Dimension: {stats.dimension}")
    print(f"   Metric: dotproduct (hybrid search enabled)")

    print(f"\n✅ Hybrid search setup complete!")
    print(f"   Dense vectors: OpenAI text-embedding-3-large (semantic)")
    print(f"   Sparse vectors: BM25 (keyword matching)")
    print(f"   Both stored in: {index_name}")

    return index, bm25_encoder


def main():
    """Main upload function"""
    import sys
    from pathlib import Path

    # Configuration
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # Paths
    documents_pkl = str(LANGCHAIN_PKL)
    index_name = PINECONE_INDEX_NAME
    bm25_path = str(BM25_ENCODER_PKL)

    # Allow command-line override
    if len(sys.argv) > 1:
        documents_pkl = sys.argv[1]
    if len(sys.argv) > 2:
        index_name = sys.argv[2]

    # Check if documents file exists
    if not Path(documents_pkl).exists():
        print(f"❌ Documents file not found: {documents_pkl}")
        print(f"\nPlease run aurelia_to_langchain.py first to generate documents.")
        sys.exit(1)

    # Ask if should create new index
    if sys.stdin.isatty():
        create_new = input(f"\nCreate new index '{index_name}'? (yes/no) [no]: ").strip().lower() == 'yes'
    else:
        create_new = True

    try:
        # Update the function call to pass bm25_path
        index, bm25_encoder = upload_to_pinecone_hybrid(
            documents_pkl_path=documents_pkl,
            index_name=index_name,
            pinecone_api_key=PINECONE_API_KEY,
            openai_api_key=OPENAI_API_KEY,
            dimension=PINECONE_DIMENSION,
            create_new_index=create_new,
            save_bm25_encoder=True,
            bm25_save_path=bm25_path  # Add this parameter
        )
        print(f"\n{'=' * 80}")
        print(f"SUCCESS!")
        print(f"{'=' * 80}")
        print(f"\nNext steps:")
        print(f"1. Update financial_qa_system_hybrid.py to use:")
        print(f"   - Index: {index_name}")
        print(f"   - use_hybrid=True")
        print(f"2. The BM25 encoder has been saved for query-time use")
        print(f"3. Run the hybrid QA system to test!")

    except Exception as e:
        print(f"\n❌ Upload failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()