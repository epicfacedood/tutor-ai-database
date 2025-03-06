#!/usr/bin/env python3
import os
import json
import argparse
import subprocess
import re
from datetime import datetime
import traceback

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file with robust error handling."""
    try:
        # First try PyPDF2
        import PyPDF2
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    text += page.extract_text() + "\n\n"
            if text.strip():  # If we got meaningful text
                return text
        except Exception as e:
            print(f"PyPDF2 extraction failed: {e}")
            # Continue to next method if PyPDF2 fails
        
        # If PyPDF2 fails or returns empty text, try pdftotext if available
        try:
            import subprocess
            result = subprocess.run(
                ["pdftotext", pdf_path, "-"],
                capture_output=True,
                text=True,
                check=True
            )
            text = result.stdout
            if text.strip():  # If we got meaningful text
                return text
        except Exception as e:
            print(f"pdftotext extraction failed: {e}")
            # Continue to next method if pdftotext fails
        
        # If all else fails, try a simple approach with PyPDF2 that ignores errors
        try:
            text = ""
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page_num in range(len(reader.pages)):
                    try:
                        page = reader.pages[page_num]
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n\n"
                    except:
                        # Skip pages that cause errors
                        continue
            return text
        except Exception as e:
            print(f"Fallback extraction failed: {e}")
            
        # If we get here, all extraction methods failed
        return "Failed to extract text from PDF."
    except Exception as e:
        print(f"Error in extract_text_from_pdf: {e}")
        return "Failed to extract text from PDF due to unexpected error."

def chunk_text(text, max_chunk_size=3000):
    """Split text into manageable chunks with smaller default size."""
    # Handle empty or None text
    if not text:
        return ["No text content available."]
    
    # Split by paragraphs first to preserve structure
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = []
    current_size = 0
    
    for paragraph in paragraphs:
        # If a single paragraph is too large, split it by sentences
        if len(paragraph) > max_chunk_size:
            sentences = re.split(r'(?<=[.!?])\s+', paragraph)
            for sentence in sentences:
                if current_size + len(sentence) + 2 > max_chunk_size:  # +2 for newlines
                    chunks.append("\n\n".join(current_chunk))
                    current_chunk = [sentence]
                    current_size = len(sentence)
                else:
                    current_chunk.append(sentence)
                    current_size += len(sentence) + 2  # +2 for newlines
        # Otherwise add the whole paragraph if it fits
        elif current_size + len(paragraph) + 2 > max_chunk_size:  # +2 for newlines
            chunks.append("\n\n".join(current_chunk))
            current_chunk = [paragraph]
            current_size = len(paragraph)
        else:
            current_chunk.append(paragraph)
            current_size += len(paragraph) + 2  # +2 for newlines
    
    if current_chunk:
        chunks.append("\n\n".join(current_chunk))
    
    # Ensure we have at least one chunk
    if not chunks:
        chunks = ["No meaningful content could be extracted."]
    
    return chunks

def extract_metadata(pdf_path, text):
    """Extract metadata from the PDF file and its content."""
    metadata = {
        "filename": os.path.basename(pdf_path),
        "file_path": pdf_path,
        "file_size_bytes": os.path.getsize(pdf_path),
        "processed_date": datetime.now().isoformat(),
    }
    
    # Try to extract subject from filename or content
    filename = os.path.basename(pdf_path).lower()
    if "math" in filename:
        metadata["subject"] = "Mathematics"
    elif "physics" in filename:
        metadata["subject"] = "Physics"
    elif "chem" in filename:
        metadata["subject"] = "Chemistry"
    elif "bio" in filename:
        metadata["subject"] = "Biology"
    elif "econs" in filename or "economics" in filename:
        metadata["subject"] = "Economics"
    else:
        # Default to Mathematics based on the syllabus we saw
        metadata["subject"] = "Mathematics"
    
    # Try to extract topic from content
    topic_patterns = [
        (r"chapter\s*\d+\s*:\s*([\w\s]+)", "Chapter title"),
        (r"topic\s*\d*\s*:\s*([\w\s]+)", "Topic"),
        (r"section\s*\d+\s*:\s*([\w\s]+)", "Section"),
    ]
    
    for pattern, key in topic_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            metadata["topic"] = matches[0].strip()
            break
    
    # If no topic found, use filename without extension
    if "topic" not in metadata:
        metadata["topic"] = os.path.splitext(os.path.basename(pdf_path))[0]
    
    # Try to extract education level
    if "jc" in filename.lower() or "jc" in text.lower() or "a level" in text.lower():
        metadata["education_level"] = "JC / A Level"
    elif "secondary" in filename.lower() or "secondary" in text.lower() or "o level" in text.lower():
        metadata["education_level"] = "Secondary / O Level"
    else:
        metadata["education_level"] = "JC / A Level"  # Default based on syllabus
    
    return metadata

def fix_json_string(json_str):
    """Attempt to fix common JSON formatting issues."""
    # Handle None or empty string
    if not json_str:
        return "{}"
    
    # Remove any thinking or non-JSON content
    think_pattern = r'<think>.*?</think>'
    json_str = re.sub(think_pattern, '', json_str, flags=re.DOTALL)
    
    # Try to extract JSON from markdown code blocks
    json_block_pattern = r'```(?:json)?\s*([\s\S]*?)```'
    json_blocks = re.findall(json_block_pattern, json_str)
    if json_blocks:
        json_str = json_blocks[0]
    
    # Replace common LaTeX-style escapes that might cause issues
    json_str = json_str.replace('\\\\', '\\')
    
    # Fix missing commas between array elements
    json_str = re.sub(r'(\w+"|")\s*\n\s*("|\w+)', r'\1,\n\2', json_str)
    
    # Fix missing commas between object properties
    json_str = re.sub(r'(true|false|null|"[^"]*"|[0-9]+)\s*\n\s*(")', r'\1,\n\2', json_str)
    
    # Fix trailing commas in arrays and objects
    json_str = re.sub(r',\s*(\]|\})', r'\1', json_str)
    
    # Fix missing quotes around property names
    json_str = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', json_str)
    
    # Fix unescaped quotes in strings
    # This is tricky and might cause issues, so we'll skip it for now
    
    # Fix unescaped backslashes in strings
    json_str = re.sub(r'([^\\])\\([^"\\/bfnrtu])', r'\1\\\\\2', json_str)
    
    # Ensure the string starts with { and ends with }
    json_str = json_str.strip()
    if not json_str.startswith('{'):
        json_str = '{' + json_str
    if not json_str.endswith('}'):
        json_str = json_str + '}'
    
    return json_str

def extract_json_from_text(text):
    """Extract JSON from text, handling various formats."""
    # If it's already a dictionary, return it
    if isinstance(text, dict):
        return text
        
    # Handle None or empty string
    if not text:
        return None
    
    # Try to find JSON between triple backticks
    json_start = text.find("```json")
    if json_start != -1:
        json_start += 7  # Skip ```json
        json_end = text.find("```", json_start)
        if json_end != -1:
            json_str = text[json_start:json_end].strip()
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                print(f"JSON parsing error in triple backticks: {e}")
    
    # Try to find JSON between single backticks
    json_start = text.find("`{")
    if json_start != -1:
        json_start += 1  # Skip `
        json_end = text.find("}`", json_start)
        if json_end != -1:
            json_str = text[json_start:json_end+1].strip()
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                print(f"JSON parsing error in single backticks: {e}")
    
    # Try to find JSON between curly braces
    first_brace = text.find('{')
    last_brace = text.rfind('}')
    if first_brace != -1 and last_brace != -1 and first_brace < last_brace:
        json_str = text[first_brace:last_brace+1]
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"Primary JSON parsing error: {e}")
            print("Creating fallback JSON structure...")
    
    # If all else fails, return None
    return None

def create_fallback_json(text, metadata):
    """Create a simple structured JSON when parsing fails."""
    # Extract what looks like key concepts
    concepts = []
    
    # Look for definitions or key terms
    definition_patterns = [
        r'([A-Z][a-zA-Z\s]+):\s*([^\.]+\.)',  # Capitalized term followed by colon and definition
        r'([A-Z][a-zA-Z\s]+)\s+is\s+([^\.]+\.)',  # Capitalized term followed by "is" and definition
        r'Definition[:\s]+([^\.]+\.)',  # Definition followed by text
    ]
    
    for pattern in definition_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if isinstance(match, tuple):
                concept_name = match[0].strip()
                definition = match[1].strip()
            else:
                concept_name = "Definition"
                definition = match.strip()
            
            concepts.append({
                "concept_name": concept_name,
                "definition": definition
            })
    
    # Look for formulas
    formula_patterns = [
        r'([A-Za-z][^=\n]+)=([^\n]+)',  # Simple equation pattern
    ]
    
    for pattern in formula_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            formula = f"{match[0].strip()} = {match[1].strip()}"
            concepts.append({
                "concept_name": "Formula",
                "definition": "",
                "formulas": [formula]
            })
    
    # Extract what looks like practice questions
    questions = []
    question_patterns = [
        r'(\d+\.\s*[^\?]+\?)',  # Numbered question ending with ?
        r'(Question\s*\d+[^\.]+\.)',  # Question followed by number
    ]
    
    for pattern in question_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            questions.append({
                "question_text": match.strip(),
                "difficulty_level": "Medium",
                "solution": ""
            })
    
    # Create a simple summary
    summary = text[:200] + "..." if len(text) > 200 else text
    
    # Construct the fallback JSON
    fallback_json = {
        "metadata": metadata,
        "content": {
            "summary": summary,
            "key_concepts": concepts[:5],  # Limit to 5 concepts
            "practice_questions": questions[:3]  # Limit to 3 questions
        },
        "related_topics": [],
        "extraction_method": "fallback"
    }
    
    return fallback_json

def process_with_deepseek(text, metadata, json_schema=None):
    """Process text with DeepSeek model to convert to educational JSON."""
    # Create the prompt
    prompt = f"""Convert the following educational content into a structured JSON format suitable for a tutoring AI system.

