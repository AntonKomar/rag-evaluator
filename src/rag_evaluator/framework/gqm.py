import gc
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging
import json
import numpy as np
import torch

from rag_evaluator.adapters.langchain import LangChainRAGAdapter

from ..config import get_config, GoalConfig, QuestionConfig, EvaluationConfig
from .llm_metric_mapper import LLMMetricMapper
from .metric_executor import MetricExecutor
from .evaluation_data import EvaluationData, TestCase, TestCaseResult


@dataclass
class MetricResult:
    metric_id: str
    value: float
    weight: float = 1.0

    individual_scores: Optional[List[Dict[str, Any]]] = None
    
    @property
    def has_details(self) -> bool:
        return self.individual_scores is not None

@dataclass
class QuestionResult:
    question_text: str
    metrics: List[MetricResult]
    weight: float = 1.0
    
    @property
    def score(self) -> float:
        if not self.metrics:
            return 0.0
        
        total_weight = sum(metric.weight for metric in self.metrics)
        weighted_sum = sum(metric.value * metric.weight for metric in self.metrics)
        return weighted_sum / total_weight


@dataclass
class GoalResult:
    goal_name: str
    questions: List[QuestionResult]
    weight: float = 1.0
    
    @property
    def score(self) -> float:
        if not self.questions:
            return 0.0
        
        total_weight = sum(question.weight for question in self.questions)
        weighted_sum = sum(question.score * question.weight for question in self.questions)
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0


@dataclass
class EvaluationResult:
    goals: List[GoalResult]
    
    @property
    def score(self) -> float:
        if not self.goals:
            return 0.0
        
        total_weight = sum(goal.weight for goal in self.goals)
        weighted_sum = sum(goal.score * goal.weight for goal in self.goals)
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_score": self.score,
            "goals": [
                {
                    "name": goal.goal_name,
                    "score": goal.score,
                    "weight": goal.weight,
                    "questions": [
                        {
                            "text": question.question_text,
                            "score": question.score,
                            "weight": question.weight,
                            "metrics": [
                                {
                                    "id": metric.metric_id,
                                    "value": metric.value,
                                    "weight": metric.weight,
                                    **({"individual_scores": metric.individual_scores} 
                                        if metric.has_details else {})
                                }
                                for metric in question.metrics
                            ]
                        }
                        for question in goal.questions
                    ]
                }
                for goal in self.goals
            ]
        }
    
    def save(self, filepath: str) -> None:
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2, cls=NumpyEncoder)


@dataclass
class CachedMetricResult:
    metric_id: str
    value: float
    individual_scores: Optional[List[Dict[str, Any]]] = None


