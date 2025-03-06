#!/usr/bin/env python3
import os
import re
import shutil
import argparse
import subprocess
import json
from collections import defaultdict

def is_solution_file(filename):
    """Check if a file is likely a solution file based on its name."""
    solution_keywords = [
        'solution', 'solutions', 'soln', 'solns', 'sol', 'sols',
        'answer', 'answers', 'ans', 'anss',
        'worked', 'worked example', 'worked examples',
        'key', 'keys', 'answer key', 'answer keys'
    ]
    
    # Convert to lowercase for case-insensitive matching
    lower_filename = filename.lower()
    
    # Check for solution keywords
    for keyword in solution_keywords:
        if keyword in lower_filename:
            return True
    
    return False

def is_question_file(filename):
    """Check if a file is likely a question paper based on its name."""
    question_keywords = [
        'question', 'questions', 'qn', 'qns', 
        'problem', 'problems', 'exercise', 'exercises',
        'worksheet', 'worksheets', 'assignment', 'assignments',
        'practice', 'test', 'exam', 'quiz'
    ]
    
    # Convert to lowercase for case-insensitive matching
    lower_filename = filename.lower()
    
    # Check for question keywords
    for keyword in question_keywords:
        if keyword in lower_filename:
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

def extract_text_from_pdf(pdf_path, max_pages=2):
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

def classify_standalone_file(pdf_path):
    """Classify a standalone file as a question paper, solution, or note."""
    # First check the filename
    filename = os.path.basename(pdf_path)
    if is_solution_file(filename):
        return "solution"
    if is_question_file(filename):
        return "question_paper"
    
    # If filename doesn't give a clear indication, check the content
    text = extract_text_from_pdf(pdf_path)
    if not text:
        return "unknown"
    
    # Check for solution indicators in the content
    solution_indicators = [
        'solution', 'solutions', 'answer', 'answers', 'solved', 'worked example',
        'ans:', 'sol:', 'soln:', 'answer:', 'solution:'
    ]
    
    # Check for question indicators in the content
    question_indicators = [
        'question', 'questions', 'problem', 'problems', 'exercise', 'exercises',
        'q1.', 'q2.', 'q1)', 'q2)', 'question 1', 'question 2'
    ]
    
    # Count occurrences of indicators
    solution_count = sum(text.lower().count(indicator) for indicator in solution_indicators)
    question_count = sum(text.lower().count(indicator) for indicator in question_indicators)
    
    # Classify based on indicator counts
    if solution_count > question_count * 1.5:  # Solutions have more solution indicators
        return "solution"
    elif question_count > solution_count:  # Questions have more question indicators
        return "question_paper"
    else:
        # If neither dominates, it's likely a note
        return "standalone_note"

def find_pairs_and_classify(source_dir, similarity_threshold=0.8):
    """Find pairs based on filename similarity and classify standalone files."""
    # Get all PDF files
    pdf_files = [f for f in os.listdir(source_dir) if f.lower().endswith('.pdf')]
    
    # First, identify solution files and question files
    solution_files = [f for f in pdf_files if is_solution_file(f)]
    question_files = [f for f in pdf_files if is_question_file(f)]
    
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
            
            similarity = calculate_filename_similarity(sol_file, q_file)
            if similarity > similarity_threshold and similarity > best_score:
                best_match = q_file
                best_score = similarity
        
        if best_match:
            # Found a pair
            pairs.append([sol_file, best_match])
            paired_files.add(sol_file)
            paired_files.add(best_match)
    
    # Look for similar files among the remaining files
    remaining_files = [f for f in pdf_files if f not in paired_files]
    
    for i, file1 in enumerate(remaining_files):
        if file1 in paired_files:
            continue
        
        for file2 in remaining_files[i+1:]:
            if file2 in paired_files:
                continue
            
            similarity = calculate_filename_similarity(file1, file2)
            if similarity > similarity_threshold:
                # Check if one is likely a solution and the other a question
                file1_is_sol = is_solution_file(file1)
                file2_is_sol = is_solution_file(file2)
                file1_is_q = is_question_file(file1)
                file2_is_q = is_question_file(file2)
                
                if (file1_is_sol and file2_is_q) or (file1_is_q and file2_is_sol):
                    pairs.append([file1, file2])
                    paired_files.add(file1)
                    paired_files.add(file2)
    
    # Classify standalone files
    standalone_files = [f for f in pdf_files if f not in paired_files]
    classifications = {}
    
    for file in standalone_files:
        file_path = os.path.join(source_dir, file)
        classification = classify_standalone_file(file_path)
        classifications[file] = classification
    
    return pairs, classifications

