import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path)) 

from rag_evaluator.config import get_config
from rag_evaluator.generators.question_generator import QuestionGenerator
from rag_evaluator.constants import QuestionType
import logging

logging.basicConfig(level=logging.DEBUG)

generator = QuestionGenerator()

pinecone_config = {
    'api_key': get_config().pinecone_api_key,
    'index_name': get_config().pinecone_index_name
}

question_types = [QuestionType.SIMPLE, QuestionType.COMPLEX]
counts_per_type = {
    QuestionType.SIMPLE: 2,
    QuestionType.COMPLEX: 1
}

test_cases = generator.generate_questions(
    pinecone_config=pinecone_config,
    question_types=question_types,
    counts_per_type=counts_per_type,
    force_regenerate=True
)

print(f"\nGenerated {len(test_cases)} questions:")
for i, tc in enumerate(test_cases, 1):
    print(f"\n{i}. [{tc.question_type.upper()}]")
    print(f"   Q: {tc.question}")
    print(f"   A: {tc.ground_truth}")
    if tc.entities:
        print(f"   Entities: {', '.join(tc.entities)}")