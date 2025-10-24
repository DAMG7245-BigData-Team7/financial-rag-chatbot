#!/usr/bin/env python3
"""
Parser for individual markdown page files (Airflow format)
"""

import json
import re
from pathlib import Path


def parse_documents(markdown_dir: str, output_dir: str):
    """
    Parse markdown files - handles INDIVIDUAL page files from PDF conversion
    
    Task 2 creates: page_001.md, page_002.md, ...
    Each file = one PDF page (no internal --- separators)
    """
    print("=" * 60)
    print("PARSING MARKDOWN PAGE FILES")
    print("=" * 60)
    
    markdown_path = Path(markdown_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Get all markdown files
    md_files = sorted(markdown_path.glob("*.md"))
    
    if not md_files:
        raise FileNotFoundError(f"No markdown files in {markdown_dir}")
    
    print(f"📁 Found {len(md_files)} markdown files")
    
    elements = []
    element_counter = 0
    
    # Process each markdown file (each file = one page)
    for file_idx, md_file in enumerate(md_files, start=1):
        if file_idx % 500 == 0 or file_idx == 1:
            print(f"   Processing {file_idx}/{len(md_files)}...")
        
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.strip() or len(content) < 50:
                continue  # Skip empty/tiny files
            
            # Each file is ONE page - extract elements from it
            page_num = file_idx
            
            # Simple extraction: split into chunks
            lines = content.split('\n')
            current_text = []
            in_code_block = False
            code_lines = []
            
            for line in lines:
                line_stripped = line.strip()
                
                # Code block markers
                if line_stripped.startswith('```'):
                    if in_code_block:
                        # End code block
                        if code_lines:
                            element_counter += 1
                            elements.append({
                                "page": page_num,
                                "element_id": f"elem_{element_counter:06d}",
                                "type": "code_block",
                                "content": '\n'.join(code_lines),
                                "section": "Code"
                            })
                        code_lines = []
                        in_code_block = False
                    else:
                        # Start code block - flush text
                        if current_text:
                            text_content = '\n'.join(current_text).strip()
                            if len(text_content) > 30:
                                element_counter += 1
                                elements.append({
                                    "page": page_num,
                                    "element_id": f"elem_{element_counter:06d}",
                                    "type": "text",
                                    "content": text_content,
                                    "section": "General"
                                })
                            current_text = []
                        in_code_block = True
                
                elif in_code_block:
                    code_lines.append(line)
                else:
                    # Detect tables
                    if '|' in line_stripped and line_stripped.count('|') >= 2:
                        # Flush text, add table line as element
                        if current_text:
                            text_content = '\n'.join(current_text).strip()
                            if len(text_content) > 30:
                                element_counter += 1
                                elements.append({
                                    "page": page_num,
                                    "element_id": f"elem_{element_counter:06d}",
                                    "type": "text",
                                    "content": text_content,
                                    "section": "General"
                                })
                            current_text = []
                        
                        element_counter += 1
                        elements.append({
                            "page": page_num,
                            "element_id": f"elem_{element_counter:06d}",
                            "type": "table_block",
                            "content": line_stripped,
                            "section": "Tables"
                        })
                    else:
                        current_text.append(line)
            
            # Flush remaining text for this page
            if current_text:
                text_content = '\n'.join(current_text).strip()
                if len(text_content) > 30:
                    element_counter += 1
                    elements.append({
                        "page": page_num,
                        "element_id": f"elem_{element_counter:06d}",
                        "type": "text",
                        "content": text_content,
                        "section": "General"
                    })
        
        except Exception as e:
            print(f"⚠️  Error processing {md_file.name}: {e}")
            continue
    
    # Save JSONL
    jsonl_path = output_path / "markdown_enhanced.jsonl"
    
    print(f"\n💾 Saving elements...")
    print(f"   Total markdown files: {len(md_files)}")
    print(f"   Total elements extracted: {len(elements)}")
    
    if len(elements) == 0:
        raise ValueError(
            f"Parser extracted 0 elements from {len(md_files)} files! "
            f"Check markdown file format."
        )
    
    with open(jsonl_path, 'w', encoding='utf-8') as f:
        for elem in elements:
            f.write(json.dumps(elem, ensure_ascii=False) + '\n')
    
    file_size = jsonl_path.stat().st_size
    print(f"   ✅ JSONL created: {jsonl_path}")
    print(f"   File size: {file_size:,} bytes")
    
    # Create stats file
    stats_path = output_path / "markdown_enhanced_stats.json"
    stats = {
        "total_elements": len(elements),
        "total_files_processed": len(md_files),
        "element_types": {}
    }
    
    for elem in elements:
        elem_type = elem.get('type', 'unknown')
        stats['element_types'][elem_type] = stats['element_types'].get(elem_type, 0) + 1
    
    with open(stats_path, 'w') as f:
        json.dump(stats, f, indent=2)
    
    print(f"\n📊 Statistics:")
    for elem_type, count in stats['element_types'].items():
        print(f"   {elem_type}: {count}")
    
    print("=" * 60)
    print("✅ PARSING COMPLETE")
    print("=" * 60)
    
    return str(output_dir)