def organize_files(source_dir, output_dir):
    """Organize files into pairs and individual notes."""
    # Create output directories
    pairs_dir = os.path.join(output_dir, 'question_solution_pairs')
    notes_dir = os.path.join(output_dir, 'individual_notes')
    questions_dir = os.path.join(output_dir, 'standalone_questions')
    solutions_dir = os.path.join(output_dir, 'standalone_solutions')
    
    os.makedirs(pairs_dir, exist_ok=True)
    os.makedirs(notes_dir, exist_ok=True)
    os.makedirs(questions_dir, exist_ok=True)
    os.makedirs(solutions_dir, exist_ok=True)
    
    # Find pairs and classify standalone files
    print("Finding pairs and classifying standalone files...")
    pairs, classifications = find_pairs_and_classify(source_dir)
    
    # Organize paired files
    print(f"Found {len(pairs)} question-solution pairs")
    for i, group in enumerate(pairs, 1):
        # Create a directory for the pair
        pair_name = re.sub(r'[^\w\s-]', '', os.path.splitext(group[0])[0])
        pair_name = re.sub(r'\s+', '_', pair_name)
        pair_dir = os.path.join(pairs_dir, f"{pair_name}_{i}")
        os.makedirs(pair_dir, exist_ok=True)
        
        # Copy files to the pair directory
        for file in group:
            src_path = os.path.join(source_dir, file)
            dst_path = os.path.join(pair_dir, file)
            shutil.copy2(src_path, dst_path)
            print(f"Copied {file} to {pair_dir}")
    
    # Organize standalone files
    standalone_count = {
        "standalone_note": 0,
        "question_paper": 0,
        "solution": 0,
        "unknown": 0
    }
    
    for file, classification in classifications.items():
        src_path = os.path.join(source_dir, file)
        
        if classification == "standalone_note":
            dst_path = os.path.join(notes_dir, file)
            standalone_count["standalone_note"] += 1
        elif classification == "question_paper":
            dst_path = os.path.join(questions_dir, file)
            standalone_count["question_paper"] += 1
        elif classification == "solution":
            dst_path = os.path.join(solutions_dir, file)
            standalone_count["solution"] += 1
        else:
            dst_path = os.path.join(notes_dir, file)
            standalone_count["unknown"] += 1
        
        shutil.copy2(src_path, dst_path)
        print(f"Copied {file} to {os.path.dirname(dst_path)}")
    
    print(f"\nOrganization complete!")
    print(f"Found {len(pairs)} question-solution pairs")
    print(f"Found {standalone_count['standalone_note']} standalone notes")
    print(f"Found {standalone_count['question_paper']} standalone question papers")
    print(f"Found {standalone_count['solution']} standalone solution files")
    print(f"Found {standalone_count['unknown']} unclassified files")
    
    return len(pairs), sum(standalone_count.values())

def main():
    parser = argparse.ArgumentParser(description='Quickly organize question papers and their solution files into pairs.')
    parser.add_argument('source_dir', help='Source directory containing PDF files')
    parser.add_argument('-o', '--output-dir', default='quick_organized_files', help='Output directory for organized files')
    parser.add_argument('-t', '--threshold', type=float, default=0.8, help='Similarity threshold for pairing files (0.0-1.0)')
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.source_dir):
        print(f"Error: {args.source_dir} is not a directory")
        return 1
    
    print(f"Organizing files from {args.source_dir}...")
    organize_files(args.source_dir, args.output_dir)
    
    return 0

if __name__ == "__main__":
    exit(main()) 