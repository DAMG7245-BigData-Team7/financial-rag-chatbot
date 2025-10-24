#!/usr/bin/env python3
"""
RAG Service - Retrieval and Query Logic
"""

import os
import pickle
import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path

from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import Pinecone
from langchain_core.documents import Document
from pinecone import Pinecone as PineconeClient

logger = logging.getLogger(__name__)


class RAGService:
    """Retrieval-Augmented Generation service"""
    
    def __init__(
        self,
        pinecone_api_key: str,
        openai_api_key: str,
        index_name: str = "fintbx-hybrid-3072",
        use_hybrid: bool = True
    ):
        self.pinecone_api_key = pinecone_api_key
        self.openai_api_key = openai_api_key
        self.index_name = index_name
        self.use_hybrid = use_hybrid
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-large",
            api_key=openai_api_key
        )
        logger.info("✅ OpenAI embeddings initialized")
        
        # Initialize Pinecone client
        self.pc = PineconeClient(api_key=pinecone_api_key)
        self.index = self.pc.Index(index_name)
        logger.info(f"✅ Connected to Pinecone index: {index_name}")
        
        # Initialize vector store
        self.vector_store = Pinecone(
            index=self.index,
            embedding=self.embeddings,
            text_key="text"
        )
        logger.info("✅ Vector store initialized")
        
        logger.info("✅ RAG service ready")
    
    def retrieve_documents(
        self,
        query: str,
        top_k: int = 10,
        score_threshold: float = 0.7
    ) -> Tuple[List[Document], float]:
        """Retrieve relevant documents from Pinecone"""
        try:
            # Query vector store
            docs_with_scores = self.vector_store.similarity_search_with_score(
                query,
                k=top_k
            )
            
            if not docs_with_scores:
                logger.info(f"No documents found for: {query}")
                return [], 0.0
            
            documents = [doc for doc, score in docs_with_scores]
            scores = [score for doc, score in docs_with_scores]
            top_score = max(scores) if scores else 0.0
            
            logger.info(f"📊 Retrieved {len(documents)} docs (top score: {top_score:.3f})")
            
            return documents, top_score
            
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return [], 0.0
    
    def is_relevant(self, top_score: float, threshold: float = 0.7) -> bool:
        """Check if content is relevant"""
        return top_score >= threshold
    
    def extract_context(self, documents: List[Document], max_docs: int = 5) -> str:
        """Extract context from documents"""
        context_chunks = []
        
        for doc in documents[:max_docs]:
            page = doc.metadata.get('page', 'N/A')
            section = doc.metadata.get('section', 'Unknown')
            chunk = f"[Page {page} - {section}]\n{doc.page_content}"
            context_chunks.append(chunk)
        
        return "\n\n---\n\n".join(context_chunks)
    
    def get_source_citations(self, documents: List[Document], max_docs: int = 5) -> List[str]:
        """Get source citations"""
        citations = []
        for doc in documents[:max_docs]:
            page = doc.metadata.get('page', doc.metadata.get('page_number', 'unknown'))
            citations.append(f"page_{page}")
        
        return list(dict.fromkeys(citations))  # Remove duplicates
    
    def check_connection(self) -> bool:
        """Test Pinecone connection"""
        try:
            stats = self.index.describe_index_stats()
            logger.info(f"✅ Pinecone: {stats.total_vector_count} vectors")
            return True
        except Exception as e:
            logger.error(f"❌ Pinecone error: {e}")
            return False