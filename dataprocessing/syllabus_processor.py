import os
from typing import Dict, List, Any, Tuple
import spacy
from pathlib import Path
import json
from datetime import datetime
import re
from dataclasses import dataclass, asdict
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader

@dataclass
class CourseInfo:
    course_code: str = ""
    course_name: str = ""
    instructor: str = ""
    semester: str = ""
    year: str = ""
    description: str = ""
    objectives: List[str] = None
    prerequisites: List[str] = None
    topics: List[Dict[str, Any]] = None
    assignments: List[Dict[str, Any]] = None
    grading: Dict[str, float] = None
    schedule: List[Dict[str, Any]] = None
    resources: List[str] = None
    exam_format: Dict[str, Any] = None
    # New fields for better question-answering support
    key_concepts: List[Dict[str, Any]] = None
    common_questions: List[Dict[str, Any]] = None
    topic_relationships: List[Dict[str, Any]] = None
    difficulty_levels: Dict[str, str] = None
    assessment_patterns: List[Dict[str, Any]] = None

class SyllabusProcessor:
    def __init__(self, raw_data_dir: str, processed_data_dir: str):
        self.raw_data_dir = Path(raw_data_dir)
        self.processed_data_dir = Path(processed_data_dir)
        self.processed_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize NLP
        self.nlp = spacy.load("en_core_web_sm")
        
        # Updated patterns for H2 Mathematics syllabus
        self.section_patterns = {
            'course_code': r'CLES\s*\d{4}',
            'paper_section': r'PAPER\s+(\d+)\s*\((\d+)\s*hours\)',
            'topic_number': r'(\d+)(?:\.(\d+))?',  # Matches both main topics and subtopics
            'mathematical_expression': r'(?:[∑∫∏√π±×÷=≠≤≥∈∉⊂⊃∪∩]|[a-zA-Z]\([^)]*\)|[0-9]+!|[a-zA-Z]+\s*=\s*[^=]+)',
            'equation': r'[a-zA-Z]+\s*=\s*[^=]+',
            'vector': r'[a-zA-Z]\s*=\s*\([^)]+\)',
            'matrix': r'\[[^\]]+\]',
            'exam_format': r'Format:?\s*([^\n]+)',
            'duration': r'Duration:?\s*([^\n]+)',
            'weightage': r'Weightage:?\s*([^\n]+)',
            'calculator': r'Calculator:?\s*([^\n]+)',
            'topics': r'Topics:?\s*([^\n]+)',
            'include': r'Include:',
            'exclude': r'Exclude:',
            'bullet_point': r'•\s*([^\n]+)',
            'learning_objective': r'Learning\s+Objective[s]?:?\s*([^\n]+)',
            'key_concept': r'Key\s+Concept[s]?:?\s*([^\n]+)',
            'prerequisite': r'Prerequisite[s]?:?\s*([^\n]+)',
            'difficulty': r'Difficulty:?\s*([^\n]+)',
            'question_type': r'Question\s+Type[s]?:?\s*([^\n]+)'
        }
        
        # Mathematical symbols and expressions to preserve
        self.math_symbols = set('∑∫∏√π±×÷=≠≤≥∈∉⊂⊃∪∩')
        
        # Common mathematical functions
        self.math_functions = {
            'sin', 'cos', 'tan', 'log', 'ln', 'exp', 'sqrt', 'lim', 'sum', 'prod',
            'int', 'diff', 'grad', 'div', 'curl', 'det', 'tr', 'rank', 'norm'
        }
        
        # Common question types in mathematics
        self.question_types = {
            'proof': ['prove', 'show', 'demonstrate', 'verify'],
            'calculation': ['calculate', 'compute', 'evaluate', 'find'],
            'application': ['apply', 'use', 'implement', 'solve'],
            'analysis': ['analyze', 'examine', 'investigate', 'determine'],
            'explanation': ['explain', 'describe', 'justify', 'interpret']
        }
    
    def load_syllabus(self, file_path: Path) -> str:
        """Load syllabus content from PDF or DOCX file."""
        if file_path.suffix.lower() == '.pdf':
            loader = PyPDFLoader(str(file_path))
        elif file_path.suffix.lower() == '.docx':
            loader = Docx2txtLoader(str(file_path))
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
        
        docs = loader.load()
        return "\n".join(doc.page_content for doc in docs)
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        # Remove line breaks within mathematical expressions
        text = re.sub(r'([∑∫∏√π±×÷=≠≤≥∈∉⊂⊃∪∩])\s*\n\s*', r'\1', text)
        # Fix common OCR issues
        text = text.replace('ﬁ', 'fi').replace('ﬂ', 'fl')
        # Fix split mathematical expressions
        text = re.sub(r'([a-zA-Z])\s*\n\s*([a-zA-Z])', r'\1\2', text)
        return text.strip()
    
    def merge_math_expressions(self, lines: List[str]) -> List[str]:
        """Merge mathematical expressions that span multiple lines."""
        merged_lines = []
        current_line = ""
        in_math_expression = False
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_line:
                    merged_lines.append(current_line)
                    current_line = ""
                merged_lines.append(line)
                continue
            
            # Check if this line starts or continues a mathematical expression
            if re.search(self.section_patterns['mathematical_expression'], line):
                if current_line:
                    current_line += " " + line
                else:
                    current_line = line
                in_math_expression = True
            else:
                if current_line and in_math_expression:
                    merged_lines.append(current_line)
                    current_line = ""
                    in_math_expression = False
                merged_lines.append(line)
        
        if current_line:
            merged_lines.append(current_line)
        
        return merged_lines
    
    def extract_mathematical_content(self, text: str) -> List[Dict[str, Any]]:
        """Extract mathematical content and structure it."""
        topics = []
        current_topic = None
        current_subtopic = None
        
        # Split text into lines and clean
        lines = [self.clean_text(line) for line in text.split('\n')]
        lines = self.merge_math_expressions(lines)
        
        # Skip header content until we find the first real topic
        start_index = 0
        for i, line in enumerate(lines):
            if "CONTENT OUTLINE" in line:
                start_index = i + 1
                break
        
        for line in lines[start_index:]:
            if not line.strip():
                continue
            
            # Skip page numbers and headers
            if re.match(r'^\d+$', line.strip()) or "PAGE" in line.upper():
                continue
                
            # Check for main topic number (only match numbers followed by a title)
            topic_match = re.search(r'^(\d+)\s+([A-Za-z\s]+)', line)
            if topic_match:
                main_topic_num = topic_match.group(1)
                title = topic_match.group(2).strip()
                
                # Skip if this is a page number or header
                if len(title) < 2 or title.upper() in ["PAGE", "CONTENTS", "PREAMBLE"]:
                    continue
                
                if current_topic:
                    topics.append(current_topic)
                current_topic = {
                    'number': int(main_topic_num),
                    'title': title,
                    'content': [],
                    'formulas': [],
                    'subtopics': [],
                    'include': [],
                    'exclude': []
                }
                current_subtopic = None
            
            # Check for subtopic (indented or numbered like 1.1, 1.2, etc.)
            elif current_topic and (line.startswith(' ') or re.match(r'^\d+\.\d+\s+', line)):
                subtopic_match = re.search(r'(\d+\.\d+)\s+([A-Za-z\s]+)', line)
                if subtopic_match:
                    subtopic_num = subtopic_match.group(1)
                    title = subtopic_match.group(2).strip()
                    current_subtopic = {
                        'number': subtopic_num,
                        'title': title,
                        'content': [],
                        'formulas': [],
                        'include': [],
                        'exclude': []
                    }
                    current_topic['subtopics'].append(current_subtopic)
            
            # Process content
            elif current_subtopic or current_topic:
                target = current_subtopic if current_subtopic else current_topic
                
                # Check for Include/Exclude sections
                if re.search(self.section_patterns['include'], line):
                    target['include'] = []
                    continue
                elif re.search(self.section_patterns['exclude'], line):
                    target['exclude'] = []
                    continue
                
                # Extract mathematical expressions
                math_expressions = re.findall(self.section_patterns['mathematical_expression'], line)
                if math_expressions:
                    target['formulas'].extend(math_expressions)
                
                # Process bullet points
                bullet_match = re.search(self.section_patterns['bullet_point'], line)
                if bullet_match:
                    content = bullet_match.group(1).strip()
                    if content:
                        if target['include'] is not None and target['include']:
                            target['include'].append(content)
                        elif target['exclude'] is not None and target['exclude']:
                            target['exclude'].append(content)
                        else:
                            target['content'].append(content)
                else:
                    # Only add non-empty content
                    content = line.strip()
                    if content and not content.startswith('(') and not content.endswith(')'):
                        if target['include'] is not None and target['include']:
                            target['include'].append(content)
                        elif target['exclude'] is not None and target['exclude']:
                            target['exclude'].append(content)
                        else:
                            target['content'].append(content)
        
        # Add the last topic
        if current_topic:
            topics.append(current_topic)
        
        return topics
    
    def extract_exam_format(self, text: str) -> Dict[str, Any]:
        """Extract exam format details."""
        exam_format = {}
        
        # Extract format
        format_match = re.search(self.section_patterns['exam_format'], text)
        if format_match:
            exam_format['format'] = format_match.group(1).strip()
        
        # Extract duration
        duration_match = re.search(self.section_patterns['duration'], text)
        if duration_match:
            exam_format['duration'] = duration_match.group(1).strip()
        
        # Extract weightage
        weightage_match = re.search(self.section_patterns['weightage'], text)
        if weightage_match:
            exam_format['weightage'] = weightage_match.group(1).strip()
        
        # Extract calculator policy
        calculator_match = re.search(self.section_patterns['calculator'], text)
        if calculator_match:
            exam_format['calculator'] = calculator_match.group(1).strip()
        
        return exam_format
    
    def extract_learning_objectives(self, text: str) -> List[str]:
        """Extract learning objectives from the syllabus."""
        objectives = []
        
        # Look for the "SYLLABUS AIMS" section
        aims_section = re.search(r'SYLLABUS AIMS(.*?)(?=ASSESSMENT OBJECTIVES|$)', text, re.DOTALL)
        if aims_section:
            aims_text = aims_section.group(1)
            # Extract objectives from the aims section
            for line in aims_text.split('\n'):
                if re.match(r'^[a-d]\)', line.strip()):
                    objectives.append(line.strip())
        
        # Also look for explicit learning objectives
        for match in re.finditer(self.section_patterns['learning_objective'], text):
            objectives.extend([obj.strip() for obj in match.group(1).split(',')])
        
        return objectives

    def extract_key_concepts(self, text: str) -> List[Dict[str, Any]]:
        """Extract key concepts and their relationships."""
        concepts = []
        for match in re.finditer(self.section_patterns['key_concept'], text):
            concept_text = match.group(1).strip()
            # Extract mathematical expressions within the concept
            math_exprs = re.findall(self.section_patterns['mathematical_expression'], concept_text)
            concepts.append({
                'concept': concept_text,
                'mathematical_expressions': math_exprs,
                'related_topics': self._find_related_topics(concept_text)
            })
        return concepts

    def _find_related_topics(self, text: str) -> List[str]:
        """Find topics related to a given text using NLP."""
        doc = self.nlp(text)
        related_topics = []
        
        # Find topic numbers mentioned in the text
        topic_matches = re.finditer(self.section_patterns['topic_number'], text)
        for match in topic_matches:
            related_topics.append(match.group(0))
        
        # Find mathematical functions and symbols
        for token in doc:
            if token.text in self.math_functions:
                related_topics.append(f"Mathematical Function: {token.text}")
        
        return related_topics

    def extract_assessment_patterns(self, text: str) -> List[Dict[str, Any]]:
        """Extract common assessment patterns and question types."""
        patterns = []
        
        # Extract Assessment Objectives (AO)
        ao_section = re.search(r'ASSESSMENT OBJECTIVES.*?(?=USE OF A GRAPHING CALCULATOR|$)', text, re.DOTALL)
        if ao_section:
            ao_text = ao_section.group(0)
            for line in ao_text.split('\n'):
                if re.match(r'^AO\d+', line.strip()):
                    patterns.append({
                        'type': 'assessment_objective',
                        'description': line.strip(),
                        'keywords': self._extract_keywords(line)
                    })
        
        # Extract question types
        for match in re.finditer(self.section_patterns['question_type'], text):
            question_types = [qt.strip() for qt in match.group(1).split(',')]
            for qt in question_types:
                for category, keywords in self.question_types.items():
                    if any(keyword in qt.lower() for keyword in keywords):
                        patterns.append({
                            'type': category,
                            'description': qt,
                            'keywords': [k for k in keywords if k in qt.lower()]
                        })
        
        return patterns

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from text."""
        doc = self.nlp(text.lower())
        keywords = []
        
        # Extract mathematical functions and symbols
        for token in doc:
            if token.text in self.math_functions:
                keywords.append(token.text)
        
        # Extract topic numbers
        topic_matches = re.finditer(self.section_patterns['topic_number'], text)
        for match in topic_matches:
            keywords.append(match.group(0))
        
        return keywords

    def extract_course_info(self, text: str) -> CourseInfo:
        """Extract structured information from syllabus text."""
        course_info = CourseInfo()
        
        # Extract course code
        course_code_match = re.search(self.section_patterns['course_code'], text)
        if course_code_match:
            course_info.course_code = course_code_match.group(0)
        
        # Extract paper sections
        paper_sections = re.findall(self.section_patterns['paper_section'], text)
        if paper_sections:
            course_info.course_name = f"Paper {paper_sections[0][0]} ({paper_sections[0][1]} hours)"
        
        # Extract topics with mathematical content
        course_info.topics = self.extract_mathematical_content(text)
        
        # Extract exam format
        course_info.exam_format = self.extract_exam_format(text)
        
        # Extract new fields
        course_info.objectives = self.extract_learning_objectives(text)
        course_info.key_concepts = self.extract_key_concepts(text)
        course_info.common_questions = self.extract_assessment_patterns(text)
        
        # Extract prerequisites
        prereq_match = re.search(self.section_patterns['prerequisite'], text)
        if prereq_match:
            course_info.prerequisites = [p.strip() for p in prereq_match.group(1).split(',')]
        
        # Extract difficulty levels
        difficulty_match = re.search(self.section_patterns['difficulty'], text)
        if difficulty_match:
            course_info.difficulty_levels = {
                'overall': difficulty_match.group(1).strip(),
                'by_topic': self._extract_topic_difficulties(text)
            }
        
        return course_info

    def _extract_topic_difficulties(self, text: str) -> Dict[str, str]:
        """Extract difficulty levels for individual topics."""
        difficulties = {}
        current_topic = None
        
        for line in text.split('\n'):
            topic_match = re.search(self.section_patterns['topic_number'], line)
            if topic_match:
                current_topic = topic_match.group(0)
            elif current_topic and 'difficulty' in line.lower():
                difficulties[current_topic] = line.split(':', 1)[1].strip()
        
        return difficulties
    
    def process_syllabus(self, file_path: Path) -> Dict[str, Any]:
        """Process a single syllabus file and return structured data."""
        print(f"Processing syllabus: {file_path.name}")
        
        # Load syllabus content
        content = self.load_syllabus(file_path)
        
        # Extract information
        course_info = self.extract_course_info(content)
        
        # Convert to dictionary and add metadata
        result = asdict(course_info)
        result['metadata'] = {
            'source_file': str(file_path),
            'processed_date': datetime.now().isoformat(),
            'file_type': file_path.suffix.lower()[1:]
        }
        
        return result
    
    def process_all_syllabi(self):
        """Process all syllabus files in the raw_data directory."""
        if not self.raw_data_dir.exists():
            print(f"Raw data directory not found: {self.raw_data_dir}")
            return
        
        results = []
        for file_path in self.raw_data_dir.glob('*'):
            if file_path.suffix.lower() in ['.pdf', '.docx']:
                try:
                    result = self.process_syllabus(file_path)
                    results.append(result)
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
        
        # Save results
        output_file = self.processed_data_dir / 'syllabus_data.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"Processed {len(results)} syllabi. Results saved to {output_file}")

if __name__ == "__main__":
    processor = SyllabusProcessor(
        raw_data_dir="raw_data",
        processed_data_dir="processed_data"
    )
    processor.process_all_syllabi() 