#!/usr/bin/env python3
"""
Simplified parser for Airflow DAG
Wraps the main parser logic
"""

import sys
from pathlib import Path


def parse_documents(markdown_dir: str, output_dir: str):
    """
    Parse markdown documents
    
    Args:
        markdown_dir: Directory containing markdown files
        output_dir: Directory for output files
    """
    # In production, this would import and run your actual parser
    # For now, this is a placeholder
    
    from pathlib import Path
    import json
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Simple parsing logic (replace with your actual parser)
    md_files = list(Path(markdown_dir).glob("*.md"))
    
    elements = []
    for idx, md_file in enumerate(md_files):
        with open(md_file, 'r') as f:
            content = f.read()
        
        elements.append({
            "page": idx + 1,
            "element_id": f"elem_{idx:04d}",
            "type": "text",
            "content": content[:500],  # First 500 chars
            "section": "General"
        })
    
    # Save JSONL
    jsonl_path = output_path / "parsed_enhanced.jsonl"
    with open(jsonl_path, 'w') as f:
        for elem in elements:
            f.write(json.dumps(elem) + '\n')
    
    print(f"✅ Parsed {len(elements)} elements")
    return str(jsonl_path)