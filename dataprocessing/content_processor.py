import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import json
import logging
from datetime import datetime
from pathlib import Path
import re
from tenacity import retry, stop_after_attempt, wait_exponential
import numpy as np

from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import spacy
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ContentChunk:
    id: str
    values: List[float]
    metadata: Dict[str, Any]

    def to_dict(self):
        """Convert the chunk to a dictionary with numpy arrays converted to lists."""
        return {
            "id": self.id,
            "values": self.values.tolist() if isinstance(self.values, np.ndarray) else self.values,
            "metadata": self.metadata
        }

class ContentProcessor:
    def __init__(self, raw_data_dir: str, processed_data_dir: str):
        """Initialize the content processor."""
        self.raw_data_dir = Path(raw_data_dir)
        self.processed_data_dir = Path(processed_data_dir)
        self.processed_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize sentence transformer for embeddings
        logger.info("Loading sentence transformer model...")
        self.embeddings = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("Sentence transformer model loaded successfully")
        
        # Load spaCy model
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.info("Downloading spaCy model...")
            os.system("python -m spacy download en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Initialize processing statistics
        self.stats = {
            "total_documents": 0,
            "processed_documents": 0,
            "total_chunks": 0,
            "processing_errors": 0,
            "start_time": datetime.now().isoformat(),
            "end_time": None
        }

    def load_document(self, file_path: Path) -> Optional[str]:
        """Load document content based on file type."""
        try:
            if file_path.suffix.lower() == '.pdf':
                loader = PyPDFLoader(str(file_path))
            elif file_path.suffix.lower() in ['.docx', '.doc']:
                loader = Docx2txtLoader(str(file_path))
            else:
                logger.warning(f"Unsupported file type: {file_path.suffix}")
                return None
            
            documents = loader.load()
            return "\n".join(doc.page_content for doc in documents)
        except Exception as e:
            logger.error(f"Error loading document {file_path}: {str(e)}")
            self.stats["processing_errors"] += 1
            return None

    def extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from filename and content."""
        try:
            # Extract metadata from filename
            filename = file_path.stem
            metadata = {
                "file_path": str(file_path),
                "processed_date": datetime.now().isoformat(),
                "file_type": file_path.suffix.lower(),
                "school": None,
                "year": None,
                "type": None,
                "content_type": None,
                "topics": [],
                "difficulty": None
            }
            
            # Try to extract school name
            school_patterns = [
                r'(SAJC|SRJC|TJC|TMJC|TPJC|VJC|YIJC|YJC|RI)',
                r'([A-Z]{2,4}JC)'
            ]
            for pattern in school_patterns:
                match = re.search(pattern, filename)
                if match:
                    metadata["school"] = match.group(1)
                    break
            
            # Try to extract year
            year_match = re.search(r'20\d{2}', filename)
            if year_match:
                metadata["year"] = year_match.group(0)
            
            # Try to determine content type
            if "notes" in filename.lower():
                metadata["type"] = "notes"
            elif "paper" in filename.lower() or "prelim" in filename.lower():
                metadata["type"] = "past paper"
            
            # Try to determine specific content type
            if "solution" in filename.lower() or "ans" in filename.lower():
                metadata["content_type"] = "solution"
            elif "question" in filename.lower() or "qn" in filename.lower():
                metadata["content_type"] = "question"
            elif "revision" in filename.lower():
                metadata["content_type"] = "revision"
            
            # Try to extract topics from filename
            topic_keywords = [
                "trigonometry", "calculus", "vectors", "complex", "probability",
                "statistics", "functions", "sequences", "series", "matrices"
            ]
            for keyword in topic_keywords:
                if keyword in filename.lower():
                    metadata["topics"].append(keyword)
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {str(e)}")
            self.stats["processing_errors"] += 1
            raise

    def process_document(self, file_path: Path) -> List[ContentChunk]:
        """Process a single document into chunks."""
        try:
            # Load document
            content = self.load_document(file_path)
            if not content:
                return []
            
            # Extract metadata
            metadata = self.extract_metadata(file_path)
            
            # Split content into chunks
            chunks = self.text_splitter.split_text(content)
            
            # Process each chunk
            processed_chunks = []
            for i, chunk in enumerate(chunks):
                # Generate embedding using sentence transformer
                embedding = self.embeddings.encode(chunk, convert_to_list=True)
                
                # Create chunk metadata
                chunk_metadata = metadata.copy()
                chunk_metadata.update({
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "content": chunk
                })
                
                # Create chunk ID
                chunk_id = f"{file_path.stem}_chunk_{i}"
                
                # Create ContentChunk
                processed_chunks.append(ContentChunk(
                    id=chunk_id,
                    values=embedding,
                    metadata=chunk_metadata
                ))
            
            self.stats["total_chunks"] += len(processed_chunks)
            return processed_chunks
            
        except Exception as e:
            logger.error(f"Error processing document {file_path}: {str(e)}")
            self.stats["processing_errors"] += 1
            return []

    def process_all_content(self):
        """Process all content files in the raw data directory."""
        try:
            all_chunks = []
            
            # Process notes
            notes_dir = self.raw_data_dir / "notes"
            if notes_dir.exists():
                for file_path in tqdm(list(notes_dir.glob("**/*.pdf")), desc="Processing notes"):
                    self.stats["total_documents"] += 1
                    chunks = self.process_document(file_path)
                    if chunks:
                        self.stats["processed_documents"] += 1
                        all_chunks.extend(chunks)
            
            # Process past papers
            papers_dir = self.raw_data_dir / "past_papers"
            if papers_dir.exists():
                for file_path in tqdm(list(papers_dir.glob("**/*.pdf")), desc="Processing past papers"):
                    self.stats["total_documents"] += 1
                    chunks = self.process_document(file_path)
                    if chunks:
                        self.stats["processed_documents"] += 1
                        all_chunks.extend(chunks)
            
            # Update end time
            self.stats["end_time"] = datetime.now().isoformat()
            
            # Save processed chunks
            chunks_file = self.processed_data_dir / "content_chunks.json"
            with open(chunks_file, "w") as f:
                json.dump([chunk.to_dict() for chunk in all_chunks], f, indent=2)
            logger.info(f"Saved {len(all_chunks)} chunks to {chunks_file}")
            
            # Save statistics
            stats_file = self.processed_data_dir / "processing_stats.json"
            with open(stats_file, "w") as f:
                json.dump(self.stats, f, indent=2)
            logger.info(f"Processing completed. Statistics saved to {stats_file}")
            
        except Exception as e:
            logger.error(f"Error processing content: {str(e)}")
            raise

if __name__ == "__main__":
    # Example usage
    processor = ContentProcessor(
        raw_data_dir="raw_data",
        processed_data_dir="processed_data"
    )
    processor.process_all_content() 