class GQMFramework:    
    def __init__(self, config: EvaluationConfig):
        self.config = config
        self.logger = logging.getLogger("rag_evaluator.gqm")
        # self.metric_mapper = LLMMetricMapper()
        self.metric_executor = MetricExecutor()

        self._metric_cache: Dict[str, CachedMetricResult] = {}
        
        # Not needed - managed manually by providing metrics in config
        # if self._needs_metric_mapping():
        #     self.logger.info("Mapping questions to metrics using LLM")
        #     self.metric_mapper.map_all_questions(self.config)
    
    def _needs_metric_mapping(self) -> bool:
        if not get_config().use_metric_mapper:
            self.logger.info("Metric mapping is disabled via environment configuration")
            return False
        
        for goal in self.config.goals:
            for question in goal.questions:
                if not question.metrics:
                    return True
        return False
    
    def _test_rag_system(self, test_cases: List[TestCase], rag_system: LangChainRAGAdapter) -> EvaluationData:
        self.logger.info(f"Running {len(test_cases)} test cases through RAG system")
        
        test_case_results = []
        
        for test_case in test_cases:
            try:
                rag_result = rag_system.query(test_case.question)
                
                test_case_results.append(TestCaseResult(
                    query=test_case.question,
                    generated_answer=rag_result.answer,
                    retrieved_documents=rag_result.retrieved_documents,
                    ground_truth=test_case.ground_truth,
                    entities=test_case.entities,
                    question_type=test_case.question_type
                ))
                
            except Exception as e:
                self.logger.error(f"Failed to process test case '{test_case.question}': {e}")
                test_case_results.append(TestCaseResult(
                    query=test_case.question,
                    generated_answer="",
                    retrieved_documents=[],
                    ground_truth=test_case.ground_truth,
                    entities=test_case.entities,
                    question_type=test_case.question_type
                ))
        
        return EvaluationData(test_case_results=test_case_results)
    
    def _get_or_execute_metric(self, metric_id: str, weight: float, evaluation_data: EvaluationData) -> MetricResult:
        if metric_id in self._metric_cache:
            cached_result = self._metric_cache[metric_id]

            self.logger.info(f"Using cached result for metric: {metric_id}")
            
            return MetricResult(
                metric_id=metric_id,
                value=cached_result.value,
                weight=weight,
                individual_scores=cached_result.individual_scores
            )
        
        self.logger.info(f"Executing metric: {metric_id}")
        try:
            value = self.metric_executor.execute_metric(metric_id, evaluation_data)

            if value is None:
                return None
        
            self.logger.info(f"Metric {metric_id} executed with value: {value}")
            
            if isinstance(value, dict) and get_config().return_detailed_results:
                score = value.get("score", 0.0)
                individual_scores = value.get("individual_scores")
            else:
                score = float(value)
                individual_scores = None
            
            cached_result = CachedMetricResult(
                metric_id=metric_id,
                value=score,
                individual_scores=individual_scores
            )
            self._metric_cache[metric_id] = cached_result
            
            return MetricResult(
                metric_id=metric_id,
                value=score,
                weight=weight,
                individual_scores=individual_scores
            )
            
        except Exception as e:
            self.logger.error(f"Failed to execute metric {metric_id}: {e}")
            raise
    
    def evaluate_question(self, question_config: QuestionConfig, evaluation_data: EvaluationData) -> QuestionResult:
        self.logger.info(f"Evaluating question: {question_config.text}")
        
        metric_results = []

        for metric_id, weight in question_config.metrics.items():
            metric_result = self._get_or_execute_metric(metric_id, weight, evaluation_data)
            if metric_result is not None:
                metric_results.append(metric_result)
        
        return QuestionResult(
            question_text=question_config.text,
            metrics=metric_results,
            weight=question_config.weight
        )
    
    def evaluate_goal(self, goal_config: GoalConfig, evaluation_data: EvaluationData) -> GoalResult:
        self.logger.info(f"Evaluating goal: {goal_config.name}")
        
        question_results = []
        for question_config in goal_config.questions:
            result = self.evaluate_question(question_config, evaluation_data)
            question_results.append(result)
        
        return GoalResult(
            goal_name=goal_config.name,
            questions=question_results,
            weight=goal_config.weight
        )
    
    def evaluate(self, test_cases: List[Dict], rag_system: Any) -> EvaluationResult:
        self.logger.info(f"Starting evaluation with {len(self.config.goals)} goals")
        
        evaluation_data = self._test_rag_system(test_cases, rag_system)
        
        self.logger.info("Unloading RAG system to free memory...")
        self._unload_rag_system(rag_system)
        time.sleep(5)

        goal_results = []
        for goal_config in self.config.goals:
            result = self.evaluate_goal(goal_config, evaluation_data)
            goal_results.append(result)
        
        return EvaluationResult(
            goals=goal_results
        )
    
    def _unload_rag_system(self, rag_system: Any) -> None:
        try:
            if hasattr(rag_system, 'rag_pipeline'):
                if hasattr(rag_system.rag_pipeline, 'llm'):
                    rag_system.rag_pipeline.llm = None
                if hasattr(rag_system.rag_pipeline, 'retriever'):
                    rag_system.rag_pipeline.retriever = None
                rag_system.rag_pipeline = None
            
            if hasattr(rag_system, 'retriever'):
                if hasattr(rag_system.retriever, 'vectorstore'):
                    rag_system.retriever.vectorstore = None
                rag_system.retriever = None
            
            rag_system = None
            
            gc.collect()
            
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            elif hasattr(torch, 'mps') and torch.backends.mps.is_available():
                torch.mps.empty_cache()
            
            self.logger.info("RAG system unloaded successfully")
            
        except Exception as e:
            self.logger.warning(f"Error while unloading RAG system: {e}")
    

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif hasattr(obj, 'item'):
            try:
                return obj.item()
            except:
                pass
        return super().default(obj)