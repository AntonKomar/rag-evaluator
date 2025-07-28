from typing import Dict, List, Optional
from pathlib import Path
import subprocess, sys, time, webbrowser, logging

from rag_evaluator.adapters.langchain import LangChainRAGAdapter
from rag_evaluator.framework.evaluation_data import TestCase

from ..config import get_config, EvaluationConfig
from ..constants import QuestionType
from ..clients.gemini_client import create_gemini_client
from .gqm import GQMFramework, EvaluationResult
from ..generators.question_generator import QuestionGenerator


class EvaluationPipeline:
    def __init__(self, config: EvaluationConfig):
        self.config = config
        self.pinecone_config = get_config().get_pinecone_config()
        self.logger = logging.getLogger("rag_evaluator.pipeline")
        
        create_gemini_client()
        
        self.logger.info("Initialized Gemini client")
        
        self.framework = GQMFramework(config)
        self.question_generator = QuestionGenerator()
    

    def generate_test_cases(self, force_regenerate: bool = False) -> List[TestCase]:        
        self.logger.info("Generating test cases")
        
        question_types = []
        counts_per_type = {}
        
        for question_type_str, params in self.config.test_case_generation.items():
            try:
                question_type = QuestionType(question_type_str)
                question_types.append(question_type)
                counts_per_type[question_type] = params.get("count", 1)
            except ValueError:
                self.logger.warning(f"Unknown question type: {question_type_str}")
                continue
        
        if not question_types:
            raise ValueError("No valid question types specified in configuration")
        
        questions = self.question_generator.generate_questions(
            pinecone_config=self.pinecone_config,
            question_types=question_types,
            counts_per_type=counts_per_type,
            force_regenerate=force_regenerate
        )
        
        return questions
    

    def evaluate(self, rag_system: LangChainRAGAdapter, 
                test_cases: Optional[List[Dict]] = None,
                force_regenerate_questions: bool = False) -> EvaluationResult:
        start_time = time.time()
        self.logger.info("Starting RAG system evaluation")
        
        if test_cases is None:
            test_cases = self.generate_test_cases(force_regenerate_questions)
        
        self.logger.info(f"Using {len(test_cases)} test cases for evaluation")
        
        result = self.framework.evaluate(test_cases, rag_system)
        
        elapsed_time = time.time() - start_time
        self.logger.info(f"Evaluation completed in {elapsed_time:.2f} seconds")
        self.logger.info(f"Overall score: {result.score:.4f}")
        
        return result
    

    def save_results(self, result: EvaluationResult, output_dir: Optional[str] = None) -> None:
        output_dir = output_dir or get_config().output_dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        result_file_name = f"evaluation_result_{time.strftime('%Y%m%d_%H%M%S')}.json"
        result_path = Path(output_dir) / result_file_name
        result.save(str(result_path))
        self.logger.info(f"Saved evaluation results to {result_path}")
    
    
    def clear_question_cache(self) -> None:
        self.question_generator.cache.clear_cache()
        self.logger.info("Cleared question cache")


    def launch_dashboard(self, open_browser: bool = True) -> bool:
        logger = logging.getLogger("rag_evaluator.dashboard")
        dashboard_dir = Path(__file__).resolve().parents[3] / "dashboard"
        runner_path = dashboard_dir / "run.py"

        if not runner_path.exists():
            logger.error("Dashboard runner not found at %s", runner_path)
            return False

        try:
            self._dashboard_proc = subprocess.Popen(
                [sys.executable, str(runner_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )
            logger.info("Dashboard servers starting...")
            time.sleep(5)

            if open_browser:
                webbrowser.open("http://localhost:5173")
                logger.info("Opened dashboard in browser")

            return True
        except Exception as exc:
            logger.exception("Failed to launch dashboard: %s", exc)
            return False