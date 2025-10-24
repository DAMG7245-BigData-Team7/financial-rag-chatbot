#!/usr/bin/env python3
"""
Database connection and operations for PostgreSQL
"""

import os
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON, ARRAY,text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager

logger = logging.getLogger(__name__)

Base = declarative_base()


class ConceptNoteDB(Base):
    """PostgreSQL table for concept notes"""
    __tablename__ = "concept_notes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    concept = Column(String(255), unique=True, nullable=False, index=True)
    note_json = Column(JSON, nullable=False)
    source = Column(String(50), nullable=False, index=True)  # 'fintbx' or 'wikipedia'
    sources_used = Column(ARRAY(Text), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Database:
    """Database manager for AURELIA"""
    
    def __init__(self, connection_string: str):
        """Initialize database connection"""
        self.engine = create_engine(
            connection_string,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,  # Verify connections before using
            echo=False  # Set to True for SQL debugging
        )
        self.SessionLocal = sessionmaker(bind=self.engine)
        logger.info("✅ Database engine created")
    
    def create_tables(self):
        """Create all tables if they don't exist"""
        Base.metadata.create_all(self.engine)
        logger.info("✅ Database tables created/verified")
    
    @contextmanager
    def get_session(self) -> Session:
        """Context manager for database sessions"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            session.close()
    
    def get_concept_note(self, concept: str) -> Optional[Dict[str, Any]]:
        """Retrieve a concept note from cache - returns dict instead of DB object"""
        with self.get_session() as session:
            note_obj = session.query(ConceptNoteDB).filter(
                ConceptNoteDB.concept == concept
            ).first()
        
            if not note_obj:
                return None
        
            # Convert to dictionary while still in session
            return {
                "note_json": note_obj.note_json,
                "source": note_obj.source,
                "sources_used": note_obj.sources_used,
                "created_at": note_obj.created_at,
                "updated_at": note_obj.updated_at
            }
    
    def save_concept_note(
        self,
        concept: str,
        note_json: Dict[str, Any],
        source: str,
        sources_used: List[str]
    ) -> ConceptNoteDB:
        """Save or update a concept note"""
        with self.get_session() as session:
            # Check if exists
            existing = session.query(ConceptNoteDB).filter(
                ConceptNoteDB.concept == concept
            ).first()
            
            if existing:
                # Update existing
                existing.note_json = note_json
                existing.source = source
                existing.sources_used = sources_used
                existing.updated_at = datetime.utcnow()
                logger.info(f"📝 Updated concept: {concept}")
                return existing
            else:
                # Create new
                new_note = ConceptNoteDB(
                    concept=concept,
                    note_json=note_json,
                    source=source,
                    sources_used=sources_used
                )
                session.add(new_note)
                logger.info(f"✨ Created new concept: {concept}")
                return new_note
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        with self.get_session() as session:
            total = session.query(ConceptNoteDB).count()
            
            # Count by source
            fintbx_count = session.query(ConceptNoteDB).filter(
                ConceptNoteDB.source == 'fintbx'
            ).count()
            
            wikipedia_count = session.query(ConceptNoteDB).filter(
                ConceptNoteDB.source == 'wikipedia'
            ).count()
            
            return {
                "total_cached_concepts": total,
                "source_breakdown": {
                    "fintbx": fintbx_count,
                    "wikipedia": wikipedia_count
                }
            }
    
    def delete_concept(self, concept: str) -> bool:
        """Delete a concept note"""
        with self.get_session() as session:
            deleted = session.query(ConceptNoteDB).filter(
                ConceptNoteDB.concept == concept
            ).delete()
            return deleted > 0
    
    def list_all_concepts(self) -> List[str]:
        """List all cached concept names"""
        with self.get_session() as session:
            results = session.query(ConceptNoteDB.concept).all()
            return [r[0] for r in results]
    
    def check_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False


# Initialize database connection from environment
def get_database() -> Database:
    """Get database instance from environment variables"""
    
    # Build connection string from environment
    db_host = os.getenv("DB_HOST")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_name = os.getenv("DB_NAME")
    
    connection_string = f"postgresql://{db_user}:{db_password}@{db_host}:5432/{db_name}"
    
    db = Database(connection_string)
    db.create_tables()  # Ensure tables exist
    
    return db