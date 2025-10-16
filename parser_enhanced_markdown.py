#!/usr/bin/env python3
"""
Enhanced AI-Powered Markdown Parser for Project AURELIA
Generic RAG-optimized parser for technical document content extraction
- Advanced Code Extraction: Functions, arrays, expressions (language-agnostic)
- Smart Equation Detection: Multi-line matrices, mathematical expressions
- Formula Recognition: Non-code mathematical formulas
- Citation Support: Page numbers, sections, captions for RAG retrieval
- Figure/Table Detection: Captions and references for accurate citations
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class Element:
    """Enhanced element with advanced extraction attributes"""
    page: int
    element_id: str
    type: str  # text, heading, code_block, formula, equation, table_block, figure
    content: str
    section: str
    order: int
    bbox: Optional[List[float]] = None
    confidence: Optional[float] = None
    # Type-specific attributes
    level: Optional[int] = None
    language: Optional[str] = None
    latex: Optional[str] = None
    html: Optional[str] = None
    markdown: Optional[str] = None
    # Advanced extraction fields
    variable_name: Optional[str] = None
    code_type: Optional[str] = None
    equation_type: Optional[str] = None
    equation_number: Optional[str] = None
    formula_type: Optional[str] = None
    table_type: Optional[str] = None
    row_count: Optional[int] = None
    extraction_method: Optional[str] = None
    caption: Optional[str] = None
    detection_model: Optional[str] = None

    def to_jsonl(self) -> str:
        """Convert to JSONL format"""
        data = asdict(self)
        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}
        return json.dumps(data, ensure_ascii=False)


class EnhancedMarkdownParser:
    """Single comprehensive Markdown parser with advanced capabilities"""

    def __init__(self, markdown_dir: str, output_dir: str = "."):
        self.markdown_dir = Path(markdown_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        self.elements: List[Element] = []
        self.current_section = "Unknown"
        self.element_counter = 0

        # Track extracted content to prevent duplicates
        self.extracted_code = set()
        self.extracted_equations = set()
        self.extracted_formulas = set()

        # Statistics
        self.stats = {
            'tables': 0,
            'formulas': 0,
            'figures': 0,
            'code': 0,
            'equations': 0,
            'headings': 0,
            'lists': 0,
            'text': 0
        }

        logger.info("✅ Enhanced AURELIA Parser initialized for RAG pipeline")

    def extract(self):
        """Main extraction process with advanced capabilities"""
        logger.info(f"🚀 Starting enhanced extraction from {self.markdown_dir}")

        try:
            # Get all markdown files
            md_files = sorted(self.markdown_dir.glob('*.md'))
            if not md_files:
                logger.error(f"No markdown files found in {self.markdown_dir}")
                return

            logger.info(f"Found {len(md_files)} markdown files")

            # Process each markdown file
            for file_idx, md_file in enumerate(md_files, start=1):
                if file_idx % 10 == 0 or file_idx == 1:
                    logger.info(f"Processing file {file_idx}/{len(md_files)}: {md_file.name}")

                # Read markdown content
                try:
                    with open(md_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                except Exception as e:
                    logger.warning(f"Failed to read {md_file.name}: {e}")
                    continue

                if content.strip():
                    # Add basic text element
                    self._add_basic_text_element(content, file_idx, md_file.name)

                    # Run advanced extraction on this file's content
                    self._run_advanced_extraction_for_file(content, file_idx)

            logger.info(f"📄 Processed {len(md_files)} files")

            # Finalize
            self.elements.sort(key=lambda x: (x.page, x.order))
            self._save_outputs()

            logger.info("✅ Enhanced extraction complete!")
            logger.info(f"   Total elements: {len(self.elements)}")

            # Show breakdown by page and type
            page_counts = {}
            element_counts = {}
            for elem in self.elements:
                page_counts[elem.page] = page_counts.get(elem.page, 0) + 1
                element_counts[elem.type] = element_counts.get(elem.type, 0) + 1

            for elem_type, count in sorted(element_counts.items()):
                logger.info(f"   {elem_type}: {count}")

            # Show page distribution (first 10 pages)
            logger.info("   File distribution (first 10):")
            for page in sorted([p for p in page_counts.keys() if p <= 10]):
                logger.info(f"     File {page}: {page_counts[page]} elements")

        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            raise

    def _add_basic_text_element(self, text: str, file_num: int, file_name: str = None):
        """Add basic text element"""
        self.element_counter += 1
        section_name = self._extract_section_name(text, file_name)
        elem = Element(
            page=file_num,
            element_id=f"elem_{self.element_counter:04d}",
            type='text',
            content=text.strip(),
            section=section_name,
            order=self.element_counter
        )
        self.elements.append(elem)
        self.stats['text'] += 1

    def _run_advanced_extraction_for_file(self, page_text: str, file_num: int):
        """Run sequential extraction preserving reading order"""
        if not page_text.strip():
            return

        # Get section name for this content
        base_section = self._extract_section_name(page_text)

        # NEW APPROACH: Sequential line-by-line processing to preserve reading order
        self._extract_elements_sequentially(page_text, file_num, base_section)

    def _extract_elements_sequentially(self, page_text: str, file_num: int, base_section: str):
        """Extract elements in reading order, line by line"""
        lines = page_text.split('\n')
        current_text_buffer = []
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            # Skip empty lines and add to text buffer
            if not line:
                current_text_buffer.append('')
                i += 1
                continue

            # Check for different element types in priority order
            element_extracted = False

            # 1. Try to extract code block starting at this line
            code_result = self._try_extract_code_at_line(lines, i)
            if code_result:
                # Flush any accumulated text first
                self._flush_text_buffer(current_text_buffer, file_num, base_section)
                current_text_buffer = []

                # Add the code element
                self._add_code_element(code_result, file_num, base_section)
                i += code_result['lines_consumed']
                element_extracted = True

            # 2. Try to extract table starting at this line
            elif self._is_table_start(line):
                table_result = self._try_extract_table_at_line(lines, i)
                if table_result:
                    # Flush text buffer first
                    self._flush_text_buffer(current_text_buffer, file_num, base_section)
                    current_text_buffer = []

                    # Add the table element
                    self._add_table_element(table_result, file_num, base_section)
                    i += table_result['lines_consumed']
                    element_extracted = True

            # 3. Try to extract equation/formula
            elif self._is_equation_line(line):
                equation_result = self._try_extract_equation_at_line(lines, i)
                if equation_result:
                    # Flush text buffer first
                    self._flush_text_buffer(current_text_buffer, file_num, base_section)
                    current_text_buffer = []

                    # Add the equation element
                    self._add_equation_element(equation_result, file_num, base_section)
                    i += equation_result['lines_consumed']
                    element_extracted = True

            # 4. If no special element, add to text buffer
            if not element_extracted:
                current_text_buffer.append(lines[i])
                i += 1

        # Flush any remaining text buffer
        self._flush_text_buffer(current_text_buffer, file_num, base_section)

    def _flush_text_buffer(self, text_buffer: List[str], file_num: int, base_section: str):
        """Flush accumulated text lines as a text element"""
        if not text_buffer:
            return

        # Join the text and clean it up
        text_content = '\n'.join(text_buffer).strip()

        # Only create text element if there's meaningful content
        if len(text_content) > 20:  # Minimum threshold
            self.element_counter += 1
            elem = Element(
                page=file_num,
                element_id=f"elem_{self.element_counter:04d}",
                type='text',
                content=text_content,
                section=base_section,
                order=self.element_counter,
                extraction_method='sequential_text_buffer'
            )
            self.elements.append(elem)
            self.stats['text'] += 1

    def _try_extract_code_at_line(self, lines: List[str], start_idx: int) -> Dict:
        """Try to extract code starting at the given line"""
        line = lines[start_idx].strip()

        # Check for various code patterns
        if self._is_code_line(line):
            # Look ahead to see if this is part of a multi-line code block
            code_lines = [lines[start_idx]]
            lines_consumed = 1

            # Look for related code lines immediately following
            for i in range(start_idx + 1, min(start_idx + 10, len(lines))):
                next_line = lines[i].strip()
                if (next_line and
                    (self._is_code_line(next_line) or
                     self._is_code_continuation(next_line, line))):
                    code_lines.append(lines[i])
                    lines_consumed += 1
                elif not next_line:  # Empty line - might continue
                    code_lines.append(lines[i])
                    lines_consumed += 1
                else:
                    break

            return {
                'code': '\n'.join(code_lines).strip(),
                'lines_consumed': lines_consumed,
                'language': 'generic',
                'type': 'sequential_code'
            }

        return None

    def _is_code_line(self, line: str) -> bool:
        """Check if a line looks like code"""
        if not line or len(line) < 3:
            return False

        # Skip obvious non-code patterns
        if (line.startswith('#') or
            line.startswith('|') or
            re.match(r'^(page|chapter|section)\s+\d+', line.lower())):
            return False

        # Check for code patterns
        return (
            re.search(r'\w+\s*=\s*', line) or           # Assignments
            re.search(r'\w+\s*\([^)]*\)', line) or      # Function calls
            re.search(r'\[[^\]]*\]', line) or           # Arrays
            re.search(r'\d+\.\d+e[+\-]?\d+', line) or   # Scientific notation
            re.search(r'[+\-*/^]\s*\w+', line) or       # Math operations
            line.endswith(';') or                        # Statement terminator
            re.search(r'\w+\.\w+', line)                # Object notation
        )

    def _is_code_continuation(self, line: str, prev_line: str) -> bool:
        """Check if line continues a code block"""
        # Multi-line arrays or matrices
        if re.search(r'^[\d\s.\-\+]+$', line):
            return True

        # Continuation of assignments
        if '=' in prev_line and not '=' in line and re.search(r'^[\w\s\d.\-\+]+$', line):
            return True

        return False

    def _add_code_element(self, code_result: Dict, file_num: int, base_section: str):
        """Add a code element"""
        code_hash = hash(code_result['code'])

        if code_hash not in self.extracted_code:
            self.extracted_code.add(code_hash)
            self.element_counter += 1

            elem = Element(
                page=file_num,
                element_id=f"elem_{self.element_counter:04d}",
                type='code_block',
                content=code_result['code'],
                section=f"{base_section} - Code",
                order=self.element_counter,
                language=code_result['language'],
                code_type=code_result['type'],
                extraction_method='sequential_extraction'
            )
            self.elements.append(elem)
            self.stats['code'] += 1

    def _is_table_start(self, line: str) -> bool:
        """Check if line starts a table"""
        return '|' in line and len(line.split('|')) >= 3

    def _try_extract_table_at_line(self, lines: List[str], start_idx: int) -> Dict:
        """Try to extract table starting at the given line"""
        if not self._is_table_start(lines[start_idx].strip()):
            return None

        table_lines = []
        lines_consumed = 0

        # Collect all consecutive table lines
        for i in range(start_idx, len(lines)):
            line = lines[i].strip()
            if '|' in line:
                table_lines.append(lines[i])
                lines_consumed += 1
            elif not line:  # Empty line - might continue
                table_lines.append(lines[i])
                lines_consumed += 1
            else:
                break

        if len(table_lines) >= 2:  # Minimum table size
            return {
                'content': '\n'.join(table_lines).strip(),
                'lines_consumed': lines_consumed,
                'row_count': len([l for l in table_lines if l.strip() and '|' in l])
            }

        return None

    def _add_table_element(self, table_result: Dict, file_num: int, base_section: str):
        """Add a table element"""
        content_hash = hash(table_result['content'])

        if content_hash not in self.extracted_formulas:  # Use formulas set to prevent duplication
            self.extracted_formulas.add(content_hash)
            self.element_counter += 1

            elem = Element(
                page=file_num,
                element_id=f"elem_{self.element_counter:04d}",
                type='table_block',
                content=table_result['content'],
                section=f"{base_section} - Tables",
                order=self.element_counter,
                table_type='sequential_table',
                row_count=table_result['row_count'],
                extraction_method='sequential_extraction'
            )
            self.elements.append(elem)
            self.stats['tables'] += 1

    def _is_equation_line(self, line: str) -> bool:
        """Check if line looks like an equation/formula"""
        if not line or len(line) < 5:
            return False

        # Skip code and table lines
        if self._is_code_line(line) or self._is_table_start(line):
            return False

        # Look for mathematical expressions
        return (
            re.search(r'\([0-9]+\)', line) or  # Numbered equations
            (('=' in line) and re.search(r'[a-zA-Z]+\s*=\s*[^=]*[+\-*/^√∑∫]', line))
        )

    def _try_extract_equation_at_line(self, lines: List[str], start_idx: int) -> Dict:
        """Try to extract equation starting at the given line"""
        line = lines[start_idx].strip()

        if self._is_equation_line(line):
            return {
                'content': line,
                'lines_consumed': 1,
                'type': 'sequential_equation'
            }

        return None

    def _add_equation_element(self, equation_result: Dict, file_num: int, base_section: str):
        """Add an equation element"""
        content_hash = hash(equation_result['content'])

        if content_hash not in self.extracted_equations:
            self.extracted_equations.add(content_hash)
            self.element_counter += 1

            elem = Element(
                page=file_num,
                element_id=f"elem_{self.element_counter:04d}",
                type='equation',
                content=equation_result['content'],
                section=f"{base_section} - Equations",
                order=self.element_counter,
                equation_type=equation_result['type'],
                extraction_method='sequential_extraction'
            )
            self.elements.append(elem)
            self.stats['equations'] += 1

    # Legacy extraction methods (temporarily disabled in favor of sequential extraction)
    def _extract_and_group_code_blocks(self, text: str) -> List[Dict]:
        """Extract code blocks and intelligently group related ones for better RAG context"""
        # First extract all individual code snippets
        individual_codes = self._extract_code_blocks_advanced(text)

        if not individual_codes:
            return []

        # Group related code snippets by proximity and variable relationships
        grouped_blocks = []
        lines = text.split('\n')

        # Create line-to-code mapping
        code_line_map = {}
        for code in individual_codes:
            code_start_line = self._find_code_line_number(code['code'], lines)
            if code_start_line >= 0:
                code_line_map[code_start_line] = code

        # Group codes that are close together or related
        sorted_lines = sorted(code_line_map.keys())
        current_group = []

        for i, line_num in enumerate(sorted_lines):
            code = code_line_map[line_num]

            if not current_group:
                current_group.append((line_num, code))
            else:
                # Check if this code should be grouped with the current group
                last_line = current_group[-1][0]

                # Group if within 10 lines or shares variables
                if (line_num - last_line <= 10 or
                    self._codes_are_related(current_group, code)):
                    current_group.append((line_num, code))
                else:
                    # Finalize current group and start new one
                    if current_group:
                        grouped_blocks.append(self._create_code_group(current_group, lines))
                    current_group = [(line_num, code)]

        # Don't forget the last group
        if current_group:
            grouped_blocks.append(self._create_code_group(current_group, lines))

        return grouped_blocks

    def _extract_code_blocks_advanced(self, text: str) -> List[Dict]:
        """Extract individual code blocks using advanced regex patterns"""
        code_blocks = []

        # MATLAB array assignments (handles multi-line matrices)
        array_pattern = r'(\w+)\s*=\s*(?:\d+\.\d+e[+\-]?\d+\s*\*\s*)?(?:\[([\d\s,;.\-\+eE\n]+)\]|(\d+\.\d+e[+\-]?\d+\s*\*\s*[\d\s.\-\+\n]+))'
        for match in re.finditer(array_pattern, text, re.MULTILINE | re.DOTALL):
            var_name = match.group(1)
            code_content = match.group(0).strip()
            code_content = self._clean_matrix_format(code_content)

            code_blocks.append({
                'language': 'generic',
                'code': code_content,
                'variable_name': var_name,
                'type': 'array_assignment',
                'extraction_method': 'advanced_regex'
            })

        # Function definitions
        func_pattern = r'function\s+([\w,\[\]\s]+)\s*=\s*(\w+)\s*\((.*?)\)'
        for match in re.finditer(func_pattern, text):
            start = match.start()
            end_match = re.search(r'\nend\b', text[start:start+2000])

            if end_match:
                full_code = text[start:start+end_match.end()]
            else:
                full_code = match.group(0)

            code_blocks.append({
                'language': 'generic',
                'code': full_code.strip(),
                'variable_name': match.group(2),
                'type': 'function_definition',
                'extraction_method': 'advanced_regex'
            })

        # Multi-output assignments: [var1, var2] = function(...)
        multi_output_pattern = r'\[([^\]]+)\]\s*=\s*(\w+)\s*\([^)]*\)'
        for match in re.finditer(multi_output_pattern, text):
            variables = [v.strip() for v in match.group(1).split(',')]
            function_name = match.group(2)
            code_blocks.append({
                'language': 'generic',
                'code': match.group(0).strip(),
                'variable_name': variables[0] if variables else function_name,
                'type': 'multi_output_assignment',
                'extraction_method': 'advanced_regex'
            })

        # Simple variable assignments and function calls
        assign_pattern = r'(\w+)\s*=\s*([^\n=]{10,200})'
        for match in re.finditer(assign_pattern, text):
            expr = match.group(2).strip()
            if self._is_code_expression(expr):
                code_blocks.append({
                    'language': 'generic',
                    'code': match.group(0).strip(),
                    'variable_name': match.group(1),
                    'type': 'expression',
                    'extraction_method': 'advanced_regex'
                })

        # Function calls without assignment
        func_call_pattern = r'^\s*(\w+)\s*\([^)]*\)\s*$'
        for line in text.split('\n'):
            line = line.strip()
            if re.match(func_call_pattern, line) and len(line) > 5:
                # Check if it's a function call (generic pattern)
                if re.search(r'\w+\s*\([^)]*\)', line):
                    code_blocks.append({
                        'language': 'generic',
                        'code': line,
                        'variable_name': None,
                        'type': 'function_call',
                        'extraction_method': 'function_pattern'
                    })

        return code_blocks

    def _extract_standalone_code_lines(self, text: str) -> List[Dict]:
        """Extract individual embedded code lines that weren't grouped"""
        standalone_codes = []
        lines = text.split('\n')

        # Generic patterns for detecting function calls that should be code
        # This approach is language and domain agnostic

        for line_num, line in enumerate(lines):
            line_stripped = line.strip()

            # Skip if too short or obvious non-code (generic patterns)
            if (len(line_stripped) < 5 or
                line_stripped.startswith('#') or
                re.match(r'^(page|chapter|section)\s+\d+', line_stripped.lower()) or
                '. . .' in line_stripped or
                line_stripped.startswith('|') or  # Table rows
                line_stripped.startswith('>')):   # Blockquotes
                continue

            # Look for assignment patterns with MATLAB functions
            assignment_match = re.match(r'^([A-Za-z]\w*)\s*=\s*([^=]+)$', line_stripped)
            if assignment_match:
                var_name = assignment_match.group(1)
                expression = assignment_match.group(2)

                # Check if expression looks like code using generic patterns
                if (re.search(r'\w+\s*\([^)]*\)', expression) or  # Function calls
                    re.search(r'\[[^\]]*\]', expression) or        # Array/matrix notation
                    re.search(r'\d+\.\d+e[+\-]?\d+', expression) or # Scientific notation
                    re.search(r'[+\-*/^]\s*\w+', expression) or    # Mathematical operations
                    re.search(r'\w+\.\w+', expression)):           # Object notation

                    standalone_codes.append({
                        'code': line_stripped,
                        'variable_name': var_name,
                        'language': 'generic',
                        'type': 'embedded_assignment',
                        'extraction_method': 'standalone_extraction'
                    })

            # Look for standalone function calls (generic pattern)
            elif (re.match(r'^\s*\w+\s*\([^)]*\)\s*;?\s*$', line_stripped) and
                  len(line_stripped) > 5 and
                  not any(skip_word in line_stripped.lower() for skip_word in ['see', 'page', 'section', 'figure'])):
                standalone_codes.append({
                    'code': line_stripped,
                    'variable_name': None,
                    'language': 'generic',
                    'type': 'embedded_function_call',
                    'extraction_method': 'standalone_extraction'
                })

        return standalone_codes

    def _remove_extracted_code_from_text(self, text: str, extracted_code_lines: set) -> str:
        """Remove extracted code lines from text to clean it for text processing"""
        lines = text.split('\n')
        cleaned_lines = []

        for line in lines:
            line_stripped = line.strip()

            # Keep the line if it's not in extracted code
            if line_stripped not in extracted_code_lines:
                cleaned_lines.append(line)
            # Skip extracted code lines completely - don't leave debug comments

        return '\n'.join(cleaned_lines)

    def _extract_equations_smart(self, text: str) -> List[Dict]:
        """Enhanced equation extraction for mathematical expressions and matrices"""
        equations = []
        lines = text.split('\n')

        for line_num, line in enumerate(lines):
            line_stripped = line.strip()

            # Skip table of contents, placeholders, and code-like content
            if ('. . .' in line_stripped or
                re.search(r'\.{3,}', line_stripped) or
                '<!-- formula-not-decoded -->' in line_stripped or
                self._is_heading(line_stripped) or
                self._is_likely_code(line_stripped)):
                continue

            # Find numbered equations like (1), (2), etc.
            eq_match = re.match(r'\((\d+)\)\s*(.{10,})', line_stripped)
            if eq_match:
                eq_content = eq_match.group(2).strip()
                if self._has_math_content(eq_content) and not self._is_likely_code(eq_content):
                    equations.append({
                        'equation_number': eq_match.group(1),
                        'equation': eq_content,
                        'line_number': line_num,
                        'type': 'numbered_equation'
                    })

            # Find multi-line matrix outputs
            elif re.match(r'\s*\d+\.\d+e[+\-]?\d+\s*\*\s*$', line_stripped):
                matrix_lines = [line_stripped]
                for next_line_idx in range(line_num + 1, min(line_num + 10, len(lines))):
                    next_line = lines[next_line_idx].strip()
                    if re.match(r'^\s*[\d\s.\-\+]+$', next_line) and len(next_line.split()) <= 5:
                        matrix_lines.append(next_line)
                    else:
                        break

                if len(matrix_lines) > 1:
                    var_line = ""
                    for prev_line_idx in range(line_num - 1, max(line_num - 3, 0), -1):
                        prev_line = lines[prev_line_idx].strip()
                        if re.match(r'^\w+\s*=$', prev_line):
                            var_line = prev_line
                            break

                    full_equation = var_line + '\n  ' + '\n  '.join(matrix_lines)
                    equations.append({
                        'equation': full_equation,
                        'line_number': line_num,
                        'type': 'matrix_output',
                        'variable_name': var_line.replace('=', '').strip() if var_line else None
                    })

            # Find mathematical expressions (not code assignments)
            elif ('=' in line_stripped and
                  self._has_math_content(line_stripped) and
                  not self._is_likely_code(line_stripped) and
                  len(line_stripped) > 15 and
                  len(line_stripped) < 150):
                # Mathematical expressions like "Portfolio Risk = sqrt(w'*Cov*w)"
                if re.search(r'[a-zA-Z]+\s*=\s*[^\[\]]*[+\-*/^()√∑∫]', line_stripped):
                    equations.append({
                        'equation': line_stripped,
                        'line_number': line_num,
                        'type': 'mathematical_expression'
                    })

        return equations

    def _extract_formulas_regex(self, text: str) -> List[Dict]:
        """Extract mathematical formulas (excluding code and equations)"""
        formulas = []
        lines = text.split('\n')

        for line_num, line in enumerate(lines):
            line_stripped = line.strip()

            # Skip TOC, placeholders, headings, code-like content, and table content
            if ('. . .' in line_stripped or
                '<!-- formula-not-decoded -->' in line_stripped or
                self._is_heading(line_stripped) or
                self._is_likely_code(line_stripped) or
                self._is_table_content(line_stripped)):
                continue

            # Look for mathematical formulas (not code assignments or table content)
            if ('=' in line_stripped and
                self._has_math_content(line_stripped) and
                not self._is_likely_code(line_stripped) and
                not self._is_table_content(line_stripped) and
                20 < len(line_stripped) < 200):
                # Check if it's a mathematical formula with proper mathematical notation
                if re.search(r'[+\-*/^()√∑∫]|\b(sin|cos|tan|log|ln|exp|sqrt)\b', line_stripped):
                    formulas.append({
                        'formula': line_stripped,
                        'line_number': line_num,
                        'extraction_method': 'regex',
                        'type': 'mathematical_formula'
                    })

        return formulas

    def _extract_section_name(self, text: str, fallback_name: str = None) -> str:
        """Extract meaningful section name from content"""
        lines = text.split('\n')

        # Look for chapter numbers and titles
        for i, line in enumerate(lines[:10]):  # Check first 10 lines
            line_stripped = line.strip()

            # Skip page/document headers (generic pattern)
            if re.match(r'^#\s*(page|chapter|section)\s+\d+', line_stripped.lower()):
                continue

            # Look for chapter patterns (generic) - capitalized multi-word titles
            if (re.match(r'^[A-Z][a-z].*[A-Z].*$', line_stripped) and
                len(line_stripped.split()) >= 2 and
                len(line_stripped) < 80):
                return line_stripped

            # Look for numbered chapters like "1" followed by chapter name
            if re.match(r'^\d+$', line_stripped) and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line and len(next_line) > 10 and not next_line.startswith('#'):
                    return next_line

            # Look for section titles that aren't too long
            if (line_stripped and
                not line_stripped.startswith('#') and
                not '...' in line_stripped and
                len(line_stripped) > 10 and
                len(line_stripped) < 100 and
                not re.match(r'^[\d\.\-\s]+$', line_stripped)):

                # Check if it looks like a title (proper case, meaningful words)
                words = line_stripped.split()
                if (len(words) >= 2 and
                    any(word[0].isupper() for word in words if word) and
                    not any(word.lower() in ['page', 'contents', 'table'] for word in words)):
                    return line_stripped

        # If no meaningful section found, use fallback
        return fallback_name if fallback_name else "General Content"

    # Helper methods
    def _clean_matrix_format(self, code: str) -> str:
        """Clean and format matrix code properly"""
        if '1.0e+004' in code or '1.0e+' in code:
            lines = code.split('\n')
            cleaned_lines = []
            for line in lines:
                line = line.strip()
                if line and not line.endswith('='):
                    if re.match(r'^\s*[\d\s.\-\+]+$', line):
                        cleaned_lines.append('    ' + line)
                    else:
                        cleaned_lines.append(line)
                else:
                    cleaned_lines.append(line)
            return '\n'.join(cleaned_lines)
        return code

    def _is_code_expression(self, expr: str) -> bool:
        """Check if expression is likely code"""
        code_indicators = ['*', '+', '(', ')', '.', ':', '^', '/', 'sqrt', 'sin', 'cos']
        return any(op in expr for op in code_indicators) and not re.match(r'^[A-Z][a-z]+\s+[A-Z]', expr)

    def _is_likely_code(self, text: str) -> bool:
        """Enhanced check for code-like content to prevent misclassification"""
        # MATLAB/code patterns
        code_patterns = [
            r'^\w+\s*=\s*\[.*\]',  # Array assignments
            r'^\w+\s*=\s*\w+\(',  # Function calls
            r'\[([^\]]+)\]\s*=\s*\w+\s*\(',  # Multi-output assignments
            r'datenum\(',  # Specific function calls
            r'datetime\(',
            r'blsprice\(',  # Financial toolbox functions
            r'blsdelta\(',
            r'blsgamma\(',
            r'blsvega\(',
            r'blslambda\(',
            r'\w+\s*=\s*[\d.]+;?$',  # Simple numeric assignments
            r'^[A-Z]\w*\s*=\s*',  # Variable assignments starting with capital
        ]
        return any(re.search(pattern, text.strip()) for pattern in code_patterns)

    def _is_table_content(self, text: str) -> bool:
        """Check if text is likely table content"""
        text = text.strip()
        # Check for markdown table syntax
        if text.count('|') >= 2:
            return True
        # Check for table separators
        if text.count('-') > 3 and '|' in text:
            return True
        return False

    def _extract_and_group_figures_tables(self, text: str, page_num: int) -> List[Dict]:
        """Extract and intelligently group figures and tables for better RAG context"""
        figures_tables = []
        lines = text.split('\n')

        # First, extract all individual table rows and figures
        individual_items = self._extract_individual_figures_tables(text, page_num)

        if not individual_items:
            return []

        # Group tables by proximity
        table_items = [item for item in individual_items if item['type'] == 'table']
        figure_items = [item for item in individual_items if item['type'] == 'figure']

        # Group related table rows into complete tables
        if table_items:
            grouped_tables = self._group_table_rows(table_items, lines)
            figures_tables.extend(grouped_tables)

        # Add figures as-is (they're typically self-contained)
        figures_tables.extend(figure_items)

        return figures_tables

    def _extract_individual_figures_tables(self, text: str, page_num: int) -> List[Dict]:
        """Extract individual table rows and figure references"""
        items = []
        lines = text.split('\n')

        for line_num, line in enumerate(lines):
            line_stripped = line.strip()

            # Detect markdown table rows
            if '|' in line_stripped and line_stripped.count('|') >= 2:
                items.append({
                    'type': 'table',
                    'content': line_stripped,
                    'line_number': line_num,
                    'page': page_num,
                    'is_header': line_stripped.startswith('###') or 'M1' in line_stripped or 'M2' in line_stripped,
                    'is_separator': line_stripped.count('-') > 3
                })

            # Detect figure references
            elif re.search(r'\b(figure|fig|diagram|chart|graph)\s*\d*\b', line_stripped, re.IGNORECASE):
                items.append({
                    'type': 'figure',
                    'content': line_stripped,
                    'caption': line_stripped,
                    'line_number': line_num,
                    'page': page_num
                })

        return items

    def _group_table_rows(self, table_items: List[Dict], lines: List[str]) -> List[Dict]:
        """Group related table rows into complete table blocks"""
        if not table_items:
            return []

        grouped_tables = []
        current_table_group = []

        # Sort by line number
        table_items.sort(key=lambda x: x['line_number'])

        for i, item in enumerate(table_items):
            if not current_table_group:
                current_table_group.append(item)
            else:
                # Check if this row belongs to the current table
                last_line = current_table_group[-1]['line_number']
                current_line = item['line_number']

                # Group if within 3 lines (allowing for some text between rows)
                if current_line - last_line <= 3:
                    current_table_group.append(item)
                else:
                    # Finalize current table and start new one
                    if len(current_table_group) >= 2:  # At least 2 rows to make a table
                        grouped_table = self._create_table_block(current_table_group, lines)
                        if grouped_table:
                            grouped_tables.append(grouped_table)
                    current_table_group = [item]

        # Don't forget the last table
        if len(current_table_group) >= 2:
            grouped_table = self._create_table_block(current_table_group, lines)
            if grouped_table:
                grouped_tables.append(grouped_table)

        return grouped_tables

    def _create_table_block(self, table_group: List[Dict], lines: List[str]) -> Dict:
        """Create a combined table block from grouped table rows"""
        if len(table_group) < 2:
            return None

        # Sort by line number
        table_group.sort(key=lambda x: x['line_number'])

        # Combine all table rows
        table_content = []
        for item in table_group:
            table_content.append(item['content'])

        # Find table caption by looking around the table
        start_line = table_group[0]['line_number']
        end_line = table_group[-1]['line_number']

        caption = self._find_table_caption(lines, start_line, end_line)

        # Determine table type
        table_text = '\n'.join(table_content)
        if any('receipts' in row['content'].lower() for row in table_group):
            table_type = 'financial_data_table'
        elif any('M1' in row['content'] or 'M2' in row['content'] for row in table_group):
            table_type = 'matrix_comparison_table'
        else:
            table_type = 'data_table'

        return {
            'type': 'table_block',
            'content': '\n'.join(table_content),
            'caption': caption,
            'table_type': table_type,
            'row_count': len(table_group),
            'extraction_method': 'grouped_table_analysis',
            'page': table_group[0]['page']
        }

    def _find_table_caption(self, lines: List[str], start_line: int, end_line: int) -> str:
        """Find caption text near a table"""
        # Look 3 lines before table start and 2 lines after table end
        search_lines = []

        # Before table
        for i in range(max(0, start_line - 3), start_line):
            line = lines[i].strip()
            if line and not line.startswith('|') and len(line) > 10:
                search_lines.append(line)

        # After table
        for i in range(end_line + 1, min(len(lines), end_line + 3)):
            line = lines[i].strip()
            if line and not line.startswith('|') and len(line) > 10:
                search_lines.append(line)

        # Return the most descriptive line
        if search_lines:
            # Prefer lines that contain table-related keywords
            for line in search_lines:
                if any(word in line.lower() for word in ['example', 'table', 'data', 'comparison', 'matrix']):
                    return line[:150]
            # Otherwise return the first meaningful line
            return search_lines[0][:150]

        return ""

    def _find_code_line_number(self, code_content: str, lines: List[str]) -> int:
        """Find the line number where code appears in the text"""
        # Look for the first few characters of the code
        code_start = code_content.split('\n')[0].strip()[:20]
        for i, line in enumerate(lines):
            if code_start in line.strip():
                return i
        return -1

    def _codes_are_related(self, current_group: List[Tuple[int, Dict]], new_code: Dict) -> bool:
        """Check if a new code snippet is related to the current group"""
        new_var = new_code.get('variable_name', '') or ''
        if not new_var:
            return False

        # Check if any code in the group uses or defines the same variable
        for _, code in current_group:
            existing_var = code.get('variable_name', '') or ''
            existing_code = code.get('code', '') or ''

            # Same variable or one uses the other
            if (new_var and existing_var and new_var == existing_var) or \
               (new_var and new_var in existing_code) or \
               (existing_var and existing_var in new_code.get('code', '')):
                return True
        return False

    def _create_code_group(self, code_group: List[Tuple[int, Dict]], lines: List[str]) -> Dict:
        """Create a combined code block from a group of related codes"""
        if not code_group:
            return {}

        # Sort by line number
        code_group.sort(key=lambda x: x[0])

        # Combine all code snippets
        combined_codes = []
        individual_codes = []
        primary_vars = []
        block_types = set()

        for line_num, code in code_group:
            code_content = code['code']
            combined_codes.append(code_content)
            individual_codes.append(code_content)

            if code.get('variable_name'):
                primary_vars.append(code['variable_name'])
            block_types.add(code.get('type', 'unknown'))

        # Create context description based on surrounding text
        context_lines = []
        start_line = max(0, code_group[0][0] - 2)
        end_line = min(len(lines), code_group[-1][0] + 3)

        for i in range(start_line, end_line):
            line = lines[i].strip()
            if line and not any(code['code'].strip().startswith(line[:20]) for _, code in code_group):
                # This is explanatory text, not code
                if len(line) > 20 and not line.startswith('#'):
                    context_lines.append(line)

        context_description = ' '.join(context_lines[:2]) if context_lines else ""

        # Determine block type
        if 'function_definition' in block_types:
            block_type = 'function_with_examples'
        elif len(primary_vars) > 1:
            block_type = 'variable_workflow'
        elif 'array_assignment' in block_types:
            block_type = 'data_definition'
        else:
            block_type = 'code_sequence'

        return {
            'combined_code': '\n\n'.join(combined_codes),
            'individual_codes': individual_codes,
            'language': 'generic',
            'primary_variable': primary_vars[0] if primary_vars else None,
            'all_variables': list(set(primary_vars)),
            'block_type': block_type,
            'extraction_method': 'grouped_analysis',
            'context_description': context_description[:200] if context_description else None,
            'code_count': len(code_group)
        }

    def _find_nearby_caption(self, lines: List[str], center_line: int, element_type: str) -> str:
        """Find caption text near a table or figure"""
        # Look 3 lines before and after
        for offset in range(-3, 4):
            idx = center_line + offset
            if 0 <= idx < len(lines):
                line = lines[idx].strip()
                if (element_type.lower() in line.lower() or
                    re.search(r'\b(caption|title|description)\b', line, re.IGNORECASE)):
                    return line
        return ""

    def _has_math_content(self, text: str) -> bool:
        """Check for mathematical content"""
        math_indicators = ['*', '/', '^', 'sqrt', 'matrix', '∑', '∫', 'sin', 'cos', '=', '+', '-']
        return any(ind in text.lower() for ind in math_indicators)

    def _is_heading(self, line: str) -> bool:
        """Detect headings to avoid false positives"""
        if len(line) > 150:
            return False

        heading_words = ['chapter', 'section', 'introduction', 'description',
                        'getting started', 'toolbox', 'reference', 'contents']

        return any(word in line.lower() for word in heading_words)

    def _save_outputs(self):
        """Save all outputs optimized for RAG pipeline"""
        base_name = self.markdown_dir.name

        # JSONL for streaming/chunking
        jsonl_path = self.output_dir / f"{base_name}_enhanced.jsonl"
        with open(jsonl_path, 'w', encoding='utf-8') as f:
            for elem in self.elements:
                f.write(elem.to_jsonl() + '\n')
        logger.info(f"✓ JSONL saved to {jsonl_path}")

        # Full JSON with RAG metadata
        json_path = self.output_dir / f"{base_name}_enhanced.json"
        full_output = {
            'metadata': {
                'source_directory': str(self.markdown_dir),
                'parser_version': 'Enhanced AURELIA Parser v2.0',
                'total_files': len(set(elem.page for elem in self.elements)),
                'total_elements': len(self.elements),
                'extraction_date': str(Path().cwd()),
                'rag_optimized': True
            },
            'statistics': self.stats,
            'elements': [json.loads(elem.to_jsonl()) for elem in self.elements]
        }

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(full_output, f, indent=2, ensure_ascii=False)
        logger.info(f"✓ JSON saved to {json_path}")

        # Enhanced statistics for RAG evaluation
        stats_path = self.output_dir / f"{base_name}_enhanced_stats.json"
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump({
                'total_elements': len(self.elements),
                'extraction_stats': self.stats,
                'target_equation_found': any('Values' in elem.content and '1.0e+004' in elem.content for elem in self.elements),
                'deduplication_enabled': True,
                'citation_ready': True,
                'pages_processed': len(set(elem.page for elem in self.elements)),
                'average_elements_per_page': len(self.elements) / len(set(elem.page for elem in self.elements)) if self.elements else 0
            }, f, indent=2)
        logger.info(f"✓ Enhanced statistics saved to {stats_path}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Enhanced AURELIA Markdown Parser for RAG Pipeline")
    parser.add_argument("markdown_dir", help="Path to directory containing markdown files")
    parser.add_argument("-o", "--output-dir", default="enhanced_output", help="Output directory")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--rag-mode", action="store_true", help="Optimize for RAG chunking")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    markdown_dir = Path(args.markdown_dir)
    if not markdown_dir.exists():
        logger.error(f"Directory not found: {markdown_dir}")
        sys.exit(1)

    if not markdown_dir.is_dir():
        logger.error(f"Path is not a directory: {markdown_dir}")
        sys.exit(1)

    try:
        parser_instance = EnhancedMarkdownParser(str(markdown_dir), args.output_dir)
        parser_instance.extract()
        logger.info(f"🎯 AURELIA extraction complete - ready for RAG pipeline")
    except Exception as e:
        logger.error(f"Failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()