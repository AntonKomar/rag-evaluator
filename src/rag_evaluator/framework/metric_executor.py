import logging

from ..constants import MetricId
from ..metrics import retrieval_metrics, generation_metrics, system_metrics
from .evaluation_data import EvaluationData


class MetricExecutor:
    
    def __init__(self):
        self.logger = logging.getLogger("rag_evaluator.metric_executor")

    def execute_metric(self, metric_id: str, evaluation_data: EvaluationData)  -> float | dict:
        try:
            metric_enum = MetricId(metric_id)
        except ValueError:
            self.logger.error(f"Unknown metric ID: {metric_id}")
            return 0.0
        
        metric_functions = {
            MetricId.CONTEXT_PRECISION: lambda: retrieval_metrics.context_precision(evaluation_data),
            MetricId.CONTEXT_RECALL: lambda: retrieval_metrics.context_recall(evaluation_data),
            MetricId.CONTEXT_RELEVANCE: lambda: retrieval_metrics.context_relevance(evaluation_data),
            MetricId.CONTEXT_ENTITIES_RECALL: lambda: retrieval_metrics.context_entities_recall(evaluation_data),
            MetricId.FAITHFULNESS: lambda: generation_metrics.faithfulness(evaluation_data),
            MetricId.FACTUAL_CONSISTENCY: lambda: generation_metrics.factual_consistency(evaluation_data),
            MetricId.ANSWER_RELEVANCE: lambda: generation_metrics.answer_relevance(evaluation_data),
            MetricId.BERTSCORE: lambda: generation_metrics.bertscore(evaluation_data),
            MetricId.ANSWER_CORRECTNESS: lambda: system_metrics.answer_correctness(evaluation_data),
            MetricId.SEMANTIC_DIVERSITY: lambda: retrieval_metrics.semantic_diversity(evaluation_data),
            MetricId.ATTRIBUTION_SCORE: lambda: generation_metrics.attribution_score(evaluation_data),
            MetricId.ANSWER_COMPLETENESS: lambda: generation_metrics.answer_completeness(evaluation_data),
            MetricId.SELF_CONSISTENCY: lambda: generation_metrics.self_consistency_score(evaluation_data),
            MetricId.MULTI_HOP_REASONING: lambda: system_metrics.multi_hop_reasoning_score(evaluation_data),
            MetricId.CONTEXT_UTILIZATION: lambda: system_metrics.context_utilization_rate(evaluation_data)
        }
        
        try:
            metric_function = metric_functions.get(metric_enum)
            if metric_function:
                result = metric_function()
                
                return result
            else:
                self.logger.error(f"No function defined for metric: {metric_enum}")
                return 0.0
        except Exception as e:
            self.logger.error(f"Failed to execute metric {metric_id}: {e}")
            return 0.0