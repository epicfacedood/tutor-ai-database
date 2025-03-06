#!/usr/bin/env python3
import os
import argparse
import glob
import concurrent.futures
import time
from enhanced_education_pdf_to_json import pdf_to_educational_json

def process_pdf(pdf_path, output_dir, schema=None, syllabus_path=None, generate_questions=False, analyze_relationships=False):
    """Process a single PDF file."""
    try:
        # Create output filename
        base_name = os.path.basename(pdf_path)
        output_name = os.path.splitext(base_name)[0] + "_enhanced.json"
        output_path = os.path.join(output_dir, output_name)
        
        print(f"Processing {base_name}...")
        result = pdf_to_educational_json(
            pdf_path, 
            output_path, 
            schema, 
            syllabus_path,
            generate_questions,
            analyze_relationships
        )
        
        if result:
            print(f"✓ Successfully converted {base_name} to {output_name}")
            return (pdf_path, True)
        else:
            print(f"✗ Failed to convert {base_name}")
            return (pdf_path, False)
    except Exception as e:
        print(f"✗ Error processing {pdf_path}: {e}")
        return (pdf_path, False)

def batch_convert(input_pattern, output_dir, schema=None, syllabus_path=None, generate_questions=False, analyze_relationships=False, max_workers=1):
    """Convert multiple PDFs to JSON format."""
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Find all PDF files matching the pattern
    pdf_files = glob.glob(input_pattern, recursive=True)
    
    if not pdf_files:
        print(f"No PDF files found matching pattern: {input_pattern}")
        return
    
    print(f"Found {len(pdf_files)} PDF files to process")
    
    # Process files in parallel
    start_time = time.time()
    results = []
    
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                process_pdf, 
                pdf, 
                output_dir, 
                schema, 
                syllabus_path, 
                generate_questions, 
                analyze_relationships
            ): pdf for pdf in pdf_files
        }
        
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
    
    # Summarize results
    successful = [path for path, success in results if success]
    failed = [path for path, success in results if not success]
    
    print("\n" + "="*50)
    print(f"Batch Processing Complete in {time.time() - start_time:.2f} seconds")
    print(f"Successfully converted: {len(successful)}/{len(pdf_files)}")
    
    if failed:
        print("\nFailed conversions:")
        for path in failed:
            print(f"  - {path}")
    
    print("="*50)

def main():
    parser = argparse.ArgumentParser(description='Batch convert educational PDFs to enhanced JSON format')
    parser.add_argument('input_pattern', help='Glob pattern for input PDF files (e.g., "data/*.pdf")')
    parser.add_argument('-o', '--output-dir', default='output_json', help='Output directory for JSON files')
    parser.add_argument('-s', '--schema', help='Optional JSON schema file path')
    parser.add_argument('-y', '--syllabus', help='Path to syllabus PDF for mapping')
    parser.add_argument('-q', '--generate-questions', action='store_true', help='Generate additional practice questions')
    parser.add_argument('-r', '--analyze-relationships', action='store_true', help='Analyze concept relationships')
    parser.add_argument('-w', '--workers', type=int, default=1, help='Number of parallel workers (default: 1)')
    
    args = parser.parse_args()
    
    # Load schema if provided
    schema_content = None
    if args.schema:
        try:
            with open(args.schema, 'r') as f:
                schema_content = f.read()
        except Exception as e:
            print(f"Error loading schema file: {e}")
            return 1
    
    batch_convert(
        args.input_pattern, 
        args.output_dir, 
        schema_content, 
        args.syllabus,
        args.generate_questions,
        args.analyze_relationships,
        args.workers
    )

if __name__ == "__main__":
    main() 