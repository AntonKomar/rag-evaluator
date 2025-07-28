import re
import logging
import numpy as np

from rag_evaluator.config import get_config
from rag_evaluator.constants import QuestionType

from ..framework.evaluation_data import EvaluationData
from ..clients.gemini_client import get_gemini_client


class SystemMetrics:
    def __init__(self):
        self.model = get_gemini_client()
        self.logger = logging.getLogger("rag_evaluator.system_metrics")
    
    def _evaluate_with_llm(self, prompt: str, default_score: float = 0.5) -> float:
        try:
            response = self.model.generate_for_metrics(prompt)
            score = float(re.search(r'(\d+(?:\.\d+)?)', response).group(1))
            return min(max(score / 10.0, 0.0), 1.0)
        except Exception as e:
            self.logger.warning(f"LLM evaluation failed: {e}")
            return default_score


def answer_correctness(evaluation_data: EvaluationData)  -> float | dict:
    evaluator = SystemMetrics()
    
    total_scores = []
    detailed_results = []

    for result in evaluation_data.test_case_results:
        ground_truth = result.ground_truth
        if not ground_truth or not result.generated_answer:
            continue
        
        prompt = f"""Rate answer correctness against ground truth (0-10).

Query: {result.query}
Ground Truth: {ground_truth}
Generated Answer: {result.generated_answer}

Consider:
- Factual accuracy
- Completeness of important points
- No contradictions

Output only the numeric score (0-10).

Score (0-10):"""
        
        score = evaluator._evaluate_with_llm(prompt)
        total_scores.append(score)

        if get_config().return_detailed_results:
            detailed_results.append({
                "query": result.query,
                "generated_answer": result.generated_answer,
                "question_type": result.question_type,
                "score": score,
            })
    
    overall_score = np.mean(total_scores) if total_scores else 0.0
    
    if get_config().return_detailed_results:
        return {
            "score": overall_score,
            "individual_scores": detailed_results
        }
    
    return overall_score


def multi_hop_reasoning_score(evaluation_data: EvaluationData) -> float | dict:
    evaluator = SystemMetrics()
    total_scores = []
    detailed_results = []

    for result in evaluation_data.test_case_results:
        if result.question_type != QuestionType.COMPLEX:
            continue
        if not result.generated_answer or len(result.retrieved_documents) < 2:
            continue

        prompt = f"""Rate multi-hop reasoning quality (0-10).

Query: {result.query}
Answer: {result.generated_answer}
Documents Used: {len(result.retrieved_documents)}

Rate how well the answer:
1. Connects information across multiple documents (cross-references sources).
2. Presents a clear chain of reasoning.
3. Synthesizes information from the sources effectively.

Output only the numeric score (0-10).

Score (0-10):"""
        score = evaluator._evaluate_with_llm(prompt)
        total_scores.append(score)

        if get_config().return_detailed_results:
            detailed_results.append({
                "query": result.query,
                "generated_answer": result.generated_answer,
                "question_type": result.question_type,
                "score": score,
            })

    if not total_scores:
        return None

    overall_score = np.mean(total_scores) if total_scores else 0.0

    if get_config().return_detailed_results:
        return {
            "score": overall_score,
            "individual_scores": detailed_results
        }
    return overall_score


def context_utilization_rate(evaluation_data: EvaluationData)  -> float | dict:
    evaluator = SystemMetrics()
    
    total_scores = []
    detailed_results = []

    for result in evaluation_data.test_case_results:
        if not result.retrieved_documents or not result.generated_answer:
            continue
        
        contexts = [
            doc.get_content() if hasattr(doc, "get_content") else str(doc)
            for doc in result.retrieved_documents[:5] 
        ]
        
        prompt = f"""Rate context utilization effectiveness (0-10).

Query: {result.query}
Answer: {result.generated_answer}
Available Contexts: {contexts}

Rate how well the answer:
1. Uses information from the provided contexts
2. Doesn't ignore relevant available information
3. Synthesizes context information effectively

Output only the numeric score (0-10).

Score (0-10):"""
        
        score = evaluator._evaluate_with_llm(prompt)
        total_scores.append(score)

        if get_config().return_detailed_results:
            detailed_results.append({
                "query": result.query,
                "generated_answer": result.generated_answer,
                "question_type": result.question_type,
                "score": score,
            })
    
    overall_score = np.mean(total_scores) if total_scores else 0.0

    if get_config().return_detailed_results:
        return {
            "score": overall_score,
            "individual_scores": detailed_results
        }
    
    return overall_score