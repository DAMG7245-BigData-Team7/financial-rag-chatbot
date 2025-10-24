#!/usr/bin/env python3
"""
AURELIA to LangChain Document Converter
Converts AURELIA JSONL output to LangChain Document format for hybrid RAG pipeline
"""

import sys
from pathlib import Path

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import PARSED_JSONL, LANGCHAIN_PKL, LANGCHAIN_SUMMARY

import json
import logging
import pickle
from typing import List, Dict, Any
from langchain.schema import Document

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AureliaToLangChainConverter:
    """Convert AURELIA JSONL output to LangChain Documents with rich metadata"""

    def __init__(self):
        self.element_priorities = {
            'code_block': 1,
            'equation': 2,
            'formula': 3,
            'table_block': 4,
            'text': 5
        }

    def load_aurelia_jsonl(self, jsonl_path: str) -> List[Dict[str, Any]]:
        """Load AURELIA JSONL output"""
        elements = []
        try:
            with open(jsonl_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line:
                        try:
                            element = json.loads(line)
                            elements.append(element)
                        except json.JSONDecodeError as e:
                            logger.warning(f"Skipping invalid JSON at line {line_num}: {e}")

            logger.info(f"Loaded {len(elements)} elements from {jsonl_path}")
            return elements

        except FileNotFoundError:
            logger.error(f"JSONL file not found: {jsonl_path}")
            return []
        except Exception as e:
            logger.error(f"Error loading JSONL: {e}")
            return []

    def convert_to_langchain_documents(self, aurelia_elements: List[Dict[str, Any]]) -> List[Document]:
        """Convert AURELIA elements to LangChain Documents with comprehensive metadata"""
        documents = []

        for element in aurelia_elements:
            try:
                # Extract core fields
                content = element.get('content', '').strip()
                if not content:
                    continue

                # Handle both AURELIA naming conventions
                element_type = element.get('type', element.get('element_type', 'text'))
                file_num = element.get('page', element.get('file_num', 0))
                section = element.get('section', 'unknown')

                # Create comprehensive metadata (Pinecone-compatible: all scalars)
                metadata = {
                    # Core AURELIA metadata
                    'element_type': element_type,
                    'type': element_type,  # Add 'type' field for backward compatibility
                    'page': int(file_num),  # Add 'page' field
                    'file_num': int(file_num),
                    'section': str(section),
                    'page_number': int(file_num),  # For compatibility

                    # Priority for retrieval ranking
                    'priority': int(self.element_priorities.get(element_type, 5)),

                    # Source information
                    'source': f"page_{file_num:03d}",
                    'document_section': str(section),

                    # Content characteristics
                    'content_length': int(len(content)),
                    'is_structured': bool(element_type in ['code_block', 'table_block', 'equation', 'formula']),

                    # NEW: Semantic hierarchy metadata (convert list to string for Pinecone)
                    'parent_id': str(element.get('parent_id')) if element.get('parent_id') else None,
                    'depth_level': int(element.get('depth_level')) if element.get('depth_level') is not None else None,
                    'section_breadcrumb': ' > '.join(element.get('section_path', [])) if element.get('section_path') else None,

                    # Element-specific metadata
                    **self._get_element_specific_metadata(element, element_type)
                }

                # Create LangChain Document
                doc = Document(
                    page_content=content,
                    metadata=metadata
                )

                documents.append(doc)

            except Exception as e:
                logger.warning(f"Error converting element to Document: {e}")
                continue

        logger.info(f"Converted {len(documents)} AURELIA elements to LangChain Documents")
        return documents

    def _get_element_specific_metadata(self, element: Dict[str, Any], element_type: str) -> Dict[str, Any]:
        """Add element-type specific metadata (all Pinecone-compatible scalars)"""
        specific_metadata = {}

        if element_type == 'code_block':
            content = element.get('content', '')
            specific_metadata.update({
                'language': str(self._detect_language(content)),
                'has_function_call': bool('(' in content and ')' in content),
                'has_assignment': bool('=' in content),
                'line_count': int(len(content.split('\n')))
            })

        elif element_type == 'table_block':
            content = element.get('content', '')
            specific_metadata.update({
                'table_format': str('markdown'),
                'has_headers': bool(content.startswith('|') and '---' in content),
                'row_count': int(len([l for l in content.split('\n') if l.strip().startswith('|')]))
            })

        elif element_type in ['equation', 'formula']:
            content = element.get('content', '')
            specific_metadata.update({
                'math_notation': str('latex' if '$' in content else 'text'),
                'has_variables': bool(any(c.islower() for c in content if c.isalpha())),
                'formula_length': int(len(content))
            })

        elif element_type == 'text':
            content = element.get('content', '')
            specific_metadata.update({
                'word_count': int(len(content.split())),
                'has_technical_terms': bool(any(term in content.lower() for term in ['matlab', 'function', 'algorithm', 'equation'])),
                'paragraph_count': int(len([p for p in content.split('\n\n') if p.strip()]))
            })

        # Add heading level if present
        if element_type == 'heading' and 'level' in element:
            specific_metadata['heading_level'] = int(element['level'])

        return specific_metadata

    def _detect_language(self, code_content: str) -> str:
        """Detect programming language from code content"""
        code_lower = code_content.lower()

        # MATLAB indicators
        matlab_indicators = ['function', 'end', '%', 'disp(', 'plot(', '=', 'matlab']
        if any(indicator in code_lower for indicator in matlab_indicators):
            if any(func in code_lower for func in ['blsprice', 'irr', 'npv', 'pvvar']):
                return 'matlab_financial'
            return 'matlab'

        # Python indicators
        python_indicators = ['def ', 'import ', 'print(', 'if __name__', 'class ']
        if any(indicator in code_lower for indicator in python_indicators):
            return 'python'

        # R indicators
        r_indicators = ['<-', 'library(', 'data.frame', 'ggplot']
        if any(indicator in code_lower for indicator in r_indicators):
            return 'r'

        return 'unknown'

    def get_conversion_stats(self, documents: List[Document]) -> Dict[str, Any]:
        """Get statistics about the converted documents"""
        if not documents:
            return {}

        stats = {
            'total_documents': len(documents),
            'element_type_counts': {},
            'language_counts': {},
            'total_content_length': 0,
            'structured_elements': 0,
            'pages_covered': set(),
            'average_content_length': 0
        }

        for doc in documents:
            metadata = doc.metadata
            element_type = metadata.get('element_type', 'unknown')

            # Count by element type
            stats['element_type_counts'][element_type] = stats['element_type_counts'].get(element_type, 0) + 1

            # Count by language (for code blocks)
            if element_type == 'code_block':
                language = metadata.get('language', 'unknown')
                stats['language_counts'][language] = stats['language_counts'].get(language, 0) + 1

            # Content statistics
            content_length = len(doc.page_content)
            stats['total_content_length'] += content_length

            # Structured elements
            if metadata.get('is_structured', False):
                stats['structured_elements'] += 1

            # Pages covered
            stats['pages_covered'].add(metadata.get('file_num', 0))

        # Calculate averages
        if stats['total_documents'] > 0:
            stats['average_content_length'] = stats['total_content_length'] / stats['total_documents']
            stats['pages_covered'] = len(stats['pages_covered'])

        return stats


def main():
    """Demo the AURELIA to LangChain conversion"""
    
    converter = AureliaToLangChainConverter()

    # Use paths from config
    jsonl_path = str(PARSED_JSONL)
    output_pkl = str(LANGCHAIN_PKL)
    summary_path = str(LANGCHAIN_SUMMARY)

    # Allow command-line override
    if len(sys.argv) > 1:
        jsonl_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_pkl = sys.argv[2]
        # Update summary path based on output_pkl
        summary_path = output_pkl.replace('.pkl', '_summary.json')

    print(f"Loading AURELIA JSONL output from: {jsonl_path}")
    
    # Check if input file exists
    if not Path(jsonl_path).exists():
        print(f"❌ Input file not found: {jsonl_path}")
        print(f"\nExpected location: {jsonl_path}")
        print(f"\nPlease run parser_enhanced_markdown.py first to generate the JSONL file.")
        print(f"\nExample:")
        print(f"  python chunking_strategy/parser_enhanced_markdown.py")
        return

    aurelia_elements = converter.load_aurelia_jsonl(jsonl_path)

    if not aurelia_elements:
        print("❌ No elements loaded. Please check the JSONL path.")
        return

    print(f"✅ Loaded {len(aurelia_elements)} AURELIA elements")

    print("\n🔄 Converting to LangChain Documents...")
    documents = converter.convert_to_langchain_documents(aurelia_elements)

    print(f"✅ Converted to {len(documents)} LangChain Documents")

    # Get conversion statistics
    stats = converter.get_conversion_stats(documents)

    print("\n" + "=" * 60)
    print("CONVERSION STATISTICS")
    print("=" * 60)
    print(f"Total Documents: {stats['total_documents']}")
    print(f"Pages Covered: {stats['pages_covered']}")
    print(f"Structured Elements: {stats['structured_elements']}")
    print(f"Average Content Length: {stats['average_content_length']:.1f} chars")

    print("\n📊 Element Type Distribution:")
    for element_type, count in sorted(stats['element_type_counts'].items()):
        percentage = (count / stats['total_documents']) * 100
        print(f"  {element_type}: {count} ({percentage:.1f}%)")

    if stats['language_counts']:
        print("\n💻 Code Language Distribution:")
        for language, count in sorted(stats['language_counts'].items()):
            print(f"  {language}: {count}")

    print("\n" + "=" * 60)
    print("SAMPLE DOCUMENTS")
    print("=" * 60)
    for i, doc in enumerate(documents[:3]):
        print(f"\n📄 Document {i+1}:")
        print(f"  Type: {doc.metadata['element_type']}")
        print(f"  Page: {doc.metadata['file_num']}")
        if doc.metadata.get('section_breadcrumb'):
            print(f"  Section: {doc.metadata['section_breadcrumb']}")
        if doc.metadata.get('parent_id'):
            print(f"  Parent: {doc.metadata['parent_id']}")
        print(f"  Content: {doc.page_content[:100]}...")
        print(f"  Metadata keys: {list(doc.metadata.keys())}")

    # Show hierarchy statistics
    print("\n" + "=" * 60)
    print("HIERARCHY STATISTICS")
    print("=" * 60)
    docs_with_hierarchy = sum(1 for doc in documents if doc.metadata.get('parent_id'))
    if docs_with_hierarchy > 0:
        print(f"Documents with parent relationships: {docs_with_hierarchy} ({docs_with_hierarchy/len(documents)*100:.1f}%)")
    else:
        print("No hierarchical relationships found")

    depth_counts = {}
    for doc in documents:
        depth = doc.metadata.get('depth_level', 0)
        if depth is None:
            depth = 0
        depth_counts[depth] = depth_counts.get(depth, 0) + 1

    if depth_counts:
        print(f"\n📊 Depth Distribution:")
        for depth in sorted(depth_counts.keys())[:5]:
            print(f"  Level {depth}: {depth_counts[depth]} documents")

    # Save documents to pickle file
    print("\n" + "=" * 60)
    print("SAVING DOCUMENTS")
    print("=" * 60)
    
    # Ensure output directory exists
    output_path = Path(output_pkl)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 Saving to: {output_pkl}")
    with open(output_pkl, 'wb') as f:
        pickle.dump(documents, f)
    print(f"✅ Saved {len(documents)} documents")

    # Save summary statistics
    print(f"📁 Saving summary to: {summary_path}")
    with open(summary_path, 'w') as f:
        # Convert sets to lists for JSON serialization
        stats_json = {k: list(v) if isinstance(v, set) else v for k, v in stats.items()}
        json.dump(stats_json, f, indent=2)
    print(f"✅ Saved summary")

    print("\n" + "=" * 60)
    print("SUCCESS! 🎉")
    print("=" * 60)
    print(f"\n📦 Output files created:")
    print(f"  1. {output_pkl}")
    print(f"  2. {summary_path}")
    print(f"\n🚀 Next step:")
    print(f"  Run: python chunking_strategy/upload_to_pinecone_hybrid.py")


if __name__ == "__main__":
    main()