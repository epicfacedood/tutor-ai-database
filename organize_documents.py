#!/usr/bin/env python3
import os
import re
import shutil
import argparse
import json
from collections import defaultdict
import PyPDF2

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

def is_note_file(filename):
    """Check if a file is likely a note based on its name."""
    note_keywords = [
        'note', 'notes', 'lecture', 'lectures', 'summary', 'summaries',
        'chapter', 'chapters', 'topic', 'topics', 'theory', 'concept',
        'learning package', 'guide', 'handbook', 'manual', 'reference',
        'cheat sheet', 'formula', 'definition', 'explanation'
    ]
    
    # Convert to lowercase for case-insensitive matching
    lower_filename = filename.lower()
    
    # Check for note keywords
    for keyword in note_keywords:
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

def extract_text_from_pdf(pdf_path, max_pages=2):
    """Extract text from the first few pages of a PDF file."""
    try:
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

def classify_document(filename):
    """Classify a document based on its filename into more specific categories."""
    is_solution = is_solution_file(filename)
    is_question = is_question_file(filename)
    is_note = is_note_file(filename)
    
    # Determine the document type based on keyword combinations
    if is_solution and is_question:
        return "combined_question_solution"
    elif is_solution and is_note:
        return "notes_with_solutions"
    elif is_question and is_note:
        return "notes_with_questions"
    elif is_solution:
        return "solution"
    elif is_question:
        return "question_paper"
    elif is_note:
        return "standalone_note"
    else:
        # If no clear classification, check for common patterns in filenames
        lower_filename = filename.lower()
        
        # Check for common naming patterns
        if re.search(r'(bmq|apq).*sol', lower_filename):
            return "solution"
        elif re.search(r'(bmq|apq)(?!.*sol)', lower_filename):
            return "question_paper"
        elif re.search(r'(ch|chapter|topic).*\d', lower_filename):
            return "standalone_note"
        elif re.search(r'(tutor|teacher|lecturer)', lower_filename):
            return "notes_with_solutions"
        
        # Default to unknown
        return "unknown"

def find_pairs_and_classify(source_dir, similarity_threshold=0.7):
    """Find pairs based on filename similarity and classify standalone files."""
    # Get all PDF files
    pdf_files = [f for f in os.listdir(source_dir) if f.lower().endswith('.pdf')]
    
    # First, identify solution files and question files
    solution_files = [f for f in pdf_files if is_solution_file(f) and not is_question_file(f)]
    question_files = [f for f in pdf_files if is_question_file(f) and not is_solution_file(f)]
    
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
                file1_is_sol = is_solution_file(file1) and not is_question_file(file1)
                file2_is_sol = is_solution_file(file2) and not is_question_file(file2)
                file1_is_q = is_question_file(file1) and not is_solution_file(file1)
                file2_is_q = is_question_file(file2) and not is_solution_file(file2)
                
                if (file1_is_sol and file2_is_q) or (file1_is_q and file2_is_sol):
                    pairs.append([file1, file2])
                    paired_files.add(file1)
                    paired_files.add(file2)
    
    # Classify standalone files
    standalone_files = [f for f in pdf_files if f not in paired_files]
    classifications = {}
    
    print(f"Classifying {len(standalone_files)} standalone files...")
    for i, file in enumerate(standalone_files):
        print(f"Classifying {i+1}/{len(standalone_files)}: {file}")
        classification = classify_document(file)
        classifications[file] = classification
    
    return pairs, classifications

def organize_files(source_dir, output_dir):
    """Organize files into pairs and individual categories."""
    # Create output directories
    pairs_dir = os.path.join(output_dir, 'question_solution_pairs')
    notes_dir = os.path.join(output_dir, 'notes')
    questions_dir = os.path.join(output_dir, 'standalone_questions')
    solutions_dir = os.path.join(output_dir, 'standalone_solutions')
    combined_dir = os.path.join(output_dir, 'combined_materials')
    notes_with_questions_dir = os.path.join(combined_dir, 'notes_with_questions')
    notes_with_solutions_dir = os.path.join(combined_dir, 'notes_with_solutions')
    combined_question_solution_dir = os.path.join(combined_dir, 'combined_question_solution')
    
    os.makedirs(pairs_dir, exist_ok=True)
    os.makedirs(notes_dir, exist_ok=True)
    os.makedirs(questions_dir, exist_ok=True)
    os.makedirs(solutions_dir, exist_ok=True)
    os.makedirs(notes_with_questions_dir, exist_ok=True)
    os.makedirs(notes_with_solutions_dir, exist_ok=True)
    os.makedirs(combined_question_solution_dir, exist_ok=True)
    
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
        "notes_with_questions": 0,
        "notes_with_solutions": 0,
        "combined_question_solution": 0,
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
        elif classification == "notes_with_questions":
            dst_path = os.path.join(notes_with_questions_dir, file)
            standalone_count["notes_with_questions"] += 1
        elif classification == "notes_with_solutions":
            dst_path = os.path.join(notes_with_solutions_dir, file)
            standalone_count["notes_with_solutions"] += 1
        elif classification == "combined_question_solution":
            dst_path = os.path.join(combined_question_solution_dir, file)
            standalone_count["combined_question_solution"] += 1
        else:
            # If classification is unknown, put in notes
            dst_path = os.path.join(notes_dir, file)
            standalone_count["unknown"] += 1
        
        shutil.copy2(src_path, dst_path)
        print(f"Copied {file} to {os.path.dirname(dst_path)}")
    
    # Print summary
    print("\nOrganization Summary:")
    print(f"Question-Solution Pairs: {len(pairs)}")
    print(f"Standalone Notes: {standalone_count['standalone_note']}")
    print(f"Standalone Questions: {standalone_count['question_paper']}")
    print(f"Standalone Solutions: {standalone_count['solution']}")
    print(f"Notes with Questions: {standalone_count['notes_with_questions']}")
    print(f"Notes with Solutions: {standalone_count['notes_with_solutions']}")
    print(f"Combined Question-Solution: {standalone_count['combined_question_solution']}")
    if standalone_count["unknown"] > 0:
        print(f"Unknown (classified as notes): {standalone_count['unknown']}")

def main():
    parser = argparse.ArgumentParser(description='Organize educational documents into categories.')
    parser.add_argument('--source', '-s', default='dataprocessing/raw_data/notes', help='Source directory containing PDF files (default: dataprocessing/raw_data/notes)')
    parser.add_argument('--output', '-o', default='organized_data', help='Output directory for organized files (default: organized_data)')
    
    args = parser.parse_args()
    
    # Create the source directory structure if it doesn't exist
    if not os.path.exists(args.source):
        os.makedirs(args.source, exist_ok=True)
        print(f"Created source directory: {args.source}")
    
    # Create the output directory if it doesn't exist
    if not os.path.exists(args.output):
        os.makedirs(args.output, exist_ok=True)
        print(f"Created output directory: {args.output}")
    
    # Organize the files
    organize_files(args.source, args.output)

if __name__ == "__main__":
    main() 