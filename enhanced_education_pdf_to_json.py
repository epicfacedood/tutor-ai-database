#!/usr/bin/env python3
import os
import json
import argparse
import subprocess
import PyPDF2
import tempfile
import re
from datetime import datetime
from enhanced_prompts import get_enhanced_extraction_prompt, get_syllabus_mapping_prompt, get_question_generation_prompt, get_concept_relationship_prompt

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text += page.extract_text() + "\n\n"
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None

def chunk_text(text, max_chunk_size=4000):
    """Split text into manageable chunks."""
    words = text.split()
    chunks = []
    current_chunk = []
    current_size = 0
    
    for word in words:
        if current_size + len(word) + 1 > max_chunk_size:
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
            current_size = len(word)
        else:
            current_chunk.append(word)
            current_size += len(word) + 1  # +1 for the space
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
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
    
    # Try to extract education level
    if "jc" in filename.lower() or "jc" in text.lower() or "a level" in text.lower():
        metadata["education_level"] = "JC / A Level"
    elif "secondary" in filename.lower() or "secondary" in text.lower() or "o level" in text.lower():
        metadata["education_level"] = "Secondary / O Level"
    else:
        metadata["education_level"] = "JC / A Level"  # Default based on syllabus
    
    return metadata

def process_with_deepseek(text, metadata, json_schema=None, syllabus_text=None):
    """Process text with DeepSeek model to convert to educational JSON."""
    # Get the enhanced prompt
    prompt = get_enhanced_extraction_prompt(text, metadata, json_schema)
    
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
        
        # Find JSON in the output (between triple backticks if present)
        json_start = output.find("```json")
        if json_start != -1:
            json_start += 7  # Skip ```json
            json_end = output.find("```", json_start)
            if json_end != -1:
                output = output[json_start:json_end].strip()
        
        # Try to parse as JSON to validate
        try:
            parsed_json = json.loads(output)
            # Add the extracted metadata
            if "metadata" in parsed_json:
                parsed_json["metadata"].update(metadata)
            else:
                parsed_json["metadata"] = metadata
            
            # If we have syllabus text, enhance with syllabus mapping
            if syllabus_text:
                syllabus_mapping = process_syllabus_mapping(text, syllabus_text, metadata)
                if syllabus_mapping:
                    parsed_json["syllabus_mapping"] = syllabus_mapping
            
            # Generate additional practice questions
            additional_questions = generate_practice_questions(parsed_json)
            if additional_questions and "generated_questions" in additional_questions:
                if "content" not in parsed_json:
                    parsed_json["content"] = {}
                if "practice_questions" not in parsed_json["content"]:
                    parsed_json["content"]["practice_questions"] = []
                parsed_json["content"]["practice_questions"].extend(additional_questions["generated_questions"])
            
            # Analyze concept relationships
            concept_relationships = analyze_concept_relationships(parsed_json, syllabus_text)
            if concept_relationships:
                parsed_json["relationships"] = concept_relationships
            
            return parsed_json
        except json.JSONDecodeError as e:
            # If we can't parse the whole output, try to find JSON-like content
            import re
            json_pattern = r'\{.*\}'
            match = re.search(json_pattern, output, re.DOTALL)
            if match:
                try:
                    json_text = match.group(0)
                    # Fix common JSON issues
                    json_text = json_text.replace("\\(", "").replace("\\)", "")
                    json_text = json_text.replace("\\", "\\\\")
                    parsed_json = json.loads(json_text)
                    # Add the extracted metadata
                    if "metadata" in parsed_json:
                        parsed_json["metadata"].update(metadata)
                    else:
                        parsed_json["metadata"] = metadata
                    return parsed_json
                except json.JSONDecodeError as e2:
                    print(f"Secondary JSON parsing error: {e2}")
            
            print(f"Could not parse JSON from model output. Error: {e}")
            print("Raw output:")
            print(output)
            
            # Save the raw output as a fallback
            fallback_json = {
                "metadata": metadata,
                "raw_content": output,
                "parsing_error": str(e)
            }
            return fallback_json
            
    except subprocess.CalledProcessError as e:
        print(f"Error running DeepSeek model: {e}")
        print(f"Error output: {e.stderr}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

def process_syllabus_mapping(text, syllabus_text, metadata):
    """Process syllabus mapping with DeepSeek model."""
    # Get the syllabus mapping prompt
    prompt = get_syllabus_mapping_prompt(text, syllabus_text, metadata)
    
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
        
        # Find JSON in the output (between triple backticks if present)
        json_start = output.find("```json")
        if json_start != -1:
            json_start += 7  # Skip ```json
            json_end = output.find("```", json_start)
            if json_end != -1:
                output = output[json_start:json_end].strip()
        
        # Try to parse as JSON
        try:
            parsed_json = json.loads(output)
            return parsed_json
        except json.JSONDecodeError:
            print("Could not parse syllabus mapping JSON")
            return None
            
    except Exception as e:
        print(f"Error processing syllabus mapping: {e}")
        return None

def generate_practice_questions(content_json):
    """Generate additional practice questions with DeepSeek model."""
    # Get the question generation prompt
    prompt = get_question_generation_prompt(content_json)
    
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
        
        # Find JSON in the output (between triple backticks if present)
        json_start = output.find("```json")
        if json_start != -1:
            json_start += 7  # Skip ```json
            json_end = output.find("```", json_start)
            if json_end != -1:
                output = output[json_start:json_end].strip()
        
        # Try to parse as JSON
        try:
            parsed_json = json.loads(output)
            return parsed_json
        except json.JSONDecodeError:
            print("Could not parse generated questions JSON")
            return None
            
    except Exception as e:
        print(f"Error generating practice questions: {e}")
        return None

def analyze_concept_relationships(content_json, syllabus_text=None):
    """Analyze relationships between concepts with DeepSeek model."""
    # Get the concept relationship prompt
    prompt = get_concept_relationship_prompt(content_json, syllabus_text)
    
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
        
        # Find JSON in the output (between triple backticks if present)
        json_start = output.find("```json")
        if json_start != -1:
            json_start += 7  # Skip ```json
            json_end = output.find("```", json_start)
            if json_end != -1:
                output = output[json_start:json_end].strip()
        
        # Try to parse as JSON
        try:
            parsed_json = json.loads(output)
            return parsed_json
        except json.JSONDecodeError:
            print("Could not parse concept relationships JSON")
            return None
            
    except Exception as e:
        print(f"Error analyzing concept relationships: {e}")
        return None

def pdf_to_educational_json(pdf_path, output_path=None, json_schema=None, syllabus_path=None, generate_questions=False, analyze_relationships=False):
    """Convert a PDF to educational JSON using DeepSeek model with enhanced features."""
    # Extract text from PDF
    text = extract_text_from_pdf(pdf_path)
    if not text:
        return False
    
    # Extract metadata
    metadata = extract_metadata(pdf_path, text)
    
    # Extract syllabus text if provided
    syllabus_text = None
    if syllabus_path:
        syllabus_text = extract_text_from_pdf(syllabus_path)
    
    # Split into chunks if text is too long
    chunks = chunk_text(text)
    
    # Process each chunk and combine results
    results = []
    for i, chunk in enumerate(chunks):
        print(f"Processing chunk {i+1}/{len(chunks)}...")
        result = process_with_deepseek(chunk, metadata, json_schema, syllabus_text)
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
                "practice_questions": [],
                "worked_examples": []
            },
            "relationships": {}
        }
        
        # Combine content from all chunks
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
                
                # Combine worked examples
                if "worked_examples" in result["content"]:
                    combined_result["content"]["worked_examples"].extend(result["content"]["worked_examples"])
            
            # Combine relationships
            if "relationships" in result:
                for key, value in result["relationships"].items():
                    if key not in combined_result["relationships"]:
                        combined_result["relationships"][key] = value
                    elif isinstance(value, list):
                        combined_result["relationships"][key].extend(value)
            
            # Combine syllabus mapping
            if "syllabus_mapping" in result:
                if "syllabus_mapping" not in combined_result:
                    combined_result["syllabus_mapping"] = result["syllabus_mapping"]
                elif isinstance(result["syllabus_mapping"], dict):
                    for key, value in result["syllabus_mapping"].items():
                        if key not in combined_result["syllabus_mapping"]:
                            combined_result["syllabus_mapping"][key] = value
                        elif isinstance(value, list):
                            combined_result["syllabus_mapping"][key].extend(value)
        
        # Remove duplicates from lists
        if "relationships" in combined_result:
            for key, value in combined_result["relationships"].items():
                if isinstance(value, list):
                    combined_result["relationships"][key] = list(set(value))
    else:
        combined_result = results[0] if results else {}
    
    # Save to file if output path is provided
    if output_path:
        with open(output_path, 'w') as f:
            json.dump(combined_result, f, indent=2)
        print(f"Enhanced educational JSON saved to {output_path}")
    
    return combined_result

