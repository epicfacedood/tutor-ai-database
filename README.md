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

# Knowledge Graph Builder for Educational Content

This project builds a knowledge graph from educational content, specifically course syllabi. The knowledge graph represents relationships between courses, topics, subtopics, and other educational concepts.

## Project Structure

```
.
├── data/
│   ├── raw/             # Raw syllabus files (PDF, DOCX, TXT)
│   └── processed/       # Processed data and knowledge graph
├── dataprocessing/      # Data processing scripts
│   ├── syllabus_processor_nltk.py     # Process syllabi using NLTK
│   ├── build_knowledge_graph_nltk.py  # Build knowledge graph
│   ├── visualize_knowledge_graph.py   # Visualize knowledge graph
│   ├── upload_knowledge_graph_to_pinecone.py  # Upload graph to Pinecone
│   ├── knowledge_graph_rag.py         # RAG with knowledge graph
│   └── api.py                         # API for frontend integration
└── .env                 # Environment variables (API keys)
```

## Setup

1. Create a virtual environment:

   ```
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:

   ```
   python3 -m pip install langchain langchain-community langchain-anthropic langchain-openai nltk networkx matplotlib pypdf docx2txt python-dotenv pinecone-client fastapi uvicorn
   ```

3. Set up your API keys in the `.env` file:
   ```
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   PINECONE_API_KEY=your_pinecone_api_key_here
   PINECONE_ENVIRONMENT=your_pinecone_environment_here
   PINECONE_INDEX=your_pinecone_index_name_here
   ```

## Usage

1. Place your syllabus files (PDF, DOCX, or TXT) in the `data/raw/` directory.

2. Process the syllabi:

   ```
   cd dataprocessing
   python3 syllabus_processor_nltk.py
   ```

   This will generate a `syllabus_data.json` file in the `data/processed/` directory.

3. Build the knowledge graph:

   ```
   python3 build_knowledge_graph_nltk.py
   ```

   This will generate a `knowledge_graph.gml` file in the `data/processed/` directory.

4. Visualize the knowledge graph:
   ```
   python3 visualize_knowledge_graph.py
   ```
   This will generate a `knowledge_graph_visualization.png` file in the `data/processed/` directory.

## Integrating with a Frontend RAG Application

If you have a frontend application that uses RAG (Retrieval-Augmented Generation) with Pinecone, you can integrate the knowledge graph by following these steps:

1. Upload the knowledge graph to Pinecone:

   ```
   cd dataprocessing
   python3 upload_knowledge_graph_to_pinecone.py
   ```

   This will convert the knowledge graph nodes and relationships into vector embeddings and upload them to your Pinecone index.

2. Test the knowledge graph enhanced RAG:

   ```
   python3 knowledge_graph_rag.py
   ```

   This will demonstrate how the knowledge graph enhances RAG by providing additional context from related nodes.

3. Start the API server:

   ```
   python3 api.py
   ```

   This will start a FastAPI server on port 8000 that provides endpoints for your frontend to interact with the knowledge graph.

4. Connect your frontend to the API:

   The API provides the following endpoints:

   - `POST /ask` - Ask a question and get an answer using the knowledge graph enhanced RAG
   - `GET /graph/nodes` - Get all nodes in the knowledge graph
   - `GET /graph/edges` - Get all edges in the knowledge graph
   - `GET /graph/node/{node_id}` - Get details for a specific node
   - `GET /graph/search?query={query}` - Search for nodes in the graph based on a text query

   Example frontend code to ask a question:

   ```javascript
   async function askQuestion(question) {
     const response = await fetch("http://localhost:8000/ask", {
       method: "POST",
       headers: {
         "Content-Type": "application/json",
       },
       body: JSON.stringify({ question }),
     });
     return await response.json();
   }
   ```

## How It Works

1. **Syllabus Processing**: The `syllabus_processor_nltk.py` script reads syllabus files, extracts structured information such as course code, topics, subtopics, prerequisites, and difficulty levels, and saves this information in a JSON file.

2. **Knowledge Graph Building**: The `build_knowledge_graph_nltk.py` script reads the processed syllabus data, creates a knowledge graph using the NetworkX library, and saves it in GML format. The knowledge graph represents relationships between courses, topics, subtopics, and other educational concepts.

3. **Knowledge Graph Visualization**: The `visualize_knowledge_graph.py` script reads the knowledge graph and creates a visual representation using Matplotlib.

4. **Knowledge Graph to Pinecone**: The `upload_knowledge_graph_to_pinecone.py` script converts the knowledge graph nodes and relationships into vector embeddings and uploads them to Pinecone for use in RAG applications.

5. **Knowledge Graph Enhanced RAG**: The `knowledge_graph_rag.py` script demonstrates how to use the knowledge graph to enhance RAG by providing additional context from related nodes.

6. **API for Frontend Integration**: The `api.py` script provides a FastAPI server with endpoints for your frontend to interact with the knowledge graph.

## Example

The repository includes a sample syllabus file (`data/raw/sample_syllabus.txt`) that demonstrates the format expected by the processor. You can use this as a template for your own syllabus files.

## Requirements

- Python 3.9+
- NLTK
- NetworkX
- Matplotlib
- LangChain
- Anthropic API key (for Claude LLM)
- OpenAI API key (for embeddings)
- Pinecone API key (for vector database)
- FastAPI and Uvicorn (for API server)

## License

This project is licensed under the MIT License - see the LICENSE file for details.
