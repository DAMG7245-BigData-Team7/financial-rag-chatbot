#!/usr/bin/env python3
"""
AURELIA FastAPI Service
Main API endpoints for concept note generation
"""

import os
import logging
import time
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
from typing import List

# Load environment variables from project root
root_dir = Path(__file__).parent.parent
env_path = root_dir / ".env"
load_dotenv(dotenv_path=env_path)

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.models import (
    QueryRequest, QueryResponse, SeedRequest, SeedResponse,
    HealthResponse, StatsResponse, ConceptNote, SourceType, SeedResult
)
from app.database import get_database
from app.rag_service import RAGService
from app.instructor_service import InstructorService
from app.wikipedia_service import WikipediaService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AURELIA API",
    description="Automated Financial Concept Note Generator",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
db = None
rag_service = None
instructor_service = None
wikipedia_service = None


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global db, rag_service, instructor_service, wikipedia_service
    
    import sys
    print("=" * 60, flush=True)
    print("🚀 AURELIA API STARTING...", flush=True)
    print("=" * 60, flush=True)
    print(f"Python version: {sys.version}", flush=True)
    
    try:
        print("\n📊 Initializing database...", flush=True)
        db = get_database()
        print("✅ Database connected", flush=True)
        
        print("\n🤖 Initializing RAG service...", flush=True)
        rag_service = RAGService(
            pinecone_api_key=os.getenv("PINECONE_API_KEY"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            index_name=os.getenv("PINECONE_INDEX_NAME", "fintbx-hybrid-3072"),
            use_hybrid=False
        )
        print("✅ RAG service initialized", flush=True)
        
        print("\n📝 Initializing instructor service...", flush=True)
        instructor_service = InstructorService()
        print("✅ Instructor initialized", flush=True)
        
        print("\n🌐 Initializing Wikipedia service...", flush=True)
        wikipedia_service = WikipediaService()
        print("✅ Wikipedia initialized", flush=True)
        
        print("\n" + "=" * 60, flush=True)
        print("🎉 AURELIA API READY!", flush=True)
        print("=" * 60, flush=True)
        
    except Exception as e:
        print(f"\n❌ STARTUP FAILED: {e}", flush=True, file=sys.stderr)
        import traceback
        traceback.print_exc()
        raise


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "AURELIA API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "query": "/query",
            "seed": "/seed",
            "stats": "/stats"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    
    # Check Pinecone connection
    pinecone_status = "connected" if rag_service and rag_service.check_connection() else "disconnected"
    
    # Check PostgreSQL connection
    postgres_status = "connected" if db and db.check_connection() else "disconnected"
    
    overall_status = "healthy" if (pinecone_status == "connected" and postgres_status == "connected") else "unhealthy"
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        pinecone=pinecone_status,
        postgres=postgres_status,
        components={
            "rag_service": "initialized" if rag_service else "not_initialized",
            "instructor": "initialized" if instructor_service else "not_initialized",
            "wikipedia": "initialized" if wikipedia_service else "not_initialized"
        }
    )


@app.post("/query", response_model=QueryResponse)
async def query_concept(request: QueryRequest):
    """
    Query for a concept note with intelligent fallback
    
    Process:
    1. Check PostgreSQL cache
    2. If not cached: Query Pinecone
    3. If found in fintbx.pdf: Generate from toolbox
    4. If not found: Fallback to Wikipedia
    5. Cache and return
    """
    
    logger.info(f"🔍 Query request for concept: {request.concept}")
    
    # STEP 1: Check cache (unless force_refresh)
    # STEP 1: Check cache (unless force_refresh)
    if not request.force_refresh:
        cached_note = db.get_concept_note(request.concept)
    
        if cached_note:
            logger.info(f"💾 Found cached note for '{request.concept}'")
        
             # Now cached_note is a dict, not a DB object
            return QueryResponse(
                concept=request.concept,
                note=ConceptNote(**cached_note["note_json"]),
                source=SourceType(cached_note["source"]),
                cached=True,
                cached_at=cached_note["created_at"],
                sources_used=cached_note["sources_used"] or []
            )
    
    # STEP 2: Query Pinecone for fintbx.pdf content
    logger.info(f"📊 Querying Pinecone for '{request.concept}'...")
    documents, top_score = rag_service.retrieve_documents(
        query=request.concept,
        top_k=10,
        score_threshold=0.4  # Lowered threshold
    )
    
    # STEP 3: Check if relevant content found
    if documents and rag_service.is_relevant(top_score, threshold=0.4):  # Lowered threshold
        # Content found in fintbx.pdf
        logger.info(f"✅ Relevant content found in fintbx.pdf (score: {top_score:.3f})")
        
        # Extract context
        context = rag_service.extract_context(documents, max_docs=5)
        
        # Get citations
        sources_used = rag_service.get_source_citations(documents, max_docs=5)
        
        # Generate structured note
        note = instructor_service.generate_note_from_fintbx(
            concept=request.concept,
            context_chunks=[context]
        )
        
        source = SourceType.FINTBX
        
    else:
        # STEP 4: Fallback to Wikipedia
        logger.info(f"⚠️ No relevant content in fintbx.pdf (score: {top_score:.3f})")
        logger.info(f"🌐 Attempting Wikipedia fallback for '{request.concept}'...")
        
        # Check if finance-related
        if not wikipedia_service.is_finance_related(request.concept):
            raise HTTPException(
                status_code=404,
                detail=f"Concept '{request.concept}' not found in Financial Toolbox and is not finance-related"
            )
        
        # Fetch Wikipedia content
        wiki_content = wikipedia_service.fetch_content(request.concept)
        
        if not wiki_content:
            raise HTTPException(
                status_code=404,
                detail=f"Concept '{request.concept}' not found in Financial Toolbox or Wikipedia"
            )
        
        # Generate note from Wikipedia
        note = instructor_service.generate_note_from_wikipedia(
            concept=request.concept,
            wikipedia_content=wiki_content
        )
        
        source = SourceType.WIKIPEDIA
        sources_used = [f"wikipedia:{request.concept}"]
    
    # STEP 5: Cache the generated note
    db.save_concept_note(
        concept=request.concept,
        note_json=note.dict(),
        source=source.value,
        sources_used=sources_used
    )
    
    logger.info(f"✅ Generated and cached note for '{request.concept}' from {source.value}")
    
    # STEP 6: Return response
    return QueryResponse(
        concept=request.concept,
        note=note,
        source=source,
        cached=False,
        generated_at=datetime.utcnow(),
        sources_used=sources_used,
        relevance_score=top_score if source == SourceType.FINTBX else None
    )


