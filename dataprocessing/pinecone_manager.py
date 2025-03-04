import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import pinecone
from tenacity import retry, stop_after_attempt, wait_exponential
import logging
from datetime import datetime

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

class PineconeManager:
    def __init__(self, api_key: str, environment: str):
        """Initialize Pinecone client."""
        self.pc = pinecone.Pinecone(api_key=api_key)
        self.index_name = os.getenv("PINECONE_INDEX", "h2-math-index")
        
        # Create index if it doesn't exist
        if self.index_name not in self.pc.list_indexes().names():
            self.pc.create_index(
                name=self.index_name,
                dimension=1536,
                metric='cosine',
                spec=pinecone.ServerlessSpec(
                    cloud='aws',
                    region='us-east-1'
                )
            )
            logger.info(f"Created new index: {self.index_name}")
        
        self.index = self.pc.Index(self.index_name)
        logger.info(f"Connected to index: {self.index_name}")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def upsert_chunks(self, chunks: List[ContentChunk], batch_size: int = 100):
        """Upsert chunks to Pinecone in batches."""
        total_chunks = len(chunks)
        for i in range(0, total_chunks, batch_size):
            batch = chunks[i:i + batch_size]
            vectors = [
                {
                    "id": chunk.id,
                    "values": chunk.values,
                    "metadata": chunk.metadata
                }
                for chunk in batch
            ]
            
            try:
                self.index.upsert(vectors=vectors)
                logger.info(f"Upserted batch {i//batch_size + 1} of {(total_chunks + batch_size - 1)//batch_size}")
            except Exception as e:
                logger.error(f"Error upserting batch: {str(e)}")
                raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def query(self, vector: List[float], top_k: int = 5, filter: Optional[Dict] = None) -> List[Dict]:
        """Query the index with a vector and optional filters."""
        try:
            results = self.index.query(
                vector=vector,
                top_k=top_k,
                filter=filter,
                include_metadata=True
            )
            return results.matches
        except Exception as e:
            logger.error(f"Error querying index: {str(e)}")
            raise

    def delete_all(self):
        """Delete all vectors from the index."""
        try:
            self.index.delete(delete_all=True)
            logger.info("Deleted all vectors from index")
        except Exception as e:
            logger.error(f"Error deleting vectors: {str(e)}")
            raise

    def get_stats(self) -> Dict:
        """Get index statistics."""
        try:
            stats = self.index.describe_index_stats()
            return {
                "total_vector_count": stats.total_vector_count,
                "dimension": stats.dimension,
                "index_fullness": stats.index_fullness
            }
        except Exception as e:
            logger.error(f"Error getting index stats: {str(e)}")
            raise

if __name__ == "__main__":
    # Example usage
    api_key = os.getenv("PINECONE_API_KEY")
    environment = os.getenv("PINECONE_ENVIRONMENT")
    
    if not api_key or not environment:
        raise ValueError("Please set PINECONE_API_KEY and PINECONE_ENVIRONMENT environment variables")
    
    manager = PineconeManager(api_key, environment)
    stats = manager.get_stats()
    print(f"Index statistics: {stats}") 