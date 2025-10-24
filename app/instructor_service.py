#!/usr/bin/env python3
"""
Instructor Integration - Structured Output Generation
"""

import os
import logging
from typing import List
from openai import OpenAI
import instructor
from app.models import ConceptNote

logger = logging.getLogger(__name__)


class InstructorService:
    """Generate structured ConceptNotes using instructor + OpenAI"""
    
    def __init__(self):
        """Initialize instructor client"""
        self.client = instructor.from_openai(
            OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        )
        logger.info("✅ Instructor service initialized")
    
    def generate_note_from_fintbx(
        self,
        concept: str,
        context_chunks: List[str]
    ) -> ConceptNote:
        """
        Generate structured note from Financial Toolbox context
        
        Args:
            concept: The financial concept name
            context_chunks: List of relevant text chunks from Pinecone
        
        Returns:
            Structured ConceptNote
        """
        
        # Combine context
        context = "\n\n---\n\n".join(context_chunks)
        
        # Generate structured output
        note = self.client.chat.completions.create(
            model="gpt-4o-mini",
            response_model=ConceptNote,
            messages=[
                {
                    "role": "system",
                    "content": """You are a financial expert creating structured concept notes from MATLAB Financial Toolbox documentation.

Generate comprehensive, accurate notes with:
- Clear definitions
- Key technical points
- MATLAB function names (if applicable)
- Code examples (if available in context)
- Mathematical formulas (if relevant)
- Related concepts

Be precise, technical, and cite specific information from the context."""
                },
                {
                    "role": "user",
                    "content": f"""Create a structured concept note for: {concept}

Context from Financial Toolbox documentation:
{context}

Generate a comprehensive note covering definition, key points, MATLAB functions, examples, and related concepts."""
                }
            ],
            temperature=0.2,  # Low temperature for consistency
            max_retries=3
        )
        
        logger.info(f"✅ Generated note for '{concept}' from fintbx.pdf")
        return note
    
    def generate_note_from_wikipedia(
        self,
        concept: str,
        wikipedia_content: str
    ) -> ConceptNote:
        """
        Generate structured note from Wikipedia content
        
        Args:
            concept: The financial concept name
            wikipedia_content: Wikipedia article text
        
        Returns:
            Structured ConceptNote
        """
        
        note = self.client.chat.completions.create(
            model="gpt-4o-mini",
            response_model=ConceptNote,
            messages=[
                {
                    "role": "system",
                    "content": """You are a financial expert creating structured concept notes from Wikipedia content.

Generate concise, finance-focused notes with:
- Clear definition
- Key points (focus on financial aspects)
- Related concepts
- Practical applications

Note: This is from Wikipedia, not Financial Toolbox, so matlab_functions and examples may not be applicable."""
                },
                {
                    "role": "user",
                    "content": f"""Create a structured concept note for: {concept}

Wikipedia Content:
{wikipedia_content}

Generate a concise note focusing on financial relevance."""
                }
            ],
            temperature=0.2,
            max_retries=3
        )
        
        logger.info(f"✅ Generated note for '{concept}' from Wikipedia")
        return note