def main():
    parser = argparse.ArgumentParser(description='Convert educational PDF to enhanced structured JSON using DeepSeek model')
    parser.add_argument('pdf_path', help='Path to the PDF file')
    parser.add_argument('-o', '--output', help='Output JSON file path')
    parser.add_argument('-s', '--schema', help='Optional JSON schema file path')
    parser.add_argument('-y', '--syllabus', help='Path to syllabus PDF for mapping')
    parser.add_argument('-q', '--generate-questions', action='store_true', help='Generate additional practice questions')
    parser.add_argument('-r', '--analyze-relationships', action='store_true', help='Analyze concept relationships')
    parser.add_argument('-t', '--topic', help='Override topic detection')
    parser.add_argument('-l', '--level', help='Override education level detection')
    
    args = parser.parse_args()
    
    # Load schema if provided
    json_schema = None
    if args.schema:
        try:
            with open(args.schema, 'r') as f:
                json_schema = f.read()
        except Exception as e:
            print(f"Error loading schema file: {e}")
            return 1
    
    output_path = args.output or f"{os.path.splitext(args.pdf_path)[0]}_enhanced.json"
    
    result = pdf_to_educational_json(
        args.pdf_path, 
        output_path, 
        json_schema, 
        args.syllabus,
        args.generate_questions,
        args.analyze_relationships
    )
    
    if result:
        print("Successfully converted PDF to enhanced educational JSON")
        return 0
    else:
        print("Failed to convert PDF to enhanced educational JSON")
        return 1

if __name__ == "__main__":
    exit(main()) 