@app.post("/seed", response_model=SeedResponse)
async def seed_concepts(request: SeedRequest):
    """
    Seed database with concept notes from fintbx.pdf
    
    Called by Airflow DAG to pre-generate concept notes
    """
    
    logger.info(f"🌱 Seed request for {len(request.concepts)} concepts")
    
    start_time = time.time()
    
    results = {
        "total": len(request.concepts),
        "seeded": 0,
        "skipped": 0,
        "failed": 0,
        "details": []
    }
    
    for concept in request.concepts:
        try:
            logger.info(f"Processing concept: {concept}")
            
            # Check if already cached (unless overwrite)
            if not request.overwrite:
                existing = db.get_concept_note(concept)
                if existing:
                    logger.info(f"⏭️  Skipping '{concept}' - already cached")
                    results["skipped"] += 1
                    results["details"].append(SeedResult(
                        concept=concept,
                        status="skipped",
                        reason="already_cached"
                    ))
                    continue
            
            # Query Pinecone
            documents, top_score = rag_service.retrieve_documents(
                query=concept,
                top_k=10,
                score_threshold=0.4  # Lowered threshold
            )
            
            # Check if relevant content found
            if not documents or not rag_service.is_relevant(top_score, threshold=0.4):  # Lowered threshold
                logger.info(f"⏭️  Skipping '{concept}' - no relevant content (score: {top_score:.3f})")
                results["skipped"] += 1
                results["details"].append(SeedResult(
                    concept=concept,
                    status="skipped",
                    reason="no_relevant_content",
                    score=top_score
                ))
                continue
            
            # Extract context and generate note
            context = rag_service.extract_context(documents, max_docs=5)
            sources_used = rag_service.get_source_citations(documents, max_docs=5)
            
            note = instructor_service.generate_note_from_fintbx(
                concept=concept,
                context_chunks=[context]
            )
            
            # Save to database
            db.save_concept_note(
                concept=concept,
                note_json=note.dict(),
                source="fintbx",
                sources_used=sources_used
            )
            
            logger.info(f"✅ Seeded '{concept}' (score: {top_score:.3f})")
            results["seeded"] += 1
            results["details"].append(SeedResult(
                concept=concept,
                status="seeded",
                score=top_score,
                sources_count=len(documents)
            ))
            
            # Rate limiting
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"❌ Failed to seed '{concept}': {e}")
            results["failed"] += 1
            results["details"].append(SeedResult(
                concept=concept,
                status="failed",
                error=str(e)
            ))
    
    duration = time.time() - start_time
    
    logger.info(f"🌱 Seeding complete: {results['seeded']}/{results['total']} seeded in {duration:.1f}s")
    
    return SeedResponse(
        total=results["total"],
        seeded=results["seeded"],
        skipped=results["skipped"],
        failed=results["failed"],
        details=results["details"],
        duration_seconds=duration
    )


@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get system statistics"""
    
    stats = db.get_stats()
    
    return StatsResponse(
        total_cached_concepts=stats["total_cached_concepts"],
        source_breakdown=stats["source_breakdown"],
        recent_queries=0,
        cache_hit_rate=None
    )


@app.delete("/cache/{concept}")
async def delete_cached_concept(concept: str):
    """Delete a cached concept note"""
    
    deleted = db.delete_concept(concept)
    
    if deleted:
        return {"message": f"Deleted cached note for '{concept}'"}
    else:
        raise HTTPException(status_code=404, detail=f"Concept '{concept}' not found in cache")


@app.get("/cache")
async def list_cached_concepts():
    """List all cached concepts"""
    
    concepts = db.list_all_concepts()
    
    return {
        "total": len(concepts),
        "concepts": sorted(concepts)
    }