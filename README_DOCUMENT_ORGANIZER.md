# Document Organizer

This script organizes educational documents (PDFs) by categorizing them into:

- Question-solution pairs
- Standalone notes
- Standalone questions
- Standalone solutions
- Combined materials:
  - Notes with questions
  - Notes with solutions
  - Combined question-solution documents

## How It Works

1. **Pairing Question Papers and Solutions**:

   - The script first tries to match question papers with their corresponding solutions based on filename similarity.
   - It identifies question papers and solutions using keywords in filenames.
   - Solutions typically have keywords like "ans", "soln", "answer", "solution", etc.
   - Question papers typically have keywords like "question", "problem", "exercise", etc.

2. **Classification for Standalone Documents**:

   - For documents that don't have a clear pair, the script analyzes the filename.
   - It classifies each document based on keyword combinations in the filename.
   - Documents can be classified as standalone notes, questions, solutions, or combined materials.
   - The script also looks for common patterns like "bmq", "apq", "chapter", etc. to improve classification.

3. **Organization**:
   - Question-solution pairs are placed together in dedicated folders.
   - Standalone documents are organized into separate directories based on their classification.
   - Combined materials are organized into subdirectories based on their specific type.

## Requirements

- Python 3.6+
- PyPDF2

## Installation

Make sure you have the required package:

```
pip install PyPDF2
```

## Usage

```bash
python organize_documents.py
```

By default, the script will:

- Look for PDF files in the `dataprocessing/raw_data/notes` directory
- Output organized files to the `organized_data` directory

### Optional Arguments

- `--source`, `-s`: Source directory containing PDF files (default: dataprocessing/raw_data/notes)
- `--output`, `-o`: Output directory for organized files (default: organized_data)

Example with custom directories:

```bash
python organize_documents.py --source my_pdfs --output sorted_pdfs
```

## Output Structure

```
organized_data/
├── question_solution_pairs/
│   ├── pair_1/
│   │   ├── question.pdf
│   │   └── solution.pdf
│   └── pair_2/
│       ├── question.pdf
│       └── solution.pdf
├── notes/
│   └── note1.pdf
├── standalone_questions/
│   └── question1.pdf
├── standalone_solutions/
│   └── solution1.pdf
└── combined_materials/
    ├── notes_with_questions/
    │   └── note_with_questions.pdf
    ├── notes_with_solutions/
    │   └── note_with_solutions.pdf
    └── combined_question_solution/
        └── combined_document.pdf
```

## Example

1. Place your PDF files in the `dataprocessing/raw_data/notes` directory.
2. Run the script:
   ```
   python organize_documents.py
   ```
3. Check the organized files in the `organized_data` directory.
