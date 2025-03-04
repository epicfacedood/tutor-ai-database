import os
import time
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Pinecone
pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))

# Use a more descriptive index name
index_name = "supertutor-embeddings"

# Delete existing index if it exists
if index_name in pc.list_indexes():
    print(f"Deleting existing index: {index_name}")
    pc.delete_index(index_name)
    # Wait for deletion to complete
    while index_name in pc.list_indexes():
        print("Waiting for index deletion to complete...")
        time.sleep(5)
    print(f"Successfully deleted index: {index_name}")

# Create new index with correct dimension
print(f"Creating new index: {index_name}")
try:
    pc.create_index(
        name=index_name,
        dimension=384,  # Match the dimension of your vectors
        metric="cosine",  # Using cosine similarity for normalized vectors
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"
        )
    )

    # Wait for index to be ready with timeout
    max_wait_time = 300  # 5 minutes
    start_time = time.time()
    while index_name not in pc.list_indexes():
        if time.time() - start_time > max_wait_time:
            raise TimeoutError("Index creation timed out after 5 minutes")
        print("Waiting for index creation to complete...")
        time.sleep(5)

    # Additional check to ensure index is ready
    try:
        index = pc.Index(index_name)
        index.describe_index_stats()
        print(f"Successfully created and verified index: {index_name} with dimension 384")
        
        # Update the .env file with the new index name
        env_path = '.env'
        with open(env_path, 'r') as file:
            lines = file.readlines()
        
        with open(env_path, 'w') as file:
            for line in lines:
                if line.startswith('PINECONE_INDEX='):
                    file.write(f'PINECONE_INDEX={index_name}\n')
                else:
                    file.write(line)
        
        print(f"Updated .env file with new index name: {index_name}")
    except Exception as e:
        print(f"Index created but verification failed: {str(e)}")
        print("Please check your Pinecone console for more details.")

except Exception as e:
    print(f"Error creating index: {str(e)}")
    print("Please check your Pinecone console for more details.") 