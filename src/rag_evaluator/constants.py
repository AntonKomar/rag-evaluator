from enum import Enum
from typing import Dict, List
from dataclasses import dataclass


class QuestionType(Enum):
    SIMPLE = "simple"
    COMPLEX = "complex" 
    DISTRACTING = "distracting"
    SITUATIONAL = "situational"
    DOUBLE = "double"
    CONVERSATIONAL = "conversational"


class MetricId(Enum):
    CONTEXT_PRECISION = "context_precision"
    CONTEXT_RECALL = "context_recall"
    CONTEXT_RELEVANCE = "context_relevance" 
    CONTEXT_ENTITIES_RECALL = "context_entities_recall"
    FAITHFULNESS = "faithfulness"
    FACTUAL_CONSISTENCY = "factual_consistency"
    ANSWER_RELEVANCE = "answer_relevance"
    BERTSCORE = "bertscore"
    ANSWER_CORRECTNESS = "answer_correctness"
    SEMANTIC_DIVERSITY = "semantic_diversity"
    ATTRIBUTION_SCORE = "attribution_score"
    ANSWER_COMPLETENESS = "answer_completeness"
    SELF_CONSISTENCY = "self_consistency"
    MULTI_HOP_REASONING = "multi_hop_reasoning"
    CONTEXT_UTILIZATION = "context_utilization"


@dataclass
class MetricInfo:
    name: str
    description: str
    use_cases: List[str]


METRIC_INFO: Dict[MetricId, MetricInfo] = {
    MetricId.CONTEXT_PRECISION: MetricInfo(
        name="Context Precision",
        description="Measures how relevant retrieved documents are to the query",
        use_cases=["document relevance", "retrieval quality", "precision of search results"]
    ),
    
    MetricId.CONTEXT_RECALL: MetricInfo(
        name="Context Recall",
        description="Measures completeness of retrieved relevant information", 
        use_cases=["completeness of retrieval", "information coverage", "missing documents"]
    ),
    
    MetricId.CONTEXT_RELEVANCE: MetricInfo(
        name="Context Relevance",
        description="LLM-based evaluation of document relevance to query",
        use_cases=["semantic relevance", "contextual appropriateness", "query understanding"]
    ),
    
    MetricId.CONTEXT_ENTITIES_RECALL: MetricInfo(
        name="Context Entities Recall", 
        description="Measures recall of important entities in retrieved documents",
        use_cases=["entity coverage", "important information recall", "named entity retrieval"]
    ),
    
    MetricId.FAITHFULNESS: MetricInfo(
        name="Faithfulness",
        description="Measures if generated claims are supported by retrieved context",
        use_cases=["factual accuracy", "grounding in context", "avoiding fabrication", "claim verification"]
    ),
    
    MetricId.FACTUAL_CONSISTENCY: MetricInfo(
        name="Factual Consistency", 
        description="Detects hallucinations and measures factual consistency",
        use_cases=["hallucination detection", "factual correctness", "avoiding made-up information"]
    ),
    
    MetricId.ANSWER_RELEVANCE: MetricInfo(
        name="Answer Relevance",
        description="Evaluates how well the answer addresses the user's query",
        use_cases=["query addressing", "response appropriateness", "answer completeness"]
    ),
    
    MetricId.BERTSCORE: MetricInfo(
        name="BERTScore",
        description="Semantic similarity between generated answer and context", 
        use_cases=["semantic similarity", "content alignment", "contextual consistency"]
    ),
    
    MetricId.ANSWER_CORRECTNESS: MetricInfo(
        name="Answer Correctness", 
        description="Compares generated answers against ground truth",
        use_cases=["accuracy against ground truth", "correctness verification", "benchmark comparison"]
    ),
    
    MetricId.SEMANTIC_DIVERSITY: MetricInfo(
        name="Semantic Diversity",
        description="Measures diversity of retrieved documents to avoid redundancy",
        use_cases=["result diversity", "avoiding redundancy", "multiple perspectives"]
    ),
    
    MetricId.ATTRIBUTION_SCORE: MetricInfo(
        name="Attribution Score",
        description="Measures how well answers attribute information to sources",
        use_cases=["source attribution", "verifiability", "transparency", "citation quality"]
    ),
    
    MetricId.ANSWER_COMPLETENESS: MetricInfo(
        name="Answer Completeness",
        description="Measures how completely the answer addresses all aspects of the query",
        use_cases=["comprehensive answers", "multi-aspect coverage", "thoroughness"]
    ),
    
    MetricId.SELF_CONSISTENCY: MetricInfo(
        name="Self-Consistency",
        description="Measures internal consistency of generated answers",
        use_cases=["logical consistency", "avoiding contradictions", "coherent reasoning"]
    ),
    
    MetricId.MULTI_HOP_REASONING: MetricInfo(
        name="Multi-Hop Reasoning",
        description="Evaluates ability to connect information across multiple documents",
        use_cases=["complex reasoning", "information synthesis", "connecting facts"]
    ),
    
    MetricId.CONTEXT_UTILIZATION: MetricInfo(
        name="Context Utilization",
        description="Measures how effectively the system uses retrieved context",
        use_cases=["context usage", "information extraction", "retrieval effectiveness"]
    )
}