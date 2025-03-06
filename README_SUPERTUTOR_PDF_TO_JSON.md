# SuperTutor AI: Enhanced PDF-to-JSON Conversion System

This system converts educational PDF materials into richly structured JSON format with detailed metadata for use in the SuperTutor AI application's RAG (Retrieval Augmented Generation) system.

## Features

- **Rich, Education-Specific JSON Schema**: Captures detailed metadata, structured content, pedagogical information, and relationship data
- **Enhanced Extraction**: Uses DeepSeek-R1-Distill-Qwen-7B model with specialized prompts for educational content
- **Syllabus Mapping**: Maps content to specific curriculum requirements
- **Automatic Question Generation**: Creates additional practice questions with varied difficulty levels
- **Concept Relationship Analysis**: Builds knowledge graphs showing how concepts relate to each other
- **Batch Processing**: Supports processing multiple PDFs in parallel

## System Components

1. **`enhanced_education_pdf_to_json.py`**: Main script for converting PDFs to enhanced JSON
2. **`enhanced_prompts.py`**: Specialized prompts for educational content extraction
3. **`education_schema.json`**: Rich, education-specific JSON schema
4. **`batch_convert_pdfs.py`**: Script for batch processing multiple PDFs
5. **`ENHANCED_DATA_EXTRACTION_SUMMARY.md`**: Detailed explanation of the enhancements

## Prerequisites

- Python 3.6+
- PyPDF2 library (`pip install PyPDF2`)
- Ollama installed with the DeepSeek-R1-Distill-Qwen-7B model
  - Install Ollama from [ollama.ai](https://ollama.ai)
  - Pull the model: `ollama pull deepseek-r1:7b`

## Installation

1. Clone this repository or download the scripts
2. Install required dependencies:
   ```
   pip install PyPDF2
   ```
3. Make the scripts executable:
   ```
   chmod +x enhanced_education_pdf_to_json.py batch_convert_pdfs.py
   ```

## Usage

### Basic Usage

```bash
./enhanced_education_pdf_to_json.py path/to/your/document.pdf
```

This will:

1. Extract text from the PDF
2. Detect metadata (subject, topic, education level)
3. Process the content with the DeepSeek model using enhanced prompts
4. Save the structured JSON to a file with the same name as the PDF but with `_enhanced.json` extension

### Advanced Usage

```bash
./enhanced_education_pdf_to_json.py path/to/your/document.pdf -o output.json -s education_schema.json -y path/to/syllabus.pdf -q -r
```

Parameters:

- `-o, --output`: Specify output file path
- `-s, --schema`: Provide JSON schema file
- `-y, --syllabus`: Provide syllabus PDF for mapping
- `-q, --generate-questions`: Generate additional practice questions
- `-r, --analyze-relationships`: Analyze concept relationships
- `-t, --topic`: Override topic detection
- `-l, --level`: Override education level detection

### Batch Processing

```bash
./batch_convert_pdfs.py "dataprocessing/raw_data/notes/*.pdf" -o output_json -w 4
```

Parameters:

- First argument: Glob pattern for input PDF files
- `-o, --output-dir`: Output directory for JSON files (default: `output_json`)
- `-s, --schema`: Optional JSON schema file to use
- `-w, --workers`: Number of parallel workers (default: 1)

## Output Format

The output JSON follows the structure defined in `education_schema.json`, which includes:

### Metadata Section

```json
"metadata": {
  "subject": "Mathematics",
  "topic": "Functions",
  "subtopic": "Inverse Functions",
  "education_level": "JC / A Level",
  "syllabus_reference": "H2 Mathematics (9758), Section 1.1",
  "syllabus_code": "9758",
  "exam_board": "Cambridge",
  "difficulty_level": "Medium",
  "prerequisites": ["Domain and Range", "Basic Algebra"],
  "learning_objectives": ["Understand one-to-one functions", "Find inverse functions"]
}
```

### Content Section

```json
"content": {
  "summary": "This chapter covers the basics of functions and inverse functions...",
  "key_concepts": [
    {
      "concept_name": "One-to-One Function",
      "definition": "A function where each element in the range corresponds to exactly one element in the domain",
      "explanation": "For a one-to-one function, if f(a) = f(b), then a = b",
      "formulas": [
        {
          "formula": "If f(a) = f(b), then a = b",
          "variables": {
            "a": "First input value",
            "b": "Second input value",
            "f(a)": "Output of function f at a",
            "f(b)": "Output of function f at b"
          }
        }
      ],
      "examples": [
        {
          "problem_statement": "Determine if f(x) = 2x + 3 is one-to-one",
          "solution_steps": [
            "Assume f(a) = f(b)",
            "Then 2a + 3 = 2b + 3",
            "Simplify: 2a = 2b",
            "Divide both sides by 2: a = b"
          ],
          "final_answer": "Since f(a) = f(b) implies a = b, the function is one-to-one"
        }
      ]
    }
  ],
  "practice_questions": [
    {
      "question_text": "Find the inverse of f(x) = 3x - 5",
      "difficulty_level": "Easy",
      "solution": {
        "steps": [
          "Let y = 3x - 5",
          "Solve for x: y + 5 = 3x",
          "Divide both sides by 3: (y + 5)/3 = x",
          "Therefore, f^(-1)(x) = (x + 5)/3"
        ],
        "final_answer": "f^(-1)(x) = (x + 5)/3"
      },
      "hints": ["Replace f(x) with y", "Solve for x in terms of y", "Replace y with x in the final expression"]
    }
  ]
}
```

### Relationships Section

```json
"relationships": {
  "prerequisites": ["Domain and Range", "Basic Algebra"],
  "related_topics": ["Composite Functions", "Function Transformations"],
  "follows_from": ["Relations"],
  "leads_to": ["Calculus"]
}
```

## Benefits for RAG System

This enhanced system provides several key benefits for your SuperTutor AI RAG system:

1. **More Accurate Retrieval**: The rich, structured data enables more precise retrieval of relevant information.
2. **Contextual Understanding**: The relationship data helps the AI understand how concepts relate to each other.
3. **Curriculum Alignment**: The syllabus mapping ensures that responses align with curriculum requirements.
4. **Pedagogical Value**: The enhanced data includes information about common misconceptions, learning sequences, and other pedagogically valuable content.
5. **Practice Opportunities**: The generated questions provide additional practice material for students.

## Troubleshooting

- **JSON Parsing Errors**: If the model output cannot be parsed as JSON, the system will attempt to extract JSON-like content and fix common issues. If that fails, it will save the raw output with metadata.
- **Long Processing Time**: The enhanced system makes multiple calls to the DeepSeek model, which can take time. For batch processing, adjust the number of workers based on your system's capabilities.
- **Memory Issues**: If you encounter memory issues with large PDFs, try reducing the chunk size in the `chunk_text` function.
- **Model Errors**: Ensure Ollama is running and the DeepSeek model is properly installed.

## Next Steps

To further enhance your SuperTutor AI RAG system, consider:

1. **Vector Embedding**: Create embeddings for different components of the JSON (concepts, questions, examples) to enable more granular retrieval.
2. **Multi-Modal Enhancement**: Extend the system to handle images, diagrams, and other non-text content.
3. **User Feedback Integration**: Implement a system to collect and incorporate user feedback to improve the quality of the extracted data.
4. **Custom Fine-Tuning**: Fine-tune the DeepSeek model specifically for educational content extraction to improve accuracy.

## License

This tool is provided for educational and research purposes.

## Acknowledgments

- DeepSeek AI for the powerful language model
- Ollama for the local model hosting solution
- PyPDF2 for PDF text extraction capabilities
