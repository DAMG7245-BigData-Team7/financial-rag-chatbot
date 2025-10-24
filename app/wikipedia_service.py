#!/usr/bin/env python3
"""
Wikipedia Fallback Service
"""

import logging
import wikipedia
from typing import Optional, List

logger = logging.getLogger(__name__)


class WikipediaService:
    """Fetch and validate Wikipedia content as fallback"""
    
    def __init__(self):
        """Initialize Wikipedia service"""
        wikipedia.set_lang("en")
        logger.info("✅ Wikipedia service initialized")
    
    def fetch_content(self, concept: str, max_chars: int = 5000) -> Optional[str]:
        """
        Fetch Wikipedia content for a concept
        
        Args:
            concept: Concept to search for
            max_chars: Maximum characters to return
        
        Returns:
            Wikipedia content or None if not found
        """
        try:
            # Search for the page
            page = wikipedia.page(concept, auto_suggest=True)
            
            # Get summary + beginning of content
            content = page.summary
            
            # Add more content if summary is short
            if len(content) < 1000:
                full_content = page.content
                # Take first few paragraphs
                paragraphs = full_content.split('\n\n')[:5]
                content = '\n\n'.join(paragraphs)
            
            # Truncate if too long
            if len(content) > max_chars:
                content = content[:max_chars] + "..."
            
            logger.info(f"✅ Fetched Wikipedia content for '{concept}' ({len(content)} chars)")
            return content
            
        except wikipedia.exceptions.DisambiguationError as e:
            # Multiple pages found - try first option
            logger.warning(f"Disambiguation for '{concept}': {e.options[:3]}")
            try:
                page = wikipedia.page(e.options[0])
                return page.summary[:max_chars]
            except:
                logger.error(f"Failed to resolve disambiguation for '{concept}'")
                return None
                
        except wikipedia.exceptions.PageError:
            logger.warning(f"Wikipedia page not found for '{concept}'")
            return None
            
        except Exception as e:
            logger.error(f"Wikipedia error for '{concept}': {e}")
            return None
    
    def is_finance_related(self, concept: str) -> bool:
        """
        Check if a concept is finance-related
        
        Args:
            concept: Concept to check
        
        Returns:
            True if finance-related, False otherwise
        """
        try:
            page = wikipedia.page(concept, auto_suggest=True)
            
            # Financial keywords
            finance_keywords = [
                'finance', 'financial', 'investment', 'portfolio', 'bond',
                'stock', 'option', 'derivative', 'market', 'trading',
                'asset', 'equity', 'debt', 'security', 'capital',
                'interest', 'yield', 'return', 'risk', 'valuation',
                'pricing', 'hedging', 'arbitrage', 'swap', 'futures'
            ]
            
            # Check in summary and categories
            content_lower = (page.summary + ' '.join(page.categories)).lower()
            
            matches = sum(1 for kw in finance_keywords if kw in content_lower)
            
            # Need at least 2 finance keywords to be considered relevant
            is_relevant = matches >= 2
            
            if is_relevant:
                logger.info(f"✅ '{concept}' is finance-related ({matches} keywords)")
            else:
                logger.info(f"❌ '{concept}' is NOT finance-related ({matches} keywords)")
            
            return is_relevant
            
        except Exception as e:
            logger.error(f"Error checking finance relevance for '{concept}': {e}")
            return False
    
    def search(self, query: str, max_results: int = 5) -> List[str]:
        """
        Search Wikipedia for potential matches
        
        Args:
            query: Search query
            max_results: Maximum results to return
        
        Returns:
            List of page titles
        """
        try:
            results = wikipedia.search(query, results=max_results)
            logger.info(f"📝 Wikipedia search for '{query}': {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Wikipedia search error: {e}")
            return []