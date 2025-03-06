#!/usr/bin/env python3
import os
import json
import argparse
import subprocess
import PyPDF2
import tempfile
import re
from datetime import datetime

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

def process_with_deepseek(text, metadata, json_schema=None):
    """Process text with DeepSeek model to convert to educational JSON."""
    # Create a temporary file to store the prompt
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp:
        # Create a detailed prompt for educational content
        prompt = f"""Convert the following educational content into a structured JSON format suitable for a tutoring AI system.

METADATA:
- Subject: {metadata.get('subject', 'Mathematics')}
- Topic: {metadata.get('topic', 'Unknown')}
- Education Level: {metadata.get('education_level', 'JC / A Level')}
- Filename: {metadata.get('filename', 'Unknown')}

INSTRUCTIONS:
1. Identify the main topic and subtopics in the content
2. Extract key concepts, definitions, formulas, and examples
3. Identify any practice questions and their solutions
4. Structure the content hierarchically (topics → subtopics → concepts → examples)
5. Include page references where available
6. Tag content with relevant syllabus references if possible

{f'Use the following JSON schema: {json_schema}' if json_schema else '''
Use the following JSON structure:
{
  "metadata": {
    "subject": "string",
    "topic": "string",
    "subtopic": "string",
    "education_level": "string",
    "syllabus_reference": "string",
    "source": "string"
  },
  "content": {
    "key_concepts": [
      {
        "concept_name": "string",
        "definition": "string",
        "explanation": "string",
        "formulas": ["string"],
        "examples": [
          {
            "example_text": "string",
            "solution": "string"
          }
        ]
      }
    ],
    "practice_questions": [
      {
        "question_text": "string",
        "difficulty_level": "string",
        "solution": "string",
        "hints": ["string"]
      }
    ]
  },
  "related_topics": ["string"]
}
'''}

TEXT:
{text}

Return only valid JSON without any additional text or explanations."""
        temp.write(prompt)
        temp_path = temp.name
    
    try:
        # Run Ollama with the prompt
        result = subprocess.run(
            ["ollama", "run", "deepseek-r1:7b"],
            input=prompt,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Clean up the temporary file
        os.unlink(temp_path)
        
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

def pdf_to_educational_json(pdf_path, output_path=None, json_schema=None):
    """Convert a PDF to educational JSON using DeepSeek model."""
    # Extract text from PDF
    text = extract_text_from_pdf(pdf_path)
    if not text:
        return False
    
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
                "key_concepts": [],
                "practice_questions": []
            },
            "related_topics": []
        }
        
        # Combine key concepts and practice questions from all chunks
        for result in results:
            if "content" in result:
                if "key_concepts" in result["content"]:
                    combined_result["content"]["key_concepts"].extend(result["content"]["key_concepts"])
                if "practice_questions" in result["content"]:
                    combined_result["content"]["practice_questions"].extend(result["content"]["practice_questions"])
            if "related_topics" in result:
                combined_result["related_topics"].extend(result["related_topics"])
        
        # Remove duplicates from related_topics
        if "related_topics" in combined_result:
            combined_result["related_topics"] = list(set(combined_result["related_topics"]))
    else:
        combined_result = results[0] if results else {}
    
    # Save to file if output path is provided
    if output_path:
        with open(output_path, 'w') as f:
            json.dump(combined_result, f, indent=2)
        print(f"Educational JSON saved to {output_path}")
    
    return combined_result

def main():
    parser = argparse.ArgumentParser(description='Convert educational PDF to structured JSON using DeepSeek model')
    parser.add_argument('pdf_path', help='Path to the PDF file')
    parser.add_argument('-o', '--output', help='Output JSON file path')
    parser.add_argument('-s', '--schema', help='Optional JSON schema to use')
    parser.add_argument('-t', '--topic', help='Override topic detection')
    parser.add_argument('-l', '--level', help='Override education level detection')
    
    args = parser.parse_args()
    
    output_path = args.output or f"{os.path.splitext(args.pdf_path)[0]}.json"
    
    result = pdf_to_educational_json(args.pdf_path, output_path, args.schema)
    if result:
        print("Successfully converted PDF to educational JSON")
        return 0
    else:
        print("Failed to convert PDF to educational JSON")
        return 1

if __name__ == "__main__":
    exit(main()) 