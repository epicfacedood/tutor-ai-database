import os
from pinecone import Pinecone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Pinecone
pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))

# Get the index
index_name = os.getenv('PINECONE_INDEX')
index = pc.Index(index_name)

# Get index description
description = index.describe_index_stats()
print(f"Index Description: {description}") 