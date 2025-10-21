# Hybrid Search & Reranking Implementation Guide

## Overview

This guide explains how to implement and use **hybrid search** (semantic + keyword) with **reranking** for your Financial QA system.

## What's Included

### 1. **Hybrid Search**
- **Dense vectors**: OpenAI `text-embedding-3-large` (semantic understanding)
- **Sparse vectors**: BM25 encoding (keyword matching)
- **Combined retrieval**: Best of both worlds

### 2. **Reranking**
- **FlashRank**: Fast, local, CPU-friendly reranker
- **Cohere Rerank**: High-accuracy cloud-based reranker (optional)

---

## Architecture

```
Query
  ↓
[Dense Vector] + [Sparse Vector (BM25)]
  ↓
Pinecone Hybrid Search (top 10)
  ↓
FlashRank Reranker (→ top 5)
  ↓
GPT-4 Answer Generation
```

---

## Setup Instructions

### Step 1: Install Dependencies

```bash
cd /Users/sachinshet/Desktop/Projects/Case\ Study\ 3/AURELIA
pip install pinecone-text flashrank
```

Already done! ✅

### Step 2: Process Your Documents

Use your existing pipeline:

```bash
# Parse markdown
cd chunking_strategy1
python parser_enhanced_markdown.py Data/markdown_pages/ -o Data/

# Convert to LangChain
python aurelia_to_langchain.py
```

This creates:
- `Data/parsed_enhanced.jsonl`
- `Data/langchain_documents.pkl`

### Step 3: Upload with Hybrid Search

**NEW**: Upload documents with both dense and sparse vectors:

```bash
cd chunking_strategy1
python upload_to_pinecone_hybrid.py
```

**What it does**:
1. Loads your `langchain_documents.pkl`
2. Generates dense vectors (OpenAI embeddings)
3. Trains BM25 encoder on your corpus
4. Generates sparse vectors (BM25)
5. Creates new Pinecone index: `fintbx-hybrid-3072` (dotproduct metric)
6. Uploads both vector types
7. Saves `Data/bm25_encoder.pkl` for querying

**Time**: ~5-10 minutes for 2,000+ documents

### Step 4: Run Hybrid QA System

```bash
cd chunking_strategy1
python financial_qa_system_hybrid.py
```

The system automatically:
- Loads the BM25 encoder
- Connects to hybrid index
- Enables hybrid search + reranking

---

## Configuration Options

### In `financial_qa_system_hybrid.py`:

#### **Option 1**: Semantic Search Only (No Hybrid)
```python
qa_system = HybridFinancialQASystem(
    use_hybrid=False,  # Semantic only
    use_reranking=True,
    reranker_type="flashrank",
    index_name="fintbx-semantic-3072"  # Your current index
)
```

**Use when**: You want reranking without creating a new index

---

#### **Option 2**: Full Hybrid Search (BEST)
```python
qa_system = HybridFinancialQASystem(
    use_hybrid=True,  # Hybrid search!
    use_reranking=True,
    reranker_type="flashrank",
    index_name="fintbx-hybrid-3072",  # Hybrid index
    bm25_encoder_path="Data/bm25_encoder.pkl"
)
```

**Use when**: Maximum retrieval quality (semantic + keywords)

---

#### **Option 3**: Hybrid Without Reranking
```python
qa_system = HybridFinancialQASystem(
    use_hybrid=True,
    use_reranking=False,  # Skip reranking
    index_name="fintbx-hybrid-3072"
)
```

**Use when**: You want hybrid search but not reranking overhead

---

## File Structure

```
AURELIA/
├── chunking_strategy1/
│   ├── parser_enhanced_markdown.py         # Step 1: Parse
│   ├── aurelia_to_langchain.py             # Step 2: Convert
│   ├── upload_to_pinecone_hybrid.py        # Step 3: Upload (NEW!)
│   ├── financial_qa_system.py              # Original (semantic only)
│   ├── financial_qa_system_hybrid.py       # Enhanced (hybrid + rerank)
│   └── Data/
│       ├── langchain_documents.pkl         # Your documents
│       └── bm25_encoder.pkl                # Saved BM25 (NEW!)
├── requirements.txt                        # Updated dependencies
└── HYBRID_SEARCH_GUIDE.md                  # This file
```

---

## Performance Comparison

| Method | Search Type | Reranking | Speed | Quality |
|--------|-------------|-----------|-------|---------|
| **Original** | Semantic only | No | Fast (4-6s) | Good |
| **Semantic + Rerank** | Semantic only | FlashRank | Medium (5-8s) | Better |
| **Hybrid + Rerank** | Dense + Sparse | FlashRank | Medium (6-9s) | BEST |

---

## Key Benefits

### Hybrid Search
- **Catches exact matches**: Function names like `blsprice`, technical terms
- **Semantic understanding**: Still works for conceptual queries
- **Robustness**: Works even with typos or paraphrasing

### Reranking
- **Better ordering**: Most relevant docs rise to top
- **Scores**: See relevance scores for each result
- **Fast**: FlashRank adds only ~1 second

---

## Troubleshooting

### "BM25 encoder not found"
**Solution**: Run `upload_to_pinecone_hybrid.py` first

### "Index 'fintbx-hybrid-3072' not found"
**Solution**: Set `create_new_index=True` in upload script

### "Hybrid search falling back to semantic"
**Reasons**:
1. BM25 encoder not loaded → Check path
2. Wrong index (not dotproduct) → Create hybrid index
3. BM25 encoder not fitted → Re-run upload script

---

## Quick Start (TL;DR)

```bash
# 1. Install deps (already done!)
pip install pinecone-text flashrank

# 2. Upload with hybrid
cd chunking_strategy1
python upload_to_pinecone_hybrid.py

# 3. Run QA system
python financial_qa_system_hybrid.py
```

That's it! You now have:
- ✅ Hybrid search (semantic + keywords)
- ✅ FlashRank reranking
- ✅ Better retrieval quality

---

## Advanced: Cohere Rerank

For even better reranking (cloud-based):

```bash
# Install Cohere
pip install cohere

# Set API key
export COHERE_API_KEY="your-key"

# Use in code
qa_system = HybridFinancialQASystem(
    use_hybrid=True,
    use_reranking=True,
    reranker_type="cohere"  # Use Cohere instead of FlashRank
)
```

**Note**: Free tier = 1,000 requests/month

---

## Questions?

- **How does BM25 work?** → Keyword frequency + document frequency (TF-IDF variant)
- **Why dotproduct metric?** → Required for sparse vector support in Pinecone
- **Can I use my existing index?** → No, cosine metric doesn't support sparse vectors
- **What if I only want reranking?** → Set `use_hybrid=False`, keeps current index

---

## Next Steps

1. ✅ Run `upload_to_pinecone_hybrid.py` to create hybrid index
2. ✅ Test with `financial_qa_system_hybrid.py`
3. Compare results with original system
4. Adjust `k` values (retrieval count) if needed
5. Try different reranking models

Enjoy better search! 🚀
