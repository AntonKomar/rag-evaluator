from typing import List, Any
from dataclasses import dataclass

from rag_evaluator.constants import QuestionType


@dataclass
class TestCase:
    question: str
    ground_truth: str
    question_type: str = QuestionType.SIMPLE
    entities: List[str] = None
    
    def __post_init__(self):
        if self.entities is None:
            self.entities = []


@dataclass
class TestCaseResult:
    query: str
    generated_answer: str
    retrieved_documents: List[Any]
    ground_truth: str
    entities: List[str] = None
    question_type: str = QuestionType.SIMPLE
    
    def __post_init__(self):
        if self.entities is None:
            self.entities = []
    

@dataclass
class EvaluationData:
    test_case_results: List[TestCaseResult]