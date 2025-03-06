#!/usr/bin/env python3
import os
import re
import shutil
import argparse
import subprocess
import json
from collections import defaultdict

def extract_text_from_pdf(pdf_path, max_pages=3):
    """Extract text from the first few pages of a PDF file."""
    try:
        import PyPDF2
        text = ""
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            # Only extract from the first few pages to save time
            for page_num in range(min(len(reader.pages), max_pages)):
                page = reader.pages[page_num]
                text += page.extract_text() + "\n\n"
        return text
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
        return ""

def classify_file_with_deepseek(pdf_path):
    """Use DeepSeek to classify a file as a question paper, solution, or individual note."""
    # Extract text from the first few pages
    text = extract_text_from_pdf(pdf_path)
    if not text:
        return "unknown", 0.0
    
    # Create the prompt
    prompt = f"""Analyze the following text extracted from a PDF file and determine if it's:
1. A question paper/worksheet (contains primarily questions or problems to solve)
2. A solution file (contains primarily answers or solutions to problems)
3. A standalone note (contains explanations, theory, or lecture notes without being primarily questions or solutions)

TEXT FROM PDF (first few pages):
{text[:2000]}

INSTRUCTIONS:
- Focus on the content structure and purpose of the document
- Look for keywords like "solution", "answer", "worked example" for solution files
- Look for question numbers, problem statements, or exercises for question papers
- Look for explanatory text, definitions, and theory for standalone notes

Return your analysis as a JSON object with the following structure:
{{
  "classification": "question_paper" or "solution" or "standalone_note",
  "confidence": a number between 0 and 1 indicating your confidence in this classification,
  "reasoning": "A brief explanation of why you classified it this way"
}}

Return ONLY the JSON without any additional text."""
    
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
        
        # Try to find JSON in the output
        json_start = output.find("{")
        json_end = output.rfind("}")
        if json_start != -1 and json_end != -1:
            json_text = output[json_start:json_end+1]
            try:
                result = json.loads(json_text)
                return result.get("classification", "unknown"), result.get("confidence", 0.0)
            except json.JSONDecodeError:
                pass
        
        # If we couldn't parse JSON, use simple heuristics
        if "solution" in output.lower() or "answer" in output.lower():
            return "solution", 0.5
        elif "question" in output.lower() or "problem" in output.lower():
            return "question_paper", 0.5
        else:
            return "standalone_note", 0.5
            
    except Exception as e:
        print(f"Error classifying {pdf_path}: {e}")
        return "unknown", 0.0

def find_similar_files(files, similarity_threshold=0.6):
    """Find similar files based on their names."""
    pairs = []
    processed = set()
    
    for i, file1 in enumerate(files):
        if file1 in processed:
            continue
        
        base1 = os.path.splitext(file1)[0].lower()
        similar_files = [file1]
        
        for file2 in files[i+1:]:
            if file2 in processed:
                continue
                
            base2 = os.path.splitext(file2)[0].lower()
            
            # Calculate similarity score
            words1 = set(re.findall(r'\w+', base1))
            words2 = set(re.findall(r'\w+', base2))
            
            if not words1 or not words2:
                continue
                
            common_words = words1.intersection(words2)
            similarity = len(common_words) / max(len(words1), len(words2))
            
            if similarity >= similarity_threshold:
                similar_files.append(file2)
                processed.add(file2)
        
        if len(similar_files) > 1:
            pairs.append(similar_files)
        
        processed.add(file1)
    
    return pairs

def organize_files_with_ai(source_dir, output_dir, max_files=None):
    """Organize files into pairs and individual notes using AI classification."""
    # Create output directories
    pairs_dir = os.path.join(output_dir, 'question_solution_pairs')
    notes_dir = os.path.join(output_dir, 'individual_notes')
    os.makedirs(pairs_dir, exist_ok=True)
    os.makedirs(notes_dir, exist_ok=True)
    
    # Get all PDF files
    pdf_files = [f for f in os.listdir(source_dir) if f.lower().endswith('.pdf')]
    
    # Limit the number of files if specified
    if max_files and len(pdf_files) > max_files:
        pdf_files = pdf_files[:max_files]
    
    print(f"Analyzing {len(pdf_files)} PDF files...")
    
    # Classify each file
    classifications = {}
    for i, file in enumerate(pdf_files, 1):
        print(f"Classifying file {i}/{len(pdf_files)}: {file}")
        file_path = os.path.join(source_dir, file)
        classification, confidence = classify_file_with_deepseek(file_path)
        classifications[file] = (classification, confidence)
        print(f"  → Classified as: {classification} (confidence: {confidence:.2f})")
    
    # Find similar files
    similar_groups = find_similar_files(pdf_files)
    
    # Organize files
    paired_files = set()
    pair_count = 0
    
    # First, process similar groups to find question-solution pairs
    for group in similar_groups:
        # Check if the group contains both questions and solutions
        has_question = any(classifications.get(f, ("unknown", 0.0))[0] == "question_paper" for f in group)
        has_solution = any(classifications.get(f, ("unknown", 0.0))[0] == "solution" for f in group)
        
        if has_question and has_solution:
            # This is a question-solution pair
            pair_count += 1
            pair_dir = os.path.join(pairs_dir, f"pair_{pair_count}")
            os.makedirs(pair_dir, exist_ok=True)
            
            for file in group:
                src_path = os.path.join(source_dir, file)
                dst_path = os.path.join(pair_dir, file)
                shutil.copy2(src_path, dst_path)
                paired_files.add(file)
                print(f"Copied {file} to {pair_dir}")
    
    # Process remaining files
    for file in pdf_files:
        if file in paired_files:
            continue
        
        classification, confidence = classifications.get(file, ("unknown", 0.0))
        
        if classification == "standalone_note" or classification == "unknown":
            # This is an individual note
            src_path = os.path.join(source_dir, file)
            dst_path = os.path.join(notes_dir, file)
            shutil.copy2(src_path, dst_path)
            print(f"Copied {file} to {notes_dir}")
        else:
            # This is a question or solution without a pair
            # We'll still treat it as an individual note
            src_path = os.path.join(source_dir, file)
            dst_path = os.path.join(notes_dir, file)
            shutil.copy2(src_path, dst_path)
            print(f"Copied {file} to {notes_dir} (unpaired {classification})")
    
    return pair_count, len(pdf_files) - len(paired_files)

def main():
    parser = argparse.ArgumentParser(description='Organize question papers and their solution files into pairs using AI.')
    parser.add_argument('source_dir', help='Source directory containing PDF files')
    parser.add_argument('-o', '--output-dir', default='ai_organized_files', help='Output directory for organized files')
    parser.add_argument('-m', '--max-files', type=int, help='Maximum number of files to process')
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.source_dir):
        print(f"Error: {args.source_dir} is not a directory")
        return 1
    
    print(f"Organizing files from {args.source_dir} using AI classification...")
    num_pairs, num_unpaired = organize_files_with_ai(args.source_dir, args.output_dir, args.max_files)
    
    print(f"\nOrganization complete!")
    print(f"Found {num_pairs} question-solution pairs")
    print(f"Found {num_unpaired} individual notes")
    print(f"\nPairs are in: {os.path.join(args.output_dir, 'question_solution_pairs')}")
    print(f"Individual notes are in: {os.path.join(args.output_dir, 'individual_notes')}")
    
    return 0

if __name__ == "__main__":
    exit(main()) 