#!/usr/bin/env python3
import os
import re
import shutil
import argparse
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

def extract_base_name(filename):
    """Extract a base name from a filename to match questions with solutions."""
    # Remove extension
    base = os.path.splitext(filename)[0]
    
    # Remove common solution indicators
    base = re.sub(r'(?i)(_|\s|-|^)(solution|solutions|soln|solns|sol|sols|answer|answers|ans|anss|worked|key|keys)s?(?:_|\s|-|$)', '', base)
    
    # Remove year indicators (e.g., 2021, 2022)
    base = re.sub(r'(?:_|\s|-|^)20\d\d(?:_|\s|-|$)', '', base)
    
    # Remove common prefixes like "Chapter", "Topic", etc.
    base = re.sub(r'(?i)(?:_|\s|-|^)(chapter|chp|ch|topic|section|sec|part|tutorial|tut)(?:\s*\d+)?(?:_|\s|-|$)', '', base)
    
    # Remove common suffixes
    base = re.sub(r'(?i)(?:_|\s|-)(revision|rev|practice|prac|exercise|ex|worksheet|sheet)s?(?:_|\s|-|$)', '', base)
    
    # Remove special characters and extra spaces
    base = re.sub(r'[^\w\s]', ' ', base)
    base = re.sub(r'\s+', ' ', base).strip()
    
    return base

def find_question_solution_pairs(directory):
    """Find question-solution pairs in the given directory."""
    # Get all PDF files
    pdf_files = [f for f in os.listdir(directory) if f.lower().endswith('.pdf')]
    
    # Separate into solution files and question files
    solution_files = [f for f in pdf_files if is_solution_file(f)]
    question_files = [f for f in pdf_files if f not in solution_files]
    
    # Extract base names for matching
    solution_bases = {extract_base_name(f): f for f in solution_files}
    
    # Group files by their base names
    pairs = defaultdict(list)
    unpaired = []
    
    # Process question files first
    for q_file in question_files:
        base_name = extract_base_name(q_file)
        pairs[base_name].append(q_file)
    
    # Then match solution files
    for base_name, s_file in solution_bases.items():
        if base_name in pairs:
            pairs[base_name].append(s_file)
        else:
            # Try to find a close match
            best_match = None
            best_score = 0
            for q_base in pairs.keys():
                # Simple similarity score: count of common words
                q_words = set(q_base.lower().split())
                s_words = set(base_name.lower().split())
                common_words = q_words.intersection(s_words)
                score = len(common_words) / max(len(q_words), len(s_words)) if max(len(q_words), len(s_words)) > 0 else 0
                
                if score > 0.5 and score > best_score:  # Threshold for matching
                    best_match = q_base
                    best_score = score
            
            if best_match:
                pairs[best_match].append(s_file)
            else:
                # If no match found, create a new entry
                pairs[base_name].append(s_file)
    
    # Identify unpaired files
    for base_name, files in pairs.items():
        if len(files) == 1:
            unpaired.append(files[0])
    
    # Remove unpaired files from pairs
    pairs = {base: files for base, files in pairs.items() if len(files) > 1}
    
    return pairs, unpaired

def organize_files(source_dir, output_dir):
    """Organize files into pairs and individual notes."""
    # Create output directories
    pairs_dir = os.path.join(output_dir, 'question_solution_pairs')
    notes_dir = os.path.join(output_dir, 'individual_notes')
    os.makedirs(pairs_dir, exist_ok=True)
    os.makedirs(notes_dir, exist_ok=True)
    
    # Find pairs and unpaired files
    pairs, unpaired = find_question_solution_pairs(source_dir)
    
    # Organize paired files
    for base_name, files in pairs.items():
        # Create a directory for each pair
        pair_dir = os.path.join(pairs_dir, base_name.replace(' ', '_'))
        os.makedirs(pair_dir, exist_ok=True)
        
        # Copy files to the pair directory
        for file in files:
            src_path = os.path.join(source_dir, file)
            dst_path = os.path.join(pair_dir, file)
            shutil.copy2(src_path, dst_path)
            print(f"Copied {file} to {pair_dir}")
    
    # Organize unpaired files (individual notes)
    for file in unpaired:
        src_path = os.path.join(source_dir, file)
        dst_path = os.path.join(notes_dir, file)
        shutil.copy2(src_path, dst_path)
        print(f"Copied {file} to {notes_dir}")
    
    return len(pairs), len(unpaired)

def main():
    parser = argparse.ArgumentParser(description='Organize question papers and their solution files into pairs.')
    parser.add_argument('source_dir', help='Source directory containing PDF files')
    parser.add_argument('-o', '--output-dir', default='organized_files', help='Output directory for organized files')
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.source_dir):
        print(f"Error: {args.source_dir} is not a directory")
        return 1
    
    print(f"Organizing files from {args.source_dir}...")
    num_pairs, num_unpaired = organize_files(args.source_dir, args.output_dir)
    
    print(f"\nOrganization complete!")
    print(f"Found {num_pairs} question-solution pairs")
    print(f"Found {num_unpaired} individual notes")
    print(f"\nPairs are in: {os.path.join(args.output_dir, 'question_solution_pairs')}")
    print(f"Individual notes are in: {os.path.join(args.output_dir, 'individual_notes')}")
    
    return 0

if __name__ == "__main__":
    exit(main()) 