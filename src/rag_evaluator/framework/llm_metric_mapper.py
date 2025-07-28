import json
import logging
from typing import List, Dict

from rag_evaluator.config import EvaluationConfig
from ..constants import MetricId, METRIC_INFO
from ..clients.gemini_client import get_gemini_client


class LLMMetricMapper:

    def __init__(self):
        self.logger = logging.getLogger("rag_evaluator.llm_metric_mapper")
        
        self.gemini_client = get_gemini_client()
    
    def map_all_questions(self, config: EvaluationConfig) -> None:
        self.logger.info("Mapping all questions to metrics")
        
        questions_data = self._collect_questions_data(config)
        
        if not questions_data:
            self.logger.warning("No questions found to map")
            return
        
        prompt = self._create_batch_mapping_prompt(questions_data)
        
        try:
            response = self.gemini_client.generate(prompt)
            
            mappings = self._parse_batch_response(response, questions_data)
            
            self._apply_mappings_to_config(config, mappings)
            
            total_questions = len(questions_data)
            mapped_count = sum(1 for mapping in mappings.values() if mapping)
            self.logger.info(f"Successfully mapped metrics for {mapped_count}/{total_questions} questions")
            
        except Exception as e:
            self.logger.error(f"Failed to map metrics in batch: {e}")
    
    def _collect_questions_data(self, config: EvaluationConfig) -> List[Dict]:
        questions_data = []
        question_id = 0
        
        for goal in config.goals:
            for question in goal.questions:
                if not question.metrics:
                    questions_data.append({
                        'id': question_id,
                        'goal_name': goal.name,
                        'goal_weight': goal.weight,
                        'question_text': question.text,
                        'question_weight': question.weight
                    })
                    question_id += 1
        
        return questions_data
    
    def _create_batch_mapping_prompt(self, questions_data: List[Dict]) -> str:
        available_metrics = []
        for metric_id, info in METRIC_INFO.items():
            use_cases_str = ", ".join(info.use_cases)
            available_metrics.append(
                f"- {info.name} ({metric_id.value}): {info.description}\n"
                f"  Use cases: {use_cases_str}"
            )
        
        available_metrics_str = "\n\n".join(available_metrics)
        
        questions_text = []
        for q_data in questions_data:
            questions_text.append(
                f"Question {q_data['id']}: {q_data['question_text']}\n"
                f"  Goal: {q_data['goal_name']} (Weight: {q_data['goal_weight']})\n"
                f"  Question Weight: {q_data['question_weight']}"
            )
        
        questions_str = "\n\n".join(questions_text)
        
        prompt = f"""You are an expert in RAG (Retrieval Augmented Generation) system evaluation. Your task is to select appropriate metrics and assign relevance weights for evaluating multiple aspects of a RAG system.

Available Metrics:
{available_metrics_str}

Questions to Evaluate:
{questions_str}

For each question, select metrics that would best evaluate that aspect of the RAG system and assign weights (0.1-1.0) based on relevance. Consider:
1. Which metrics directly address the question being asked
2. Higher weights = more relevant to the question.
3. The importance of the goal and question (higher weights may need more comprehensive evaluation)
4. Different aspects of RAG evaluation (retrieval, generation, system-wide)

Respond with ONLY a JSON object where each key is the question ID and the value is an object of metric IDs (strings) with weights. Use the exact metric IDs shown in parentheses above.

Format as JSON:
{{
  "0": {{
    "faithfulness": 1.0,
    "factual_consistency": 0.8,
    "answer_relevance": 0.6
  }},
  "1": {{
    "context_precision": 1.0,
    "context_relevance": 0.9
  }}
}}

Important: Your response must be a valid JSON object with no additional text or explanation.

Response:"""
        return prompt
    
    def _parse_batch_response(self, response: str, questions_data: List[Dict]) -> Dict[int, Dict[str, float]]:
        try:
            response = response.strip()
            
            if response.startswith("```json"):
                response = response[7:-3]
            elif response.startswith("```"):
                response = response[3:-3]
            
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            json_str = response[start_idx:end_idx]
            
            raw_mappings = json.loads(json_str)
            available_metric_ids = [mid.value for mid in MetricId]
            
            validated_mappings = {}
            
            for q_data in questions_data:
                question_id = q_data['id']
                question_id_str = str(question_id)
                
                if question_id_str in raw_mappings:
                    metric_weights = raw_mappings[question_id_str]
                    
                    if isinstance(metric_weights, dict):
                        valid_metric_weights = {}
                        for metric_id, weight in metric_weights.items():
                            if metric_id in available_metric_ids:
                                weight = max(0.1, min(1.0, float(weight)))
                                valid_metric_weights[metric_id] = weight
                            else:
                                self.logger.warning(f"Invalid metric ID for question {question_id}: {metric_id}")
                        
                        validated_mappings[question_id] = valid_metric_weights
                    else:
                        validated_mappings[question_id] = {}
                else:
                    validated_mappings[question_id] = {}
            
            return validated_mappings
            
        except (json.JSONDecodeError, ValueError) as e:
            self.logger.error(f"Failed to parse response: {e}")
            return {}
    
    def _apply_mappings_to_config(self, config, mappings: Dict[int, Dict[str, float]]) -> None:
        question_id = 0
        
        for goal in config.goals:
            for question in goal.questions:
                if not question.metrics:
                    question.metrics = mappings.get(question_id, {})
                    
                    question_id += 1