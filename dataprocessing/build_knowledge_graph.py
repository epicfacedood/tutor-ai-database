import os
import json
from typing import List, Dict
from langchain_community.graphs import NetworkxEntityGraph
from langchain_community.graphs.networkx_graph import KnowledgeTriple
from langchain_anthropic import ChatAnthropic
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
from tqdm import tqdm
import networkx as nx

# Load environment variables
load_dotenv()

# Check for API key
api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

# Initialize the LLM
try:
    llm = ChatAnthropic(
        model="claude-3-sonnet-20240229",
        anthropic_api_key=api_key,
        temperature=0.1  # Lower temperature for more focused outputs
    )
    print("LLM initialized successfully")
except Exception as e:
    print(f"Error initializing LLM: {str(e)}")
    raise

# Define the knowledge extraction prompt
KNOWLEDGE_EXTRACTION_PROMPT = PromptTemplate(
    input_variables=["content"],
    template="""Extract key knowledge triples from the following educational content. 
    Focus on core concepts, definitions, examples, and relationships.
    Format each triple as: subject | predicate | object
    Only include the most important and clear relationships.
    
    Content:
    {content}
    
    Triples:"""
)

def load_content_chunks() -> List[Dict]:
    """Load content chunks from JSON file."""
    with open('dataprocessing/processed_data/content_chunks.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def create_triple(subject: str, predicate: str, object_: str) -> KnowledgeTriple:
    """Create a KnowledgeTriple if all components are valid."""
    if subject and predicate and object_ and subject != "None" and predicate != "None" and object_ != "None":
        return KnowledgeTriple(
            subject=subject,
            predicate=predicate,
            object_=object_
        )
    return None

def extract_knowledge_triples(chunk: Dict) -> List[KnowledgeTriple]:
    """Extract knowledge triples from a content chunk."""
    triples = []
    chunk_id = chunk.get('id', 'unknown')
    
    # Add metadata triples
    if 'metadata' in chunk:
        metadata = chunk['metadata']
        if 'source' in metadata:
            triple = create_triple(
                subject=metadata['source'],
                predicate="is_source_of",
                object_=chunk_id
            )
            if triple:
                triples.append(triple)
        if 'type' in metadata:
            triple = create_triple(
                subject=chunk_id,
                predicate="has_type",
                object_=metadata['type']
            )
            if triple:
                triples.append(triple)
    
    # Extract content-based triples using LLM
    try:
        if 'content' in chunk and chunk['content']:
            prompt = KNOWLEDGE_EXTRACTION_PROMPT.format(content=chunk['content'])
            print(f"\nProcessing chunk {chunk_id}")
            print("Content preview:", chunk['content'][:200] + "...")
            print("Sending to LLM...")
            
            response = llm.invoke(prompt)
            print("LLM Response:")
            print(response)
            
            # Parse the response into triples
            for line in response.split('\n'):
                if '|' in line:
                    subject, predicate, obj = [part.strip() for part in line.split('|')]
                    triple = create_triple(subject, predicate, obj)
                    if triple:
                        triples.append(triple)
                        print(f"Created triple: {subject} | {predicate} | {obj}")
    except Exception as e:
        print(f"Error extracting triples from chunk {chunk_id}: {str(e)}")
        print(f"Error type: {type(e)}")
    
    return triples

def build_knowledge_graph():
    """Build a knowledge graph from content chunks."""
    # Initialize the graph
    graph = NetworkxEntityGraph()
    
    # Load content chunks
    chunks = load_content_chunks()
    print(f"Processing {len(chunks)} chunks...")
    
    # Process each chunk
    for chunk in tqdm(chunks):
        triples = extract_knowledge_triples(chunk)
        for triple in triples:
            if triple:  # Only add valid triples
                graph.add_triple(triple)
    
    # Save the graph using NetworkX's write_gml function
    nx.write_gml(graph._graph, 'dataprocessing/processed_data/knowledge_graph.gml')
    
    # Print graph statistics
    print(f"\nGraph Statistics:")
    print(f"Number of nodes: {len(graph._graph.nodes)}")
    print(f"Number of edges: {len(graph._graph.edges)}")
    print("Graph saved to dataprocessing/processed_data/knowledge_graph.gml")

if __name__ == "__main__":
    build_knowledge_graph() 