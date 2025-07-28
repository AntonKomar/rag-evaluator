import json
import random
import logging
from typing import Dict, List
import numpy as np
from pinecone import Pinecone

from rag_evaluator.framework.evaluation_data import TestCase

from ..constants import QuestionType
from ..clients.gemini_client import get_gemini_client
from .question_cache import QuestionCache


class QuestionGenerator:
    def __init__(self):
        self.cache = QuestionCache()
        self.logger = logging.getLogger("rag_evaluator.llm_question_generator")
        self.gemini_client = get_gemini_client()
    
    def connect_pinecone(self, api_key: str, index_name: str):
        pc = Pinecone(api_key=api_key)
        return pc.Index(index_name)
    
    def _calculate_documents_needed(self, counts_per_type: Dict[QuestionType, int]) -> int:
        total_docs = 0
        
        for question_type, count in counts_per_type.items():
            if question_type == QuestionType.SIMPLE:
                total_docs += count * 1
            elif question_type == QuestionType.COMPLEX:
                total_docs += count * 3
            else:
                total_docs += count * 2
        
        buffer = max(5, int(total_docs * 0.1))
        return total_docs + buffer
    
    def _sample_documents_from_pinecone(self, index, sample_size: int = 100) -> List[Dict]:
        documents = []
        
        try:
            stats = index.describe_index_stats()
            dimensions = stats['dimension']

            docs_per_query = min(50, sample_size)
            num_queries = (sample_size + docs_per_query - 1) // docs_per_query
            
            for _ in range(num_queries):
                if len(documents) >= sample_size:
                    break

                random_vector = np.random.randn(dimensions)
                random_vector = random_vector / np.linalg.norm(random_vector)

                remaining_docs = sample_size - len(documents)
                query_limit = min(docs_per_query, remaining_docs)
                
                results = index.query(
                    vector=random_vector.tolist(),
                    top_k=query_limit,
                    include_metadata=True
                )
                
                for match in results.matches:
                    if match.metadata:
                        documents.append({
                            'id': match.id,
                            'text': match.metadata.get('text', ''),
                            'source': match.metadata.get('source', 'unknown'),
                            'score': match.score
                        })
        
        except Exception as e:
            self.logger.error(f"Failed to sample documents from Pinecone: {e}")
            raise
        
        return documents
    
    def generate_questions(self, 
                        pinecone_config: Dict,
                        question_types: List[QuestionType],
                        counts_per_type: Dict[QuestionType, int],
                        force_regenerate: bool = False) -> List[Dict]:
        generation_config = {
            'question_types': [qt.value for qt in question_types],
            'counts_per_type': {qt.value: count for qt, count in counts_per_type.items()}
        }
        
        if not force_regenerate:
            cached_questions = self.cache.get_cached_questions(generation_config)
            if cached_questions:
                return cached_questions
        
        self.logger.info("Generating questions...")

        sample_size = self._calculate_documents_needed(counts_per_type)
        self.logger.info(f"{sample_size} documents needed for generation")
        
        index = self.connect_pinecone(pinecone_config['api_key'], pinecone_config['index_name'])
        documents = self._sample_documents_from_pinecone(index, sample_size)
        
        if not documents:
            raise ValueError("No documents found in Pinecone index")
        
        self.logger.info(f"Sampled {len(documents)} documents from Pinecone")
        
        all_questions = self._generate_all_questions(documents, question_types, counts_per_type)
        
        self.cache.cache_questions(all_questions, generation_config)
        
        self.logger.info(f"Generated total of {len(all_questions)} questions")
        return all_questions
    
    def _generate_all_questions(self, 
                                documents: List[Dict],
                                question_types: List[QuestionType],
                                counts_per_type: Dict[QuestionType, int]) -> List[Dict]:
        contexts = self._prepare_contexts(documents, question_types, counts_per_type)
        
        prompt = self._create_prompt(contexts, question_types, counts_per_type)
        
        try:
            response = self.gemini_client.generate_for_questions(prompt)
            questions = self._parse_response(response, contexts)
            
            return questions
            
        except Exception as e:
            self.logger.error(f"Failed to generate questions: {e}")
            return []
    
    def _prepare_contexts(self, 
                                   documents: List[Dict],
                                   question_types: List[QuestionType],
                                   counts_per_type: Dict[QuestionType, int]) -> List[Dict]:
        contexts = []
        question_id = 0
        doc_index = 0

        shuffled_docs = documents.copy()
        random.shuffle(shuffled_docs)
        
        for question_type in question_types:
            count = counts_per_type.get(question_type, 1)
            
            for i in range(count):
                if question_type == QuestionType.SIMPLE:
                    docs_needed = 1
                elif question_type == QuestionType.COMPLEX:
                    docs_needed = 3
                else:
                    docs_needed = 2
                
                selected_docs = []
                for _ in range(docs_needed):
                    if doc_index < len(shuffled_docs):
                        selected_docs.append(shuffled_docs[doc_index])
                        doc_index += 1
                    else:
                        selected_docs.append(shuffled_docs[doc_index % len(shuffled_docs)])
                        doc_index += 1
                
                context_text = "\n\n".join([doc['text'][:800] for doc in selected_docs])
                
                contexts.append({
                    'id': question_id,
                    'type': question_type.value,
                    'context': context_text,
                    'source_docs': selected_docs
                })
                
                question_id += 1
        
        return contexts
    
    def _create_prompt(self, 
                        contexts: List[Dict],
                        question_types: List[QuestionType],
                        counts_per_type: Dict[QuestionType, int]) -> str:
        
        type_descriptions = {
            QuestionType.SIMPLE: "Straightforward factual questions with clear, direct answers",
            QuestionType.COMPLEX: "Complex questions requiring reasoning or connecting multiple pieces of information",
            QuestionType.DISTRACTING: "Questions with some distracting information but focusing on the main context",
            QuestionType.SITUATIONAL: "Questions with user context or specific scenarios",
            QuestionType.DOUBLE: "Questions with two distinct parts connected by 'and'",
            QuestionType.CONVERSATIONAL: "Conversational questions as part of an ongoing dialogue"
        }
        
        generation_summary = []
        for question_type in question_types:
            count = counts_per_type.get(question_type, 1)
            description = type_descriptions.get(question_type, "Relevant questions")
            generation_summary.append(f"- {count} {question_type.value} questions: {description}")
        
        summary_text = "\n".join(generation_summary)
        
        contexts_text = []
        for ctx in contexts:
            contexts_text.append(f"Question {ctx['id']} ({ctx['type']}):\nContext: {ctx['context']}")
        
        contexts_str = "\n\n".join(contexts_text)
        
        prompt = f"""You are an expert at generating evaluation questions for RAG (Retrieval Augmented Generation) systems. Generate questions based on the provided contexts.

Generate the following questions:
{summary_text}

Here are the contexts for each question:
{contexts_str}

For each question ID, generate a question with its ground truth answer.

Respond with ONLY valid JSON:
{{
  "0": {{
    "question": "Generated question text",
    "ground_truth": "Complete correct answer based on context", 
    "entities": ["entity1", "entity2"]
  }},
  "1": {{
    "question": "Generated question text",
    "ground_truth": "Complete correct answer based on context",
    "entities": ["entity1", "entity2"] 
  }}
}}

Important: 
- Ground truth must be answerable from the provided context
- Questions should be appropriate for their type
- Entities are optional but useful for evaluation
- Response must be valid JSON only

Response:"""
        
        return prompt
    
    def _parse_response(self, response: str, contexts: List[Dict]) -> List[TestCase]:
        """Simplified parsing to create TestCase objects"""
        try:
            # Clean response
            response = response.strip()
            # log response for debugging
            self.logger.debug(f"Raw response from Gemini: {response}...")
            if response.startswith("```json"):
                response = response[7:-3]
            elif response.startswith("```"):
                response = response[3:-3]
            
            # Extract JSON
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            json_str = response[start_idx:end_idx]
            
            raw_questions = json.loads(json_str)
            
            test_cases = []
            for ctx in contexts:
                question_id = str(ctx['id'])
                
                if question_id in raw_questions:
                    q_data = raw_questions[question_id]
                    
                    if q_data.get('question') and q_data.get('ground_truth'):
                        test_case = TestCase(
                            question=q_data['question'].strip(),
                            ground_truth=q_data['ground_truth'].strip(),
                            question_type=ctx['type'],
                            entities=q_data.get('entities', [])
                        )
                        test_cases.append(test_case)
                        
                        self.logger.debug(f"Generated {ctx['type']} question: {test_case.question[:50]}...")
            
            self.logger.info(f"Successfully generated {len(test_cases)} test cases")
            return test_cases
            
        except Exception as e:
            self.logger.error(f"Failed to parse question generation response: {e}")
            return []