# SuperTutor AI Content Processor

This tool processes educational content (notes and past papers) for the SuperTutor AI system, extracting rich metadata and preparing it for vector storage.

## Features

- Processes PDF and DOCX files
- Extracts rich metadata using Claude AI
- Generates embeddings using OpenAI
- Handles mathematical content and formulas
- Provides detailed processing statistics
- Implements retry logic for API calls
- Supports both notes and past papers

## Setup

1. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables in `.env`:
```
OPENAI_API_KEY=your_openai_api_key
VITE_CLAUDE_API_KEY=your_claude_api_key
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENVIRONMENT=your_pinecone_environment
```

## Directory Structure

```
dataprocessing/
├── raw_data/
│   ├── notes/          # Place your notes here
│   └── past_papers/    # Place past papers here
├── processed_data/     # Processed content will be saved here
├── content_processor.py
├── pinecone_manager.py
└── process_and_upload.py
```

## Usage

1. Place your content files in the appropriate directories:
   - Notes in `raw_data/notes/`
   - Past papers in `raw_data/past_papers/`

2. Run the processor:
```bash
python process_and_upload.py
```

3. Check the results:
   - Processed content: `processed_data/content_chunks.json`
   - Processing statistics: `processed_data/processing_stats.json`

## Processing Statistics

The processor tracks:
- Total documents processed
- Successfully processed documents
- Failed documents
- Total chunks generated
- API errors encountered
- Processing time

## Error Handling

- Automatic retries for API calls
- Detailed error logging
- Fallback to rule-based extraction if AI fails
- Progress tracking and statistics

## Notes

- Supported file formats: PDF, DOCX
- Maximum content length per API call: 4000 characters
- Chunk size: 1000 characters with 200 character overlap
- Processing time varies based on content size and API response times 