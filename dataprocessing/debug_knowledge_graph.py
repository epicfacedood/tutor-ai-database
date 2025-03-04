import os
import json
from typing import List, Dict, Set, Tuple
from dotenv import load_dotenv
import networkx as nx
import re

# Define syllabus-based mathematical concepts
MATH_CONCEPTS = {
    'functions': {
        'basic_concepts': ['function', 'domain', 'range', 'one-to-one function', 'inverse function', 'composite function', 'mapping'],
        'trigonometric': [
            'sine', 'cosine', 'tangent', 'sin', 'cos', 'tan',
            'arcsin', 'arccos', 'arctan', 'inverse sine', 'inverse cosine', 'inverse tangent',
            'trigonometric function', 'trig function', 'trig', 'trigonometry'
        ],
        'reciprocal': ['cosecant', 'secant', 'cotangent', 'csc', 'sec', 'cot'],
        'characteristics': ['symmetry', 'intersections', 'turning points', 'asymptotes', 'periodicity', 'amplitude', 'frequency'],
        'properties': ['injective', 'surjective', 'bijective', 'monotonic', 'even', 'odd']
    },
    'graphs': {
        'transformations': ['translation', 'scaling', 'reflection', 'rotation', 'dilation', 'compression'],
        'features': ['intercepts', 'asymptotes', 'stationary points', 'inflection points', 'critical points', 'extrema'],
        'types': ['linear', 'quadratic', 'cubic', 'exponential', 'logarithmic', 'trigonometric', 'rational', 'piecewise'],
        'analysis': ['continuity', 'differentiability', 'concavity', 'convexity', 'monotonicity']
    },
    'calculus': {
        'limits': ['limit', 'continuity', 'differentiability', 'one-sided limit', 'infinite limit', 'limit at infinity'],
        'derivatives': ['derivative', 'gradient', 'rate of change', 'chain rule', 'product rule', 'quotient rule', 'implicit differentiation'],
        'integration': ['integral', 'antiderivative', 'definite integral', 'indefinite integral', 'area under curve', 'riemann sum'],
        'applications': ['optimization', 'rate of change', 'area', 'volume', 'velocity', 'acceleration', 'related rates']
    },
    'algebra': {
        'equations': ['linear equation', 'quadratic equation', 'simultaneous equations', 'inequalities', 'absolute value equation'],
        'polynomials': ['polynomial', 'factorization', 'remainder theorem', 'factor theorem', 'rational root theorem', 'synthetic division'],
        'complex': ['complex number', 'imaginary number', 'modulus', 'argument', 'conjugate', 'polar form', 'de moivre\'s theorem'],
        'matrices': ['matrix', 'determinant', 'inverse', 'eigenvalue', 'eigenvector', 'linear transformation']
    },
    'vectors': {
        'basic': ['vector', 'scalar', 'magnitude', 'direction', 'unit vector', 'position vector'],
        'operations': ['addition', 'subtraction', 'scalar multiplication', 'dot product', 'cross product', 'projection'],
        'applications': ['position vector', 'displacement', 'velocity', 'acceleration', 'force', 'work', 'moment'],
        'geometry': ['line', 'plane', 'distance', 'angle between vectors', 'parallel', 'perpendicular']
    },
    'sequences': {
        'types': ['arithmetic sequence', 'geometric sequence', 'convergence', 'divergence', 'monotonic', 'bounded'],
        'series': ['arithmetic series', 'geometric series', 'sum to infinity', 'partial sum', 'convergence test'],
        'applications': ['compound interest', 'growth', 'decay', 'population model', 'financial mathematics']
    },
    'angles': {
        'special': ['30°', '45°', '60°', '90°', '180°', '360°', '30 degrees', '45 degrees', '60 degrees', 'special angles'],
        'types': ['acute', 'obtuse', 'right', 'reference angle', 'basic angle', 'principal angle', 'coterminal angles'],
        'measurements': ['degrees', 'radians', 'π', 'pi', 'arc length', 'sector area'],
        'relationships': ['complementary', 'supplementary', 'adjacent', 'vertical', 'corresponding', 'alternate']
    }
}

# Define educational relationship patterns
RELATIONSHIP_PATTERNS = [
    # Hierarchical relationships
    (r'is a type of', 'is_a'),
    (r'is part of', 'part_of'),
    (r'belongs to', 'belongs_to'),
    (r'is a subset of', 'subset_of'),
    (r'is a special case of', 'special_case_of'),
    
    # Mathematical relationships
    (r'is defined as', 'defines'),
    (r'is equal to', 'equals'),
    (r'is related to', 'related_to'),
    (r'is the inverse of', 'inverse_of'),
    (r'is the reciprocal of', 'reciprocal_of'),
    (r'is equivalent to', 'equivalent_to'),
    (r'implies', 'implies'),
    (r'leads to', 'leads_to'),
    (r'can be derived from', 'derived_from'),
    (r'is used to calculate', 'calculates'),
    
    # Learning relationships
    (r'requires understanding of', 'requires'),
    (r'is used in', 'used_in'),
    (r'is applied to', 'applied_to'),
    (r'is a prerequisite for', 'prerequisite_for'),
    (r'builds upon', 'builds_upon'),
    (r'extends', 'extends'),
    (r'generalizes', 'generalizes'),
    
    # Assessment relationships
    (r'is tested in', 'tested_in'),
    (r'is assessed through', 'assessed_through'),
    (r'is part of the syllabus', 'syllabus_part'),
    (r'is a key concept in', 'key_concept_in'),
    (r'is commonly tested in', 'commonly_tested_in')
]

def clean_text(text: str) -> str:
    """Clean and normalize text for better pattern matching."""
    # Replace special characters with their normal equivalents
    text = text.replace('°', ' degrees')
    text = text.replace('π', 'pi')
    text = text.replace('×', 'x')
    text = text.replace('÷', '/')
    text = text.replace('−', '-')
    text = text.replace('–', '-')
    text = text.replace('—', '-')
    text = text.replace('\uf0b7', '')  # Remove bullet points
    text = text.replace('\uf028', '(')  # Replace special parentheses
    text = text.replace('\uf029', ')')
    text = text.replace('\uf03d', '=')  # Replace special equals sign
    
    # Remove extra whitespace and newlines
    text = ' '.join(text.split())
    
    # Convert to lowercase
    text = text.lower()
    
    return text

def load_content_chunks() -> List[Dict]:
    """Load content chunks from JSON file."""
    with open('dataprocessing/processed_data/content_chunks.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def load_syllabus_data() -> Dict:
    """Load syllabus data to understand educational structure."""
    with open('dataprocessing/processed_data/syllabus_data.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_concepts_from_text(text: str, syllabus_data: Dict) -> List[Dict]:
    """Extract mathematical concepts from text using syllabus-based patterns."""
    concepts = []
    text = clean_text(text)
    
    print("\nExtracting concepts from text...")
    print("Cleaned text preview:", text[:200] + "...")
    
    # Extract concepts based on predefined patterns
    for category, subcategories in MATH_CONCEPTS.items():
        for subcategory, terms in subcategories.items():
            for term in terms:
                term_clean = clean_text(term)
                if term_clean in text:
                    print(f"Found concept: {term} (category: {category}, subcategory: {subcategory})")
                    concepts.append({
                        'name': term,
                        'type': 'concept',
                        'category': category,
                        'subcategory': subcategory,
                        'related': []
                    })
    
    # Extract relationships between concepts
    print("\nExtracting relationships between concepts...")
    for concept1 in concepts:
        for concept2 in concepts:
            if concept1 != concept2:
                # Look for relationships in text between concepts
                text_between = text[text.find(clean_text(concept1['name'])):text.find(clean_text(concept2['name']))]
                for pattern, rel_type in RELATIONSHIP_PATTERNS:
                    if re.search(pattern, text_between):
                        print(f"Found relationship: {concept1['name']} {rel_type} {concept2['name']}")
                        concept1['related'].append({
                            'concept': concept2['name'],
                            'type': rel_type
                        })
    
    # Add syllabus-based relationships
    print("\nAdding syllabus-based relationships...")
    for concept in concepts:
        # Find where this concept appears in the syllabus
        for topic in syllabus_data:
            if 'subtopics' in topic:
                for subtopic in topic['subtopics']:
                    if clean_text(concept['name']) in clean_text(' '.join(subtopic.get('content', []))):
                        print(f"Found syllabus relationship: {concept['name']} is part of {topic['title']} - {subtopic['title']}")
                        concept['related'].append({
                            'concept': topic['title'],
                            'type': 'syllabus_part'
                        })
                        concept['related'].append({
                            'concept': subtopic['title'],
                            'type': 'syllabus_part'
                        })
    
    return concepts

def build_knowledge_graph(chunk: Dict, syllabus_data: Dict) -> nx.DiGraph:
    """Build a knowledge graph from a content chunk using syllabus-based extraction."""
    graph = nx.DiGraph()
    chunk_id = chunk.get('id', 'unknown')
    
    print("\nBuilding knowledge graph for chunk:", chunk_id)
    
    # Add metadata
    metadata = chunk.get('metadata', {})
    graph.add_node(chunk_id, type='chunk')
    
    if 'source' in metadata and metadata['source']:
        graph.add_node(metadata['source'], type='source')
        graph.add_edge(metadata['source'], chunk_id, type='is_source_of')
    if 'type' in metadata and metadata['type']:
        graph.add_node(metadata['type'], type='content_type')
        graph.add_edge(chunk_id, metadata['type'], type='has_type')
    if 'topics' in metadata and metadata['topics']:
        for topic in metadata['topics']:
            if topic:
                graph.add_node(topic, type='topic')
                graph.add_edge(chunk_id, topic, type='covers_topic')
    
    # Extract and add concepts
    content = metadata.get('content', '')
    if content:
        print("\nProcessing content...")
        print("Raw content preview:", content[:200] + "...")
        
        try:
            concepts = extract_concepts_from_text(content, syllabus_data)
            print(f"\nFound {len(concepts)} concepts")
            
            # Add concepts
            for concept in concepts:
                if 'name' in concept and concept['name']:
                    print(f"Adding concept: {concept['name']}")
                    graph.add_node(concept['name'], 
                                 type='concept',
                                 category=concept.get('category', 'unknown'),
                                 subcategory=concept.get('subcategory', 'unknown'))
                    # Link concept to chunk
                    graph.add_edge(concept['name'], chunk_id, type='appears_in')
                    
                    # Add related concepts
                    if 'related' in concept:
                        for related in concept['related']:
                            if related['concept']:
                                print(f"Adding relationship: {concept['name']} -> {related['concept']}")
                                graph.add_edge(concept['name'], 
                                             related['concept'], 
                                             type=related['type'])
        except Exception as e:
            print(f"Error processing concepts: {str(e)}")
    else:
        print("No content found in chunk metadata")
    
    return graph

def debug_knowledge_graph():
    """Build the complete knowledge graph from all content chunks."""
    # Load content chunks and syllabus data
    chunks = load_content_chunks()
    syllabus_data = load_syllabus_data()
    print(f"Loaded {len(chunks)} chunks")
    
    # Create a combined graph
    combined_graph = nx.DiGraph()
    
    # Process all chunks
    for i, chunk in enumerate(chunks):
        if (i + 1) % 100 == 0:  # Progress update every 100 chunks
            print(f"\nProcessing chunk {i+1} of {len(chunks)}...")
        
        try:
            # Build the graph for this chunk
            chunk_graph = build_knowledge_graph(chunk, syllabus_data)
            
            # Combine with the main graph
            combined_graph = nx.compose(combined_graph, chunk_graph)
            
            # Add trigonometric relationships for trigonometry-related chunks
            if 'trigonometry' in str(chunk.get('metadata', {}).get('topics', [])):
                # Add relationships between trigonometric functions
                trig_functions = ['sine', 'cosine', 'tangent', 'sin', 'cos', 'tan']
                for func1 in trig_functions:
                    for func2 in trig_functions:
                        if func1 != func2:
                            if func1 in combined_graph.nodes and func2 in combined_graph.nodes:
                                combined_graph.add_edge(func1, func2, type='related_to')
                
                # Add relationships between angles and trigonometric functions
                angle_types = ['acute', 'obtuse', 'right', 'reference angle', 'basic angle']
                for angle in angle_types:
                    if angle in combined_graph.nodes:
                        for func in trig_functions:
                            if func in combined_graph.nodes:
                                combined_graph.add_edge(angle, func, type='used_in')
        except Exception as e:
            print(f"Error processing chunk {i+1}: {str(e)}")
            continue
    
    # Save the combined graph
    nx.write_gml(combined_graph, 'dataprocessing/processed_data/knowledge_graph.gml')
    
    # Print graph statistics
    print(f"\nFinal Graph Statistics:")
    print(f"Number of nodes: {len(combined_graph.nodes)}")
    print(f"Number of edges: {len(combined_graph.edges)}")
    print("\nNode types:")
    node_types = nx.get_node_attributes(combined_graph, 'type')
    for node_type in set(node_types.values()):
        count = sum(1 for t in node_types.values() if t == node_type)
        print(f"- {node_type}: {count}")
    print("\nEdge types:")
    edge_types = nx.get_edge_attributes(combined_graph, 'type')
    for edge_type in set(edge_types.values()):
        count = sum(1 for t in edge_types.values() if t == edge_type)
        print(f"- {edge_type}: {count}")
    
    # Print concept categories
    print("\nConcept Categories:")
    concept_categories = {}
    for node in combined_graph.nodes:
        if combined_graph.nodes[node].get('type') == 'concept':
            category = combined_graph.nodes[node].get('category', 'unknown')
            if category not in concept_categories:
                concept_categories[category] = 0
            concept_categories[category] += 1
    for category, count in concept_categories.items():
        print(f"- {category}: {count}")
    
    print("\nGraph saved to dataprocessing/processed_data/knowledge_graph.gml")

if __name__ == "__main__":
    debug_knowledge_graph() 