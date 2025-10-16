#!/usr/bin/env python3
"""
FastAPI Backend for AURELIA Financial QA System
RESTful API for the Lab 1 chatbot interface
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import os
import time
import logging
from contextlib import asynccontextmanager

# Import our QA system
from financial_qa_system import FinancialQASystem

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global QA system instance
qa_system = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize QA system on startup"""
    global qa_system

    logger.info("🚀 Initializing AURELIA Financial QA System...")

    try:
        qa_system = FinancialQASystem()

        if qa_system.ready:
            logger.info("✅ QA System initialized successfully")
            logger.info(f"📊 Ready to serve financial questions")
        else:
            logger.error("❌ QA System failed to initialize")
            qa_system = None

    except Exception as e:
        logger.error(f"❌ Failed to initialize QA system: {e}")
        qa_system = None

    yield

    # Cleanup (if needed)
    logger.info("🔄 Shutting down QA system...")

# Create FastAPI app
app = FastAPI(
    title="AURELIA Financial QA API",
    description="RESTful API for financial document question-answering using Lab 1 AURELIA + Pinecone system",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for API
class QuestionRequest(BaseModel):
    question: str
    filter_type: Optional[str] = None  # "code", "tables", "matlab", etc.
    page_start: Optional[int] = None
    page_end: Optional[int] = None

class Source(BaseModel):
    rank: int
    element_type: str
    page_number: float
    section: str
    content_preview: str
    chunking_strategy: Optional[str] = None

class QuestionResponse(BaseModel):
    question: str
    answer: str
    sources: List[Source]
    processing_time: float
    timestamp: float
    filter_applied: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    system_ready: bool
    corpus_info: Dict
    timestamp: float

class StatsResponse(BaseModel):
    total_vectors: int
    element_distribution: Dict[str, int]
    available_filters: List[str]
    system_info: Dict

# API Endpoints

@app.get("/", response_model=Dict)
async def root():
    """Root endpoint - API information"""
    return {
        "message": "AURELIA Financial QA API",
        "version": "1.0.0",
        "description": "Ask questions about financial documents and MATLAB Financial Toolbox",
        "endpoints": {
            "health": "/health",
            "ask": "/ask",
            "stats": "/stats",
            "suggestions": "/suggestions"
        },
        "corpus": "2,124+ financial document chunks with structure-aware processing"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""

    corpus_info = {
        "total_documents": "2,124+",
        "source": "MATLAB Financial Toolbox",
        "structure_preservation": "100% for code and tables",
        "embedding_model": "text-embedding-3-large",
        "vector_database": "Pinecone"
    }

    return HealthResponse(
        status="healthy" if qa_system and qa_system.ready else "unhealthy",
        system_ready=qa_system is not None and qa_system.ready,
        corpus_info=corpus_info,
        timestamp=time.time()
    )

@app.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """Ask a question to the financial QA system"""

    if not qa_system or not qa_system.ready:
        raise HTTPException(
            status_code=503,
            detail="QA system not available. Please check system health."
        )

    start_time = time.time()

    try:
        # Build filter if specified
        element_filter = None
        filter_description = None

        if request.filter_type:
            if request.filter_type == "code":
                element_filter = {"element_type": "code_block"}
                filter_description = "code blocks only"
            elif request.filter_type == "matlab":
                element_filter = {"element_type": "code_block", "language": "matlab"}
                filter_description = "MATLAB code only"
            elif request.filter_type == "matlab_financial":
                element_filter = {"element_type": "code_block", "language": "matlab_financial"}
                filter_description = "MATLAB financial functions only"
            elif request.filter_type == "tables":
                element_filter = {"element_type": "table_block"}
                filter_description = "tables only"
            elif request.filter_type == "text":
                element_filter = {"element_type": "text"}
                filter_description = "text explanations only"

        # Add page range filter
        if request.page_start is not None and request.page_end is not None:
            page_filter = {"page_number": {"$gte": request.page_start, "$lte": request.page_end}}
            if element_filter:
                element_filter.update(page_filter)
            else:
                element_filter = page_filter
            filter_description = f"pages {request.page_start}-{request.page_end}" + (f", {filter_description}" if filter_description else "")

        # Get answer from QA system
        if element_filter:
            # Use filtered search
            relevant_docs = qa_system.vector_store.similarity_search(
                request.question,
                k=5,
                filter=element_filter
            )

            if not relevant_docs:
                raise HTTPException(
                    status_code=404,
                    detail=f"No relevant documents found with filter: {filter_description}"
                )

            # Create context and get LLM response
            context = "\n\n".join([doc.page_content for doc in relevant_docs])
            response = qa_system.llm.invoke(
                qa_system.prompt_template.format(context=context, question=request.question)
            )
            answer = response.content
            source_docs = relevant_docs

        else:
            # Use full QA chain
            result = qa_system.qa_chain.invoke({"query": request.question})
            answer = result["result"]
            source_docs = result["source_documents"]

        # Format sources
        sources = []
        for i, doc in enumerate(source_docs, 1):
            source = Source(
                rank=i,
                element_type=doc.metadata.get('element_type', 'unknown'),
                page_number=doc.metadata.get('page_number', 0),
                section=doc.metadata.get('section', 'Unknown section'),
                content_preview=doc.page_content[:150].replace('\n', ' ') + "...",
                chunking_strategy=doc.metadata.get('chunking_strategy', 'unknown')
            )
            sources.append(source)

        processing_time = time.time() - start_time

        return QuestionResponse(
            question=request.question,
            answer=answer,
            sources=sources,
            processing_time=processing_time,
            timestamp=time.time(),
            filter_applied=filter_description
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")

@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get system statistics"""

    if not qa_system or not qa_system.ready:
        raise HTTPException(status_code=503, detail="QA system not available")

    try:
        # Get a sample of documents to analyze distribution
        sample_docs = qa_system.vector_store.similarity_search("financial", k=100)

        element_distribution = {}
        for doc in sample_docs:
            element_type = doc.metadata.get('element_type', 'unknown')
            element_distribution[element_type] = element_distribution.get(element_type, 0) + 1

        return StatsResponse(
            total_vectors=2124,  # From our known corpus size
            element_distribution=element_distribution,
            available_filters=["code", "matlab", "matlab_financial", "tables", "text"],
            system_info={
                "embedding_model": "text-embedding-3-large",
                "vector_database": "Pinecone",
                "chunking_strategy": "AURELIA Hybrid",
                "structure_preservation": "100%"
            }
        )

    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")

@app.get("/suggestions", response_model=List[str])
async def get_suggestions():
    """Get suggested questions"""

    suggestions = [
        "What is the Black-Scholes model and how is it implemented?",
        "How do I calculate the internal rate of return using MATLAB?",
        "What portfolio optimization functions are available?",
        "Show me examples of the blsprice function",
        "How do I implement Monte Carlo simulation for options?",
        "What are the main risk management functions?",
        "How do I create and analyze yield curves?",
        "What credit risk models are available?",
        "How do I calculate Value at Risk (VaR)?",
        "Show me MATLAB code for portfolio optimization",
        "What are the Greeks in option pricing?",
        "How do I model interest rate derivatives?",
        "What bond pricing functions are available?",
        "How do I perform stress testing?",
        "What are the different volatility models?"
    ]

    return suggestions

# Additional utility endpoints

@app.get("/search/{element_type}")
async def search_by_type(element_type: str, query: str = "financial"):
    """Search for specific element types"""

    valid_types = ["code", "matlab", "matlab_financial", "tables", "text"]

    if element_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid element type. Must be one of: {valid_types}"
        )

    request = QuestionRequest(question=query, filter_type=element_type)
    return await ask_question(request)

@app.get("/pages/{start_page}/{end_page}")
async def search_page_range(start_page: int, end_page: int, query: str = "financial"):
    """Search within specific page range"""

    if start_page < 1 or end_page > 100 or start_page > end_page:
        raise HTTPException(
            status_code=400,
            detail="Invalid page range. Pages must be between 1-100 and start <= end"
        )

    request = QuestionRequest(question=query, page_start=start_page, page_end=end_page)
    return await ask_question(request)

if __name__ == "__main__":
    import uvicorn

    print("🚀 Starting AURELIA Financial QA API Server")
    print("📊 Serving Lab 1 corpus with 2,124+ financial documents")
    print("🔗 API will be available at: http://localhost:8000")
    print("📖 Interactive docs at: http://localhost:8000/docs")

    uvicorn.run(
        "backend:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["."],
        log_level="info"
    )