METADATA:
- Subject: {metadata.get('subject', 'Mathematics')}
- Topic: {metadata.get('topic', 'Unknown')}
- Education Level: {metadata.get('education_level', 'JC / A Level')}

INSTRUCTIONS:
1. Identify the main topic and subtopics in the content
2. Extract key concepts, definitions, formulas, and examples
3. Identify any practice questions and their solutions
4. Structure the content hierarchically

IMPORTANT: Return ONLY valid JSON without any additional text or explanations. Ensure all JSON is properly formatted with correct commas, quotes, and brackets.

Use the following JSON structure:
{{
  "metadata": {{
    "subject": "string",
    "topic": "string",
    "subtopic": "string",
    "education_level": "string"
  }},
  "content": {{
    "summary": "string",
    "key_concepts": [
      {{
        "concept_name": "string",
        "definition": "string",
        "explanation": "string",
        "formulas": ["string"],
        "examples": [
          {{
            "problem_statement": "string",
            "solution": "string"
          }}
        ]
      }}
    ],
    "practice_questions": [
      {{
        "question_text": "string",
        "difficulty_level": "string",
        "solution": "string",
        "hints": ["string"]
      }}
    ]
  }},
  "related_topics": ["string"]
}}

TEXT:
{text}

Remember to return ONLY valid JSON with proper formatting."""
    
    try:
        # Run Ollama with the prompt
        result = subprocess.run(
            ["ollama", "run", "deepseek-r1:7b"],
            input=prompt,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Extract JSON from the output
        output = result.stdout.strip()
        
        # Extract JSON from the text
        json_text = extract_json_from_text(output)
        
        # Try to fix common JSON issues
        fixed_json = fix_json_string(json_text)
        
        # Try to parse as JSON to validate
        try:
            parsed_json = json.loads(fixed_json)
            # Add the extracted metadata
            if "metadata" in parsed_json:
                parsed_json["metadata"].update(metadata)
            else:
                parsed_json["metadata"] = metadata
            return parsed_json
        except json.JSONDecodeError as e1:
            print(f"Primary JSON parsing error: {e1}")
            
            # Try a more aggressive approach to extract JSON
            try:
                # Try to extract just the content part if it exists
                content_match = re.search(r'"content"\s*:\s*(\{[^}]*\})', fixed_json, re.DOTALL)
                if content_match:
                    content_json = '{"content": ' + content_match.group(1) + '}'
                    content_parsed = json.loads(content_json)
                    content_parsed["metadata"] = metadata
                    return content_parsed
            except Exception:
                pass
            
            # If all else fails, create a fallback JSON
            print("Creating fallback JSON structure...")
            fallback_json = create_fallback_json(text, metadata)
            return fallback_json
            
    except subprocess.CalledProcessError as e:
        print(f"Error running DeepSeek model: {e}")
        print(f"Error output: {e.stderr}")
        # Create a fallback JSON
        return create_fallback_json(text, metadata)
    except Exception as e:
        print(f"Unexpected error: {e}")
        print(traceback.format_exc())
        # Create a fallback JSON
        return create_fallback_json(text, metadata)

def pdf_to_educational_json(pdf_path, output_path=None, json_schema=None):
    """Convert a PDF to educational JSON using DeepSeek model."""
    # Extract text from PDF
    text = extract_text_from_pdf(pdf_path)
    if not text:
        print(f"Failed to extract text from {pdf_path}")
        # Create minimal metadata
        metadata = {
            "filename": os.path.basename(pdf_path),
            "file_path": pdf_path,
            "file_size_bytes": os.path.getsize(pdf_path),
            "processed_date": datetime.now().isoformat(),
            "subject": "Mathematics",
            "topic": os.path.splitext(os.path.basename(pdf_path))[0],
            "education_level": "JC / A Level",
            "extraction_error": "Failed to extract text from PDF"
        }
        
        # Create empty result
        result = {
            "metadata": metadata,
            "content": {
                "summary": "Failed to extract text from PDF",
                "key_concepts": [],
                "practice_questions": []
            },
            "related_topics": []
        }
        
        # Save to file if output path is provided
        if output_path:
            with open(output_path, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"Empty JSON saved to {output_path}")
        
        return result
    
    # Extract metadata
    metadata = extract_metadata(pdf_path, text)
    
    # Split into chunks if text is too long
    chunks = chunk_text(text)
    
    # Process each chunk and combine results
    results = []
    for i, chunk in enumerate(chunks):
        print(f"Processing chunk {i+1}/{len(chunks)}...")
        result = process_with_deepseek(chunk, metadata, json_schema)
        if result:
            results.append(result)
    
    # Combine results if multiple chunks
    if len(results) > 1:
        # More sophisticated combination for educational content
        combined_result = {
            "metadata": results[0]["metadata"],
            "content": {
                "summary": "",
                "key_concepts": [],
                "practice_questions": []
            },
            "related_topics": []
        }
        
        # Combine key concepts and practice questions from all chunks
        for result in results:
            if "content" in result:
                # Combine summaries
                if "summary" in result["content"]:
                    combined_result["content"]["summary"] += result["content"]["summary"] + " "
                
                # Combine key concepts
                if "key_concepts" in result["content"]:
                    combined_result["content"]["key_concepts"].extend(result["content"]["key_concepts"])
                
                # Combine practice questions
                if "practice_questions" in result["content"]:
                    combined_result["content"]["practice_questions"].extend(result["content"]["practice_questions"])
            
            # Combine related topics
            if "related_topics" in result:
                combined_result["related_topics"].extend(result["related_topics"])
        
        # Remove duplicates from related_topics
        if "related_topics" in combined_result:
            combined_result["related_topics"] = list(set(combined_result["related_topics"]))
    else:
        combined_result = results[0] if results else {
            "metadata": metadata,
            "content": {
                "summary": "Failed to process content",
                "key_concepts": [],
                "practice_questions": []
            },
            "related_topics": []
        }
    
    # Save to file if output path is provided
    if output_path:
        with open(output_path, 'w') as f:
            json.dump(combined_result, f, indent=2)
        print(f"Educational JSON saved to {output_path}")
    
    return combined_result

def is_solution_file(filename):
    """Check if a file is likely a solution file based on its name."""
    solution_keywords = [
        'solution', 'solutions', 'soln', 'solns', 'sol', 'sols',
        'answer', 'answers', 'ans', 'anss',
        'worked', 'worked example', 'worked examples',
        'key', 'keys', 'answer key', 'answer keys',
        'suggested solutions', 'suggested solution',
        'tutor', 'teacher', 'teachers', 'tutors'
    ]
    
    # Convert to lowercase for case-insensitive matching
    lower_filename = filename.lower()
    
    # Check for solution keywords
    for keyword in solution_keywords:
        # Use word boundary to match whole words
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, lower_filename):
            return True
    
    return False

def is_question_file(filename):
    """Check if a file is likely a question paper based on its name."""
    question_keywords = [
        'question', 'questions', 'qn', 'qns', 
        'problem', 'problems', 'exercise', 'exercises',
        'worksheet', 'worksheets', 'assignment', 'assignments',
        'practice', 'test', 'exam', 'quiz', 'tutorial',
        'student', 'package', 'revision'
    ]
    
    # Convert to lowercase for case-insensitive matching
    lower_filename = filename.lower()
    
    # Check for question keywords
    for keyword in question_keywords:
        # Use word boundary to match whole words
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, lower_filename):
            return True
    
    return False

def calculate_filename_similarity(file1, file2):
    """Calculate similarity between two filenames."""
    # Remove extensions
    base1 = os.path.splitext(file1)[0].lower()
    base2 = os.path.splitext(file2)[0].lower()
    
    # Remove common solution indicators
    for keyword in ['solution', 'solutions', 'soln', 'solns', 'sol', 'sols', 'answer', 'answers', 'ans', 'anss']:
        base1 = re.sub(r'(?i)(_|\s|-|^)' + keyword + r's?(?:_|\s|-|$)', '', base1)
        base2 = re.sub(r'(?i)(_|\s|-|^)' + keyword + r's?(?:_|\s|-|$)', '', base2)
    
    # Remove common question indicators
    for keyword in ['question', 'questions', 'qn', 'qns', 'problem', 'problems', 'exercise', 'exercises']:
        base1 = re.sub(r'(?i)(_|\s|-|^)' + keyword + r's?(?:_|\s|-|$)', '', base1)
        base2 = re.sub(r'(?i)(_|\s|-|^)' + keyword + r's?(?:_|\s|-|$)', '', base2)
    
    # Calculate word-based similarity
    words1 = set(re.findall(r'\w+', base1))
    words2 = set(re.findall(r'\w+', base2))
    
    if not words1 or not words2:
        return 0.0
    
    common_words = words1.intersection(words2)
    similarity = len(common_words) / max(len(words1), len(words2))
    
    return similarity

def find_question_solution_pairs(file_list, similarity_threshold=0.7):
    """Find question-solution pairs in a list of files."""
    # Identify solution files and question files
    solution_files = [f for f in file_list if is_solution_file(os.path.basename(f)) and not is_question_file(os.path.basename(f))]
    question_files = [f for f in file_list if is_question_file(os.path.basename(f)) and not is_solution_file(os.path.basename(f))]
    
    # Group similar files
    pairs = []
    paired_files = set()
    
    # For each solution file, try to find a matching question file
    for sol_file in solution_files:
        if sol_file in paired_files:
            continue
        
        best_match = None
        best_score = 0
        
        for q_file in question_files:
            if q_file in paired_files:
                continue
            
            similarity = calculate_filename_similarity(os.path.basename(sol_file), os.path.basename(q_file))
            if similarity > similarity_threshold and similarity > best_score:
                best_match = q_file
                best_score = similarity
        
        if best_match:
            # Found a pair
            pairs.append((sol_file, best_match))
            paired_files.add(sol_file)
            paired_files.add(best_match)
    
    # Look for similar files among the remaining files
    remaining_files = [f for f in file_list if f not in paired_files]
    
    for i, file1 in enumerate(remaining_files):
        if file1 in paired_files:
            continue
        
        for file2 in remaining_files[i+1:]:
            if file2 in paired_files:
                continue
            
            similarity = calculate_filename_similarity(os.path.basename(file1), os.path.basename(file2))
            if similarity > similarity_threshold:
                # Check if one is likely a solution and the other a question
                file1_is_sol = is_solution_file(os.path.basename(file1)) and not is_question_file(os.path.basename(file1))
                file2_is_sol = is_solution_file(os.path.basename(file2)) and not is_question_file(os.path.basename(file2))
                file1_is_q = is_question_file(os.path.basename(file1)) and not is_solution_file(os.path.basename(file1))
                file2_is_q = is_question_file(os.path.basename(file2)) and not is_solution_file(os.path.basename(file2))
                
                if (file1_is_sol and file2_is_q):
                    pairs.append((file1, file2))
                    paired_files.add(file1)
                    paired_files.add(file2)
                elif (file1_is_q and file2_is_sol):
                    pairs.append((file2, file1))
                    paired_files.add(file1)
                    paired_files.add(file2)
    
    # Return pairs and unpaired files
    unpaired_files = [f for f in file_list if f not in paired_files]
    return pairs, unpaired_files

def process_question_solution_pair(question_path, solution_path, output_path=None, json_schema=None):
    """Process a question-solution pair to create a combined JSON with properly matched questions and solutions."""
    print(f"Processing question-solution pair: {os.path.basename(question_path)} and {os.path.basename(solution_path)}")
    
    # Extract text from both files
    question_text = extract_text_from_pdf(question_path)
    solution_text = extract_text_from_pdf(solution_path)
    
    # Extract metadata from question file
    metadata = extract_metadata(question_path, question_text)
    metadata["document_type"] = "question_solution_pair"
    metadata["question_file"] = os.path.basename(question_path)
    metadata["solution_file"] = os.path.basename(solution_path)
    
    # Create a prompt that specifically asks for matching questions with solutions
    prompt = f"""
You are an expert educational content analyzer. You need to extract questions from a question document and match them with their solutions from a solution document.

QUESTION DOCUMENT:
{question_text[:5000]}

SOLUTION DOCUMENT:
{solution_text[:5000]}

Please analyze these documents and create a structured JSON with the following:
1. A brief summary of the topic covered
2. Key mathematical concepts presented
3. A list of practice questions with their corresponding solutions

For each practice question, include:
- The complete question text
- The corresponding solution from the solution document
- An estimated difficulty level (Easy, Medium, Hard)

Focus on creating clear mappings between questions and their solutions.
"""
    
    try:
        # Process with AI using a specialized prompt for question-solution pairs
        ai_response = process_with_deepseek(prompt, metadata, json_schema)
        result = extract_json_from_text(ai_response)
        
        if not result:
            print("Primary JSON extraction failed. Creating structured format manually...")
            # Create a more structured fallback
            result = {
                "metadata": metadata,
                "content": {
                    "summary": f"Combined document containing questions from {os.path.basename(question_path)} and solutions from {os.path.basename(solution_path)}",
                    "key_concepts": [],
                    "practice_questions": []
                },
                "extraction_method": "structured_fallback"
            }
            
            # Try to extract questions and solutions using pattern matching
            questions = extract_questions(question_text)
            
            for i, question in enumerate(questions, 1):
                # Try to find matching solution
                solution = find_matching_solution(question, solution_text)
                
                result["content"]["practice_questions"].append({
                    "question_number": i,
                    "question_text": question,
                    "solution": solution if solution else "Solution not found",
                    "difficulty_level": estimate_difficulty(question)
                })
    except Exception as e:
        print(f"Error processing with AI: {str(e)}")
        # Create a basic fallback
        result = {
            "metadata": metadata,
            "content": {
                "summary": f"Combined document containing questions from {os.path.basename(question_path)} and solutions from {os.path.basename(solution_path)}",
                "question_document": question_text[:1000],
                "solution_document": solution_text[:1000]
            },
            "extraction_method": "basic_fallback"
        }
    
    # Save the result
    if output_path:
        # Create output filename based on question filename
        base_name = os.path.splitext(os.path.basename(question_path))[0]
        output_file = os.path.join(output_path, f"{base_name}_combined.json")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"Saved combined JSON to {output_file}")
    
    return result

def extract_questions(text):
    """Extract individual questions from text using pattern matching."""
    # Look for common question patterns
    patterns = [
        r'(?:\d+\.\s*|\(\d+\)\s*|\[\d+\]\s*)([^\n]+(?:\n(?!\d+\.\s*|\(\d+\)\s*|\[\d+\]\s*)[^\n]+)*)',  # Numbered questions
        r'Question\s*\d+[:\.\)]\s*([^\n]+(?:\n(?!Question\s*\d+)[^\n]+)*)'  # "Question X:" format
    ]
    
    questions = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            questions.extend(matches)
    
    # If no questions found with patterns, try splitting by common separators
    if not questions:
        # Split by blank lines followed by potential question starters
        splits = re.split(r'\n\s*\n\s*(?=\d+\.|\(\d+\)|\[\d+\]|Question)', text)
        questions = [q.strip() for q in splits if len(q.strip()) > 20]  # Filter out very short segments
    
    return questions

def find_matching_solution(question, solution_text):
    """Find the solution that matches a given question."""
    # Extract key identifiers from the question
    question_words = re.sub(r'[^\w\s]', ' ', question.lower()).split()
    significant_words = [w for w in question_words if len(w) > 3 and w not in ['what', 'when', 'where', 'which', 'find', 'calculate', 'determine']]
    
    # Look for sections in the solution text that contain multiple significant words
    best_match = ""
    best_score = 0
    
    # Split solution text into potential solution chunks
    solution_chunks = re.split(r'\n\s*\n\s*(?=\d+\.|\(\d+\)|\[\d+\]|Solution)', solution_text)
    
    for chunk in solution_chunks:
        chunk_lower = chunk.lower()
        score = sum(1 for word in significant_words if word in chunk_lower)
        if score > best_score:
            best_score = score
            best_match = chunk
    
    # Only return if we have a reasonably good match
    if best_score > min(3, len(significant_words) / 2):
        return best_match.strip()
    return ""

def estimate_difficulty(question):
    """Estimate the difficulty of a question based on its content."""
    # Count indicators of difficulty
    lower_q = question.lower()
    
    # Check for advanced mathematical terms
    advanced_terms = ['prove', 'derive', 'show that', 'hence', 'therefore', 'deduce', 'complex', 'advanced']
    advanced_count = sum(1 for term in advanced_terms if term in lower_q)
    
    # Check question length - longer questions tend to be harder
    length_factor = len(question) / 200  # Normalize by typical question length
    
    # Calculate difficulty score
    difficulty_score = advanced_count + length_factor
    
    # Assign difficulty level
    if difficulty_score > 3:
        return "Hard"
    elif difficulty_score > 1.5:
        return "Medium"
    else:
        return "Easy"

def process_batch(file_list, output_dir, max_files=10):
    """Process a batch of files, identifying and processing question-solution pairs."""
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Find question-solution pairs
    print("Finding question-solution pairs...")
    pairs, unpaired_files = find_question_solution_pairs(file_list)
    
    print(f"Found {len(pairs)} question-solution pairs and {len(unpaired_files)} standalone files")
    
    # Process pairs first
    processed_count = 0
    for solution_path, question_path in pairs:
        if processed_count >= max_files:
            break
        
        try:
            process_question_solution_pair(question_path, solution_path, output_dir)
            processed_count += 1
        except Exception as e:
            print(f"Error processing pair {os.path.basename(question_path)} and {os.path.basename(solution_path)}: {e}")
    
    # Process remaining files
    for file_path in unpaired_files:
        if processed_count >= max_files:
            break
        
        try:
            pdf_to_educational_json(file_path, output_dir)
            processed_count += 1
        except Exception as e:
            print(f"Error processing file {os.path.basename(file_path)}: {e}")
    
    print(f"Processed {processed_count} files in total")

def main():
    """Main function to process PDF files."""
    parser = argparse.ArgumentParser(description='Convert educational PDFs to structured JSON.')
    parser.add_argument('--input', '-i', help='Input PDF file or directory')
    parser.add_argument('--output', '-o', help='Output JSON file or directory')
    parser.add_argument('--batch', '-b', action='store_true', help='Process all PDFs in the input directory')
    parser.add_argument('--max', '-m', type=int, default=10, help='Maximum number of files to process in batch mode')
    parser.add_argument('--schema', '-s', help='Path to JSON schema file')
    
    args = parser.parse_args()
    
    # Load JSON schema if provided
    json_schema = None
    if args.schema and os.path.exists(args.schema):
        try:
            with open(args.schema, 'r', encoding='utf-8') as f:
                json_schema = json.load(f)
            print(f"Loaded JSON schema from {args.schema}")
        except Exception as e:
            print(f"Error loading JSON schema: {e}")
    
    # Process in batch mode
    if args.batch:
        if not args.input or not os.path.isdir(args.input):
            print("Error: In batch mode, input must be a directory")
            return
        
        # Get all PDF files in the directory
        pdf_files = []
        for root, _, files in os.walk(args.input):
            for file in files:
                if file.lower().endswith('.pdf'):
                    pdf_files.append(os.path.join(root, file))
        
        if not pdf_files:
            print(f"No PDF files found in {args.input}")
            return
        
        # Set output directory
        output_dir = args.output if args.output else os.path.join(args.input, 'json_output')
        
        # Process the batch
        print(f"Found {len(pdf_files)} PDF files. Processing up to {args.max} files...")
        process_batch(pdf_files, output_dir, args.max)
    
    # Process a single file
    else:
        if not args.input or not os.path.isfile(args.input):
            print("Error: Input must be a PDF file")
            return
        
        if not args.input.lower().endswith('.pdf'):
            print("Error: Input must be a PDF file")
            return
        
        # Set output file
        output_file = args.output
        if not output_file:
            base_name = os.path.splitext(os.path.basename(args.input))[0]
            output_file = f"{base_name}.json"
        
        # Process the file
        result = pdf_to_educational_json(args.input, output_file, json_schema)
        if result:
            print(f"Successfully processed {args.input}")
        else:
            print(f"Failed to process {args.input}")

if __name__ == "__main__":
    main() 