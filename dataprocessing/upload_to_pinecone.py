import os
import json
from pinecone import Pinecone
from dotenv import load_dotenv
from tqdm import tqdm

# Load environment variables
load_dotenv()

# Initialize Pinecone
pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))

# Get the index
index_name = os.getenv('PINECONE_INDEX')
index = pc.Index(index_name)

def load_content_chunks():
    """Load content chunks from the JSON file"""
    with open('dataprocessing/processed_data/content_chunks.json', 'r') as f:
        return json.load(f)

def upload_to_pinecone(chunks, batch_size=100):
    """Upload chunks to Pinecone in batches"""
    total_chunks = len(chunks)
    print(f"Uploading {total_chunks} chunks to Pinecone...")
    
    for i in tqdm(range(0, total_chunks, batch_size)):
        batch = chunks[i:i + batch_size]
        
        # Prepare vectors for upload
        vectors = []
        for chunk in batch:
            vectors.append({
                'id': chunk['id'],
                'values': chunk['values'],
                'metadata': {
                    'text': chunk.get('text', ''),
                    'source': chunk.get('source', ''),
                    'type': chunk.get('type', 'content')
                }
            })
        
        try:
            # Upload batch to Pinecone
            index.upsert(vectors=vectors)
        except Exception as e:
            print(f"\nError uploading batch {i//batch_size + 1}: {str(e)}")
            print("Please check your Pinecone console for more details.")
            return False
    
    return True

def verify_upload():
    """Verify the upload by checking index stats"""
    stats = index.describe_index_stats()
    print(f"\nIndex Stats: {stats}")
    return stats['total_vector_count'] > 0

def main():
    try:
        # Load content chunks
        chunks = load_content_chunks()
        
        # Upload to Pinecone
        if upload_to_pinecone(chunks):
            # Verify the upload
            if verify_upload():
                print("\nUpload complete and verified!")
            else:
                print("\nUpload completed but verification failed. Please check your Pinecone console.")
        else:
            print("\nUpload failed. Please check the error messages above.")
            
    except Exception as e:
        print(f"\nError: {str(e)}")
        print("Please check your Pinecone console for more details.")

if __name__ == "__main__":
    main() 