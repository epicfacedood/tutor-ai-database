#!/usr/bin/env python3
import os
import json
import argparse
import subprocess
import re
import traceback
from datetime import datetime
from streamlined_education_pdf_to_json import extract_text_from_pdf, extract_metadata, fix_json_string, extract_json_from_text, create_fallback_json

def process_pair_with_deepseek(question_text, solution_text, metadata):
    """Process a question-solution pair with DeepSeek model."""
    # Create the prompt
    prompt = f"""Convert the following educational question and solution pair into a structured JSON format suitable for a tutoring AI system.

METADATA:
- Subject: {metadata.get('subject', 'Mathematics')}
- Topic: {metadata.get('topic', 'Unknown')}
- Education Level: {metadata.get('education_level', 'JC / A Level')}

QUESTION CONTENT:
{question_text[:2000]}  # First 2000 chars of question

SOLUTION CONTENT:
{solution_text[:2000]}  # First 2000 chars of solution

INSTRUCTIONS:
1. Extract practice questions and their complete solutions
2. For each question:
   - Include the full question text
   - Provide the detailed solution steps
   - Identify the difficulty level (Easy, Medium, Hard)
   - Extract any hints or tips provided
   - Identify the key concepts being tested

3. Also extract any key concepts, definitions, or formulas that are explained in the materials

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
        "formulas": ["string"]
      }}
    ],
    "practice_questions": [
      {{
        "question_text": "string",
        "difficulty_level": "string",
        "concepts_tested": ["string"],
        "solution": {{
          "steps": ["string"],
          "final_answer": "string"
        }},
        "hints": ["string"]
      }}
    ]
  }}
}}

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
            combined_text = f"QUESTION:\n{question_text}\n\nSOLUTION:\n{solution_text}"
            fallback_json = create_fallback_json(combined_text, metadata)
            return fallback_json
            
    except subprocess.CalledProcessError as e:
        print(f"Error running DeepSeek model: {e}")
        print(f"Error output: {e.stderr}")
        # Create a fallback JSON
        combined_text = f"QUESTION:\n{question_text}\n\nSOLUTION:\n{solution_text}"
        return create_fallback_json(combined_text, metadata)
    except Exception as e:
        print(f"Unexpected error: {e}")
        print(traceback.format_exc())
        # Create a fallback JSON
        combined_text = f"QUESTION:\n{question_text}\n\nSOLUTION:\n{solution_text}"
        return create_fallback_json(combined_text, metadata)

def identify_question_solution_files(pair_dir):
    """Identify which files are questions and which are solutions in a pair directory."""
    files = [f for f in os.listdir(pair_dir) if f.lower().endswith('.pdf')]
    
    # Keywords that indicate a file is a solution
    solution_keywords = [
        'solution', 'solutions', 'soln', 'solns', 'sol', 'sols',
        'answer', 'answers', 'ans', 'anss',
        'worked', 'worked example', 'worked examples',
        'key', 'keys', 'answer key', 'answer keys'
    ]
    
    solution_files = []
    question_files = []
    
    for file in files:
        lower_file = file.lower()
        is_solution = any(keyword in lower_file for keyword in solution_keywords)
        
        if is_solution:
            solution_files.append(file)
        else:
            question_files.append(file)
    
    # If all files were identified as solutions or questions, use other heuristics
    if not question_files or not solution_files:
        # If we have exactly two files, assume the shorter filename is the question
        if len(files) == 2:
            if len(files[0]) <= len(files[1]):
                question_files = [files[0]]
                solution_files = [files[1]]
            else:
                question_files = [files[1]]
                solution_files = [files[0]]
        else:
            # If we have more than two files, just use the first file as question and the rest as solutions
            question_files = [files[0]] if files else []
            solution_files = files[1:] if len(files) > 1 else []
    
    return question_files, solution_files

def process_pair(pair_dir, output_path):
    """Process a question-solution pair directory."""
    # Identify question and solution files
    question_files, solution_files = identify_question_solution_files(pair_dir)
    
    if not question_files or not solution_files:
        print(f"Could not identify question and solution files in {pair_dir}")
        return False
    
    # Extract text from the first question file and all solution files
    question_file = os.path.join(pair_dir, question_files[0])
    question_text = extract_text_from_pdf(question_file) or ""
    
    solution_text = ""
    for solution_file in solution_files:
        solution_path = os.path.join(pair_dir, solution_file)
        solution_content = extract_text_from_pdf(solution_path) or ""
        solution_text += solution_content + "\n\n"
    
    # Extract metadata from the question file
    metadata = extract_metadata(question_file, question_text)
    
    # Update metadata with pair information
    metadata["pair_dir"] = pair_dir
    metadata["question_file"] = question_files[0]
    metadata["solution_files"] = solution_files
    
    # Process the pair
    result = process_pair_with_deepseek(question_text, solution_text, metadata)
    
    # Save to file
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"Pair JSON saved to {output_path}")
    return True

def process_all_pairs(pairs_dir, output_dir, max_pairs=None):
    """Process all question-solution pairs in the given directory."""
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get all pair directories
    pair_dirs = [d for d in os.listdir(pairs_dir) if os.path.isdir(os.path.join(pairs_dir, d))]
    
    # Limit to max_pairs if specified
    if max_pairs:
        pair_dirs = pair_dirs[:min(len(pair_dirs), max_pairs)]
    
    print(f"Processing {len(pair_dirs)} question-solution pairs...")
    
    # Process each pair
    successful = 0
    for i, pair_dir in enumerate(pair_dirs, 1):
        try:
            pair_path = os.path.join(pairs_dir, pair_dir)
            output_path = os.path.join(output_dir, f"{pair_dir}.json")
            
            print(f"\nPair {i}/{len(pair_dirs)}: {pair_dir}")
            
            if process_pair(pair_path, output_path):
                successful += 1
        except Exception as e:
            print(f"Error processing pair {pair_dir}: {e}")
            print(traceback.format_exc())
    
    print(f"\nProcessing complete! Successfully processed {successful}/{len(pair_dirs)} pairs.")
    return successful

def main():
    parser = argparse.ArgumentParser(description='Process question-solution pairs into JSON files.')
    parser.add_argument('pairs_dir', help='Directory containing question-solution pair directories')
    parser.add_argument('-o', '--output-dir', default='processed_pairs', help='Output directory for JSON files')
    parser.add_argument('-m', '--max-pairs', type=int, help='Maximum number of pairs to process')
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.pairs_dir):
        print(f"Error: {args.pairs_dir} is not a directory")
        return 1
    
    process_all_pairs(args.pairs_dir, args.output_dir, args.max_pairs)
    
    return 0

if __name__ == "__main__":
    exit(main()) 