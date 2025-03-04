# Educational Data Processing Pipeline

This pipeline processes educational materials (syllabus, notes, question papers, and solutions) to create a knowledge graph and vector embeddings for the SuperTutor AI application.

## Directory Structure

```
dataprocessing/
├── raw_data/           # Place your educational materials here
│   ├── syllabus/      # Syllabus documents
│   ├── notes/         # Course notes
│   ├── questions/     # Question papers
│   └── solutions/     # Solution documents
├── processed_data/    # Processed data will be saved here
│   ├── knowledge_graph.json
│   ├── text_chunks.json
│   └── faiss_index.bin
└── data_processor.py  # Main processing script
```

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Download the spaCy model:
```bash
python -m spacy download en_core_web_sm
```

3. Place your educational materials in the `raw_data` directory:
   - Supported formats: PDF, DOCX, TXT
   - Organize files in appropriate subdirectories (syllabus, notes, questions, solutions)

## Usage

Run the data processing pipeline:
```bash
python data_processor.py
```

The script will:
1. Load all documents from the raw_data directory
2. Preprocess and chunk the documents
3. Create a knowledge graph using entity extraction
4. Generate embeddings for text chunks
5. Save processed data to the processed_data directory

## Output

The processed data includes:
- `knowledge_graph.json`: A graph representation of the educational content
- `text_chunks.json`: Chunked text with metadata and embeddings
- `faiss_index.bin`: FAISS index for efficient similarity search

## Integration with SuperTutor AI

The processed data can be used with the SuperTutor AI application for:
- Semantic search across educational materials
- Knowledge graph-based question answering
- Context-aware tutoring responses
- Related concept suggestions 