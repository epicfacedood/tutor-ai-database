#!/usr/bin/env python3
"""
Enhanced prompts for educational content extraction.
These prompts are designed to extract more detailed and structured information
from educational PDFs for use in a RAG-based tutoring system.
"""

def get_enhanced_extraction_prompt(text, metadata, json_schema=None):
    """
    Generate an enhanced prompt for extracting educational content.
    
    Args:
        text: The text extracted from the PDF
        metadata: Metadata about the document
        json_schema: Optional JSON schema to use
        
    Returns:
        A string containing the prompt
    """
    
    # Default schema if none provided
    default_schema = """
    {
      "metadata": {
        "subject": "string",
        "topic": "string",
        "subtopic": "string",
        "education_level": "string",
        "syllabus_reference": "string",
        "exam_board": "string"
      },
      "content": {
        "summary": "string",
        "key_concepts": [
          {
            "concept_name": "string",
            "definition": "string",
            "explanation": "string",
            "formulas": ["string"],
            "examples": [
              {
                "problem_statement": "string",
                "solution_steps": ["string"],
                "final_answer": "string"
              }
            ]
          }
        ],
        "practice_questions": [
          {
            "question_text": "string",
            "difficulty_level": "string",
            "solution": {
              "steps": ["string"],
              "final_answer": "string"
            },
            "hints": ["string"]
          }
        ]
      },
      "relationships": {
        "prerequisites": ["string"],
        "related_topics": ["string"]
      }
    }
    """
    
    # Create the enhanced prompt
    prompt = f"""You are an expert educational content analyzer specializing in {metadata.get('subject', 'Mathematics')} for {metadata.get('education_level', 'JC / A Level')} students. 

Your task is to extract structured information from educational content and format it as JSON for a tutoring AI system. This system will use RAG (Retrieval Augmented Generation) to provide personalized tutoring to students.

DOCUMENT METADATA:
- Subject: {metadata.get('subject', 'Mathematics')}
- Topic: {metadata.get('topic', 'Unknown')}
- Education Level: {metadata.get('education_level', 'JC / A Level')}
- Filename: {metadata.get('filename', 'Unknown')}

EXTRACTION INSTRUCTIONS:
1. Carefully analyze the educational content to identify:
   - Main topic and subtopics
   - Key concepts, definitions, theorems, and principles
   - Mathematical formulas and equations (preserve their structure)
   - Step-by-step examples and their solutions
   - Practice questions and their solutions
   - Exam tips and common mistakes

2. For each key concept:
   - Provide a clear, concise definition
   - Add a detailed explanation suitable for students
   - Include all relevant formulas with variable explanations
   - Extract complete examples with step-by-step solutions
   - Note any common misconceptions or pitfalls

3. For each practice question:
   - Include the complete question text
   - Estimate difficulty level (Easy, Medium, Hard)
   - Provide a detailed solution with steps
   - Create helpful hints that guide without giving away the answer
   - Identify which concepts are being tested

4. Identify relationships between concepts:
   - Prerequisites needed to understand this content
   - Related topics that build on this content
   - Connections to other areas of the subject

5. Create a concise summary of the entire content

{f'Use the following JSON schema: {json_schema}' if json_schema else f'Use the following JSON structure: {default_schema}'}

EDUCATIONAL CONTENT:
{text}

IMPORTANT GUIDELINES:
- Preserve mathematical notation as clearly as possible
- Include ALL relevant information from the content
- Structure the information hierarchically
- Be comprehensive but avoid redundancy
- Ensure the JSON is valid and properly formatted
- Focus on accuracy and educational value

Return ONLY the JSON without any additional text or explanations."""
    
    return prompt

def get_syllabus_mapping_prompt(text, syllabus_text, metadata):
    """
    Generate a prompt for mapping content to syllabus requirements.
    
    Args:
        text: The text extracted from the PDF
        syllabus_text: Text from the syllabus document
        metadata: Metadata about the document
        
    Returns:
        A string containing the prompt
    """
    
    prompt = f"""You are an expert curriculum analyst specializing in {metadata.get('subject', 'Mathematics')} education. 

Your task is to map the given educational content to specific syllabus requirements. This mapping will help a tutoring AI system provide curriculum-aligned responses.

DOCUMENT METADATA:
- Subject: {metadata.get('subject', 'Mathematics')}
- Topic: {metadata.get('topic', 'Unknown')}
- Education Level: {metadata.get('education_level', 'JC / A Level')}

SYLLABUS CONTENT:
{syllabus_text[:2000]}  # First 2000 chars of syllabus for context

EDUCATIONAL CONTENT:
{text[:1000]}  # First 1000 chars of content for context

MAPPING INSTRUCTIONS:
1. Identify which specific syllabus topics and subtopics this content covers
2. Assign syllabus reference codes to each concept in the content
3. Note any content that goes beyond the syllabus requirements
4. Identify any syllabus requirements that are not covered by the content

Return your analysis as JSON with the following structure:
{{
  "syllabus_mapping": [
    {{
      "content_topic": "string",
      "syllabus_reference": "string",
      "syllabus_description": "string",
      "coverage_level": "string",  // "Complete", "Partial", or "Minimal"
      "missing_elements": ["string"]
    }}
  ],
  "beyond_syllabus": [
    {{
      "content_topic": "string",
      "description": "string"
    }}
  ],
  "syllabus_gaps": [
    {{
      "syllabus_reference": "string",
      "syllabus_description": "string",
      "importance": "string"  // "Core", "Supplementary", or "Advanced"
    }}
  ]
}}

Return ONLY the JSON without any additional text or explanations."""
    
    return prompt

def get_question_generation_prompt(content_json):
    """
    Generate a prompt for creating additional practice questions.
    
    Args:
        content_json: The JSON content extracted from the PDF
        
    Returns:
        A string containing the prompt
    """
    
    # Extract key concepts for context
    concepts = []
    if "content" in content_json and "key_concepts" in content_json["content"]:
        for concept in content_json["content"]["key_concepts"]:
            concepts.append({
                "name": concept.get("concept_name", ""),
                "definition": concept.get("definition", "")
            })
    
    concepts_str = "\n".join([f"- {c['name']}: {c['definition']}" for c in concepts[:5]])
    
    prompt = f"""You are an expert {content_json.get('metadata', {}).get('subject', 'Mathematics')} educator specializing in creating high-quality practice questions for {content_json.get('metadata', {}).get('education_level', 'JC / A Level')} students.

Your task is to create additional practice questions based on the educational content provided. These questions will be used by a tutoring AI system to help students practice and assess their understanding.

CONTENT TOPIC: {content_json.get('metadata', {}).get('topic', 'Unknown')}

KEY CONCEPTS:
{concepts_str}

QUESTION GENERATION INSTRUCTIONS:
1. Create 5 practice questions of varying difficulty (Easy, Medium, Hard)
2. For each question:
   - Write a clear, concise question statement
   - Provide a detailed step-by-step solution
   - Include 2-3 helpful hints that guide without giving away the answer
   - Specify which concepts are being tested
   - Estimate the time needed to solve the question
   - Assign an appropriate number of marks

3. Ensure questions test different aspects of the topic and require different skills
4. Include a mix of question types (calculation, proof, application, etc.)
5. Make questions realistic and relevant to the curriculum

Return your questions as JSON with the following structure:
{{
  "generated_questions": [
    {{
      "question_id": "string",
      "question_text": "string",
      "difficulty_level": "string",
      "marks_available": number,
      "time_estimate_minutes": number,
      "concepts_tested": ["string"],
      "solution": {{
        "steps": ["string"],
        "final_answer": "string"
      }},
      "hints": ["string"]
    }}
  ]
}}

Return ONLY the JSON without any additional text or explanations."""
    
    return prompt

def get_concept_relationship_prompt(content_json, syllabus_text=None):
    """
    Generate a prompt for identifying relationships between concepts.
    
    Args:
        content_json: The JSON content extracted from the PDF
        syllabus_text: Optional text from the syllabus document
        
    Returns:
        A string containing the prompt
    """
    
    # Extract concepts
    concepts = []
    if "content" in content_json and "key_concepts" in content_json["content"]:
        concepts = [c.get("concept_name", "") for c in content_json["content"]["key_concepts"]]
    
    concepts_str = "\n".join([f"- {c}" for c in concepts])
    
    syllabus_context = ""
    if syllabus_text:
        syllabus_context = f"""
SYLLABUS CONTEXT:
{syllabus_text[:1000]}  # First 1000 chars of syllabus
"""
    
    prompt = f"""You are an expert in {content_json.get('metadata', {}).get('subject', 'Mathematics')} curriculum design with deep knowledge of how concepts build upon each other.

Your task is to analyze the relationships between concepts in the given educational content and create a concept map that shows prerequisites, related topics, and progression paths.

CONTENT TOPIC: {content_json.get('metadata', {}).get('topic', 'Unknown')}

CONCEPTS IDENTIFIED:
{concepts_str}
{syllabus_context}

RELATIONSHIP ANALYSIS INSTRUCTIONS:
1. For each concept, identify:
   - Prerequisites: Concepts that must be understood before this one
   - Related concepts: Concepts that are closely related or complementary
   - Follows from: Concepts that naturally lead to this one
   - Leads to: More advanced concepts that build upon this one

2. Identify any missing concepts that should be included in the concept map
3. Organize concepts into a logical learning sequence
4. Note any particularly important concept relationships

Return your analysis as JSON with the following structure:
{{
  "concept_relationships": [
    {{
      "concept": "string",
      "prerequisites": ["string"],
      "related_concepts": ["string"],
      "follows_from": ["string"],
      "leads_to": ["string"],
      "importance": "string"  // "Foundational", "Core", or "Advanced"
    }}
  ],
  "missing_concepts": [
    {{
      "concept": "string",
      "description": "string",
      "relationship_to_existing": "string"
    }}
  ],
  "learning_sequence": ["string"],
  "key_relationships": [
    {{
      "from_concept": "string",
      "to_concept": "string",
      "relationship_type": "string",
      "importance": "string"
    }}
  ]
}}

Return ONLY the JSON without any additional text or explanations."""
    
    return prompt 