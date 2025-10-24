#!/usr/bin/env python3
"""
Parser wrapper that uses the full AURELIA parser
"""

import sys
from pathlib import Path

# Add dags directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from parser_enhanced_markdown import EnhancedMarkdownParser


def parse_documents(markdown_dir: str, output_dir: str):
    """
    Parse markdown documents using the full AURELIA parser
    
    Args:
        markdown_dir: Directory containing markdown files
        output_dir: Directory for output files
    
    Returns:
        Path to output directory
    """
    print(f"🔎 Using EnhancedMarkdownParser...")
    print(f"   Input:  {markdown_dir}")
    print(f"   Output: {output_dir}")
    
    # Use the real parser
    parser = EnhancedMarkdownParser(
        markdown_dir=markdown_dir,
        output_dir=output_dir
    )
    
    # Run extraction
    parser.extract()
    
    print(f"✅ Parsing complete using full AURELIA parser")
    print(f"   Total elements: {len(parser.elements)}")
    
    return output_dir