import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv
from content_processor import ContentProcessor
from pinecone_manager import PineconeManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main function to process content and upload to Pinecone."""
    try:
        # Load environment variables
        load_dotenv()
        
        # Check for required environment variables
        required_vars = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "PINECONE_API_KEY"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        # Initialize processors
        content_processor = ContentProcessor(
            raw_data_dir="raw_data",
            processed_data_dir="processed_data"
        )
        
        pinecone_manager = PineconeManager(
            api_key=os.getenv("PINECONE_API_KEY"),
            environment=os.getenv("PINECONE_ENVIRONMENT", "gcp-starter")
        )
        
        # Process content
        logger.info("Starting content processing...")
        content_processor.process_all_content()
        
        # Load processed chunks
        chunks_file = Path("processed_data/content_chunks.json")
        if not chunks_file.exists():
            raise FileNotFoundError("No processed chunks found. Please run content processing first.")
        
        with open(chunks_file, "r") as f:
            chunks = json.load(f)
        
        # Upload to Pinecone
        logger.info(f"Uploading {len(chunks)} chunks to Pinecone...")
        pinecone_manager.upsert_chunks(chunks)
        
        # Get and display index statistics
        stats = pinecone_manager.get_stats()
        logger.info(f"Pinecone index statistics: {stats}")
        
    except Exception as e:
        logger.error(f"Error in main process: {str(e)}")
        raise

if __name__ == "__main__":
    main() 