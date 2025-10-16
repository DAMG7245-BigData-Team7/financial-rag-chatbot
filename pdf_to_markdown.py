#!/usr/bin/env python3
"""
PDF to Markdown Converter with Enhanced Table Support
Converts PDF documents to markdown format, preserving tables, text, and structure.
FIXED VERSION: Always preserves all content
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
import re

# Primary extraction libraries
import pymupdf  # Also known as fitz
import pdfplumber
from tabulate import tabulate
import pandas as pd

# Optional: For enhanced extraction
try:
    from docling.document_converter import DocumentConverter
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PDFToMarkdownConverter:
    """Convert PDF documents to Markdown format with table preservation."""
    
    def __init__(self, pdf_path: str, output_dir: Optional[str] = None):
        """
        Initialize the converter.
        
        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory for output markdown files (default: same as PDF)
        """
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        self.output_dir = Path(output_dir) if output_dir else self.pdf_path.parent
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def extract_with_pymupdf(self) -> Dict[int, str]:
        """
        Extract text and tables using PyMuPDF.
        
        Returns:
            Dictionary mapping page numbers to markdown content
        """
        pages_markdown = {}
        
        try:
            doc = pymupdf.open(self.pdf_path)
            
            for page_num, page in enumerate(doc, 1):
                markdown_content = f"# Page {page_num}\n\n"
                
                # Extract all text first - ALWAYS keep this
                full_text = page.get_text()
                
                # Always add the full text
                if full_text:
                    markdown_content += self._format_text_to_markdown(full_text)
                
                # Try to extract tables and add them separately
                try:
                    tabs = page.find_tables()
                    if tabs and tabs.tables:
                        logger.info(f"Found {len(tabs.tables)} tables on page {page_num}")
                        markdown_content += "\n\n## Extracted Tables\n\n"
                        
                        for table_idx, tab in enumerate(tabs.tables):
                            try:
                                table_data = tab.extract()
                                if table_data and any(table_data):
                                    markdown_content += f"\n### Table {table_idx + 1}\n\n"
                                    markdown_content += self._table_to_markdown(table_data)
                                    markdown_content += "\n\n"
                            except Exception as e:
                                logger.debug(f"Error extracting table {table_idx}: {e}")
                                
                except AttributeError as e:
                    logger.debug(f"PyMuPDF table extraction not available: {e}")
                
                pages_markdown[page_num] = markdown_content
                
            doc.close()
            
        except Exception as e:
            logger.error(f"Error with PyMuPDF extraction: {e}")
            
        return pages_markdown
    
    def extract_with_pdfplumber(self) -> Dict[int, str]:
        """
        Extract text and tables using pdfplumber (better for tables).
        Replaces table content inline with properly formatted markdown tables.

        Returns:
            Dictionary mapping page numbers to markdown content
        """
        pages_markdown = {}

        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    markdown_content = f"# Page {page_num}\n\n"

                    # Extract all text from the page
                    full_text = page.extract_text()

                    # Extract tables
                    tables = page.extract_tables()

                    if tables and full_text:
                        logger.info(f"Found {len(tables)} tables on page {page_num}")

                        # Replace table content inline with formatted tables
                        processed_text = self._replace_tables_inline(full_text, tables)
                        markdown_content += self._format_text_to_markdown(processed_text)

                    else:
                        # No tables found - just use all text
                        if full_text:
                            markdown_content += self._format_text_to_markdown(full_text)

                    pages_markdown[page_num] = markdown_content

        except Exception as e:
            logger.error(f"Error with pdfplumber extraction: {e}")

        return pages_markdown
    
    def _replace_tables_inline(self, full_text: str, tables: List[List]) -> str:
        """
        Replace table content in text with properly formatted markdown tables.

        Args:
            full_text: The complete text from the page
            tables: List of extracted tables

        Returns:
            Text with table content replaced by formatted markdown tables
        """
        if not tables or not full_text:
            return full_text

        processed_text = full_text

        for table_idx, table in enumerate(tables):
            if not table or not any(table):
                continue

            # Create the formatted markdown table
            formatted_table = self._table_to_markdown(table)
            if not formatted_table:
                continue

            # Find the table content in the text
            table_start_line = None
            table_lines = []

            # Get representative content from the first few rows to identify table location
            for row_idx, row in enumerate(table[:3]):  # Check first 3 rows
                if row and any(str(cell).strip() for cell in row if cell is not None):
                    row_content = [str(cell).strip() for cell in row if cell is not None and str(cell).strip()]
                    if row_content:
                        table_lines.extend(row_content)

            if not table_lines:
                continue

            # Find where this table appears in the text
            lines = processed_text.split('\n')
            table_region_start = None
            table_region_end = None

            # Look for lines that contain table content
            for line_idx, line in enumerate(lines):
                line_clean = line.strip().lower()
                if not line_clean:
                    continue

                # Check if this line contains table content
                matches = 0
                for table_content in table_lines:
                    if table_content.lower() in line_clean:
                        matches += 1

                if matches > 0:
                    if table_region_start is None:
                        table_region_start = line_idx
                    table_region_end = line_idx

            # Replace the table region with formatted table
            if table_region_start is not None and table_region_end is not None:
                # Keep lines before table
                before_table = lines[:table_region_start]
                # Keep lines after table
                after_table = lines[table_region_end + 1:]

                # Insert the formatted table
                new_lines = before_table + [formatted_table] + after_table
                processed_text = '\n'.join(new_lines)

                # Update lines for next table processing
                lines = processed_text.split('\n')

        return processed_text

    def _is_likely_table_row(self, line: str) -> bool:
        """
        Determine if a line is likely part of a table.
        
        Args:
            line: Text line to check
            
        Returns:
            True if line appears to be table content
        """
        if not line.strip():
            return False
        
        # Count indicators of table-like content
        indicators = 0
        
        # Multiple consecutive spaces or tabs (column separation)
        if '  ' in line or '\t' in line:
            indicators += 1
        
        # Multiple numbers separated by spaces (data columns)
        numbers = re.findall(r'\b\d+\.?\d*\b', line)
        if len(numbers) >= 3:
            indicators += 1
        
        # Pipe separators (markdown tables)
        if line.count('|') >= 2:
            indicators += 2
        
        # High ratio of special characters used in tables
        special_chars = line.count('|') + line.count('\t') + line.count('  ')
        if len(line) > 0 and special_chars / len(line) > 0.1:
            indicators += 1
        
        # Dollar signs, percentages (financial data)
        if '$' in line or '%' in line:
            if len(numbers) >= 2:
                indicators += 1
        
        return indicators >= 2
    
    def _table_to_markdown(self, table_data: List[List]) -> str:
        """
        Convert table data to markdown format with better handling.
        
        Args:
            table_data: 2D list representing table rows and columns
            
        Returns:
            Markdown formatted table string
        """
        if not table_data or not any(table_data):
            return ""
        
        # Filter out completely empty rows
        table_data = [row for row in table_data if row and any(str(cell).strip() if cell is not None else '' for cell in row)]
        
        if not table_data:
            return ""
        
        # Clean and normalize table data
        cleaned_table = []
        max_cols = max(len(row) for row in table_data)
        
        for row in table_data:
            cleaned_row = []
            for i in range(max_cols):
                if i < len(row) and row[i] is not None:
                    # Clean cell content
                    cell_text = str(row[i]).strip()
                    # Replace newlines with spaces
                    cell_text = ' '.join(cell_text.split())
                    # Escape pipe characters
                    cell_text = cell_text.replace('|', '\\|')
                    # Limit cell width for readability
                    if len(cell_text) > 100:
                        cell_text = cell_text[:97] + '...'
                    cleaned_row.append(cell_text)
                else:
                    cleaned_row.append("")
            
            # Only add non-empty rows
            if any(cell for cell in cleaned_row):
                cleaned_table.append(cleaned_row)
        
        if not cleaned_table:
            return ""
        
        # Create markdown table
        markdown_lines = []
        
        # Header row
        header = cleaned_table[0]
        markdown_lines.append('| ' + ' | '.join(header) + ' |')
        
        # Separator row with alignment
        separator = ['---'] * len(header)
        markdown_lines.append('| ' + ' | '.join(separator) + ' |')
        
        # Data rows
        for row in cleaned_table[1:]:
            # Ensure row has same number of columns as header
            while len(row) < len(header):
                row.append('')
            row = row[:len(header)]  # Trim if too long
            markdown_lines.append('| ' + ' | '.join(row) + ' |')
        
        return '\n'.join(markdown_lines)
    
    def _format_text_to_markdown(self, text: str) -> str:
        """
        Format extracted text to markdown with improved formatting.
        NOTE: No longer filters out table-like content to preserve all text.
        
        Args:
            text: Raw text from PDF
            
        Returns:
            Formatted markdown text
        """
        if not text:
            return ""
        
        # Clean up text
        lines = text.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # DON'T skip lines that look like table data - we want to keep everything
            
            # Detect potential headers (all caps, short lines)
            if line.isupper() and len(line) < 60 and not line[0].isdigit():
                formatted_lines.append(f"\n### {line.title()}\n")
            # Detect subheaders
            elif re.match(r'^(\d+\.?\s+)?[A-Z][^.!?]*$', line) and len(line) < 60:
                if line[0].isdigit():
                    formatted_lines.append(f"\n#### {line}\n")
                elif len(formatted_lines) == 0 or formatted_lines[-1] == '':
                    formatted_lines.append(f"\n#### {line}\n")
                else:
                    formatted_lines.append(line)
            # Detect bullet points
            elif re.match(r'^[•●○◦▪▫◊→➤\-\*]\s+', line):
                bullet_text = re.sub(r'^[•●○◦▪▫◊→➤\-\*]\s+', '', line)
                formatted_lines.append(f"- {bullet_text}")
            # Detect numbered lists
            elif re.match(r'^\d+[\.\)]\s+', line):
                formatted_lines.append(line)
            else:
                formatted_lines.append(line)
        
        # Join lines with appropriate spacing
        result = []
        for i, line in enumerate(formatted_lines):
            result.append(line)
            # Add paragraph breaks between non-list items
            if i < len(formatted_lines) - 1:
                curr_is_list = line.startswith(('-', '*')) or re.match(r'^\d+[\.\)]', line)
                next_is_list = formatted_lines[i+1].startswith(('-', '*')) or re.match(r'^\d+[\.\)]', formatted_lines[i+1])
                curr_is_header = line.startswith('#')
                next_is_header = formatted_lines[i+1].startswith('#')
                
                if not curr_is_list and not next_is_list and not curr_is_header and not next_is_header:
                    result.append('')
        
        return '\n'.join(result)
    
    def convert(self, method: str = 'auto', combine_methods: bool = False) -> Path:
        """
        Convert PDF to markdown using specified method.
        
        Args:
            method: Extraction method ('pymupdf', 'pdfplumber', 'docling', 'auto')
            combine_methods: If True, try to combine results from multiple methods
            
        Returns:
            Path to the output markdown file
        """
        logger.info(f"Converting {self.pdf_path.name} using method: {method}")
        
        pages_markdown = {}
        
        if method == 'auto' or combine_methods:
            # Try pdfplumber first (better for tables)
            plumber_result = self.extract_with_pdfplumber()
            
            if combine_methods:
                # Also try PyMuPDF and merge results
                pymupdf_result = self.extract_with_pymupdf()
                
                # Merge results intelligently
                for page_num in set(list(plumber_result.keys()) + list(pymupdf_result.keys())):
                    plumber_content = plumber_result.get(page_num, "")
                    pymupdf_content = pymupdf_result.get(page_num, "")
                    
                    # Count tables in each result
                    plumber_tables = plumber_content.count('### Table')
                    pymupdf_tables = pymupdf_content.count('### Table')
                    
                    # Choose the result with more tables, or longer content if same
                    if plumber_tables > pymupdf_tables:
                        pages_markdown[page_num] = plumber_content
                    elif pymupdf_tables > plumber_tables:
                        pages_markdown[page_num] = pymupdf_content
                    else:
                        # Same number of tables, choose longer content
                        pages_markdown[page_num] = plumber_content if len(plumber_content) >= len(pymupdf_content) else pymupdf_content
            else:
                pages_markdown = plumber_result if plumber_result else self.extract_with_pymupdf()
            
            # Try Docling if available and other methods failed
            if not pages_markdown and DOCLING_AVAILABLE:
                pages_markdown = self.extract_with_docling()
                
        elif method == 'pymupdf':
            pages_markdown = self.extract_with_pymupdf()
        elif method == 'pdfplumber':
            pages_markdown = self.extract_with_pdfplumber()
        elif method == 'docling':
            pages_markdown = self.extract_with_docling()
        else:
            raise ValueError(f"Unknown method: {method}")
        
        # Write to output file
        output_path = self.output_dir / f"{self.pdf_path.stem}.md"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            # Write metadata
            f.write(f"# {self.pdf_path.stem}\n\n")
            f.write(f"*Converted from: {self.pdf_path.name}*\n")
            f.write(f"*Extraction method: {method}*\n\n")
            f.write("---\n\n")
            
            # Write each page
            for page_num in sorted(pages_markdown.keys()):
                f.write(pages_markdown[page_num])
                f.write("\n\n---\n\n")
        
        logger.info(f"Markdown saved to: {output_path}")
        logger.info(f"Total pages processed: {len(pages_markdown)}")
        
        return output_path
    
    def convert_pages_separately(self, method: str = 'auto') -> List[Path]:
        """
        Convert PDF to separate markdown files for each page.
        
        Args:
            method: Extraction method
            
        Returns:
            List of paths to output markdown files
        """
        logger.info(f"Converting {self.pdf_path.name} to separate page files")
        
        pages_markdown = {}
        
        if method == 'auto' or method == 'pdfplumber':
            pages_markdown = self.extract_with_pdfplumber()
        elif method == 'pymupdf':
            pages_markdown = self.extract_with_pymupdf()
        elif method == 'docling':
            pages_markdown = self.extract_with_docling()
        
        output_paths = []
        
        # Create subdirectory for pages
        pages_dir = self.output_dir / f"{self.pdf_path.stem}_pages"
        pages_dir.mkdir(exist_ok=True)
        
        for page_num, content in pages_markdown.items():
            page_path = pages_dir / f"page_{page_num:03d}.md"
            
            with open(page_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            output_paths.append(page_path)
            logger.info(f"Page {page_num} saved to: {page_path}")
        
        return output_paths
    
    def extract_with_docling(self) -> Dict[int, str]:
        """
        Extract using Docling if available (advanced extraction).
        
        Returns:
            Dictionary mapping page numbers to markdown content
        """
        if not DOCLING_AVAILABLE:
            logger.warning("Docling not available, skipping this method")
            return {}
        
        pages_markdown = {}
        
        try:
            converter = DocumentConverter()
            result = converter.convert(str(self.pdf_path))
            
            # Convert Docling result to markdown
            markdown = result.document.export_to_markdown()
            
            # Try to split by pages if Docling provides page information
            if hasattr(result.document, 'pages'):
                for page_num, page in enumerate(result.document.pages, 1):
                    if hasattr(page, 'export_to_markdown'):
                        pages_markdown[page_num] = page.export_to_markdown()
                    else:
                        # Fallback: split the full markdown by page markers
                        pages_markdown[page_num] = f"# Page {page_num}\n\n{markdown}"
            else:
                # Return as single page if no page structure
                pages_markdown[1] = markdown
            
        except Exception as e:
            logger.error(f"Error with Docling extraction: {e}")
            
        return pages_markdown


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(
        description="Convert PDF documents to Markdown format with enhanced table support"
    )
    parser.add_argument(
        "pdf_path",
        help="Path to the PDF file to convert"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output directory for markdown files",
        default=None
    )
    parser.add_argument(
        "-m", "--method",
        choices=['auto', 'pymupdf', 'pdfplumber', 'docling'],
        default='auto',
        help="Extraction method to use (default: auto)"
    )
    parser.add_argument(
        "-c", "--combine",
        action="store_true",
        help="Combine results from multiple extraction methods for best results"
    )
    parser.add_argument(
        "-s", "--separate-pages",
        action="store_true",
        help="Save each page as a separate markdown file"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        converter = PDFToMarkdownConverter(args.pdf_path, args.output)
        
        if args.separate_pages:
            output_paths = converter.convert_pages_separately(args.method)
            print(f"✅ Created {len(output_paths)} markdown files")
        else:
            output_path = converter.convert(args.method, combine_methods=args.combine)
            print(f"✅ Markdown saved to: {output_path}")
            
    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()