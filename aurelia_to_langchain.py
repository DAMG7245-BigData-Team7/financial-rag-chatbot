#!/usr/bin/env python3
"""
AURELIA to LangChain Document Converter
Converts AURELIA JSONL output to LangChain Document format for hybrid RAG pipeline
"""

import json
import logging
from typing import List, Dict, Any
from pathlib import Path
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

                # Create comprehensive metadata
                metadata = {
                    # Core AURELIA metadata
                    'element_type': element_type,
                    'file_num': file_num,
                    'section': section,
                    'page_number': file_num,  # For compatibility

                    # Priority for retrieval ranking
                    'priority': self.element_priorities.get(element_type, 5),

                    # Source information
                    'source': f"page_{file_num:03d}",
                    'document_section': section,

                    # Content characteristics
                    'content_length': len(content),
                    'is_structured': element_type in ['code_block', 'table_block', 'equation', 'formula'],

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
        """Add element-type specific metadata"""
        specific_metadata = {}

        if element_type == 'code_block':
            content = element.get('content', '')
            specific_metadata.update({
                'language': self._detect_language(content),
                'has_function_call': '(' in content and ')' in content,
                'has_assignment': '=' in content,
                'line_count': len(content.split('\n'))
            })

        elif element_type == 'table_block':
            content = element.get('content', '')
            specific_metadata.update({
                'table_format': 'markdown',
                'has_headers': content.startswith('|') and '---' in content,
                'row_count': len([l for l in content.split('\n') if l.strip().startswith('|')])
            })

        elif element_type in ['equation', 'formula']:
            content = element.get('content', '')
            specific_metadata.update({
                'math_notation': 'latex' if '$' in content else 'text',
                'has_variables': any(c.islower() for c in content if c.isalpha()),
                'formula_length': len(content)
            })

        elif element_type == 'text':
            content = element.get('content', '')
            specific_metadata.update({
                'word_count': len(content.split()),
                'has_technical_terms': any(term in content.lower() for term in ['matlab', 'function', 'algorithm', 'equation']),
                'paragraph_count': len([p for p in content.split('\n\n') if p.strip()])
            })

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

    # Convert the enhanced output
    jsonl_path = "/Users/sachinshet/Desktop/Projects/Case Study 3/AURELIA/enhanced_output_v11_sequential/fintbx_100_pages_enhanced.jsonl"

    print("Loading AURELIA JSONL output...")
    aurelia_elements = converter.load_aurelia_jsonl(jsonl_path)

    if not aurelia_elements:
        print("No elements loaded. Please check the JSONL path.")
        return

    print(f"Loaded {len(aurelia_elements)} AURELIA elements")

    print("Converting to LangChain Documents...")
    documents = converter.convert_to_langchain_documents(aurelia_elements)

    print(f"Converted to {len(documents)} LangChain Documents")

    # Get conversion statistics
    stats = converter.get_conversion_stats(documents)

    print("\n=== CONVERSION STATISTICS ===")
    print(f"Total Documents: {stats['total_documents']}")
    print(f"Pages Covered: {stats['pages_covered']}")
    print(f"Structured Elements: {stats['structured_elements']}")
    print(f"Average Content Length: {stats['average_content_length']:.1f} chars")

    print("\nElement Type Distribution:")
    for element_type, count in sorted(stats['element_type_counts'].items()):
        percentage = (count / stats['total_documents']) * 100
        print(f"  {element_type}: {count} ({percentage:.1f}%)")

    if stats['language_counts']:
        print("\nCode Language Distribution:")
        for language, count in sorted(stats['language_counts'].items()):
            print(f"  {language}: {count}")

    print("\n=== SAMPLE DOCUMENTS ===")
    for i, doc in enumerate(documents[:3]):
        print(f"\nDocument {i+1}:")
        print(f"Type: {doc.metadata['element_type']}")
        print(f"Page: {doc.metadata['file_num']}")
        print(f"Content: {doc.page_content[:100]}...")
        print(f"Metadata keys: {list(doc.metadata.keys())}")

if __name__ == "__main__":
    main()