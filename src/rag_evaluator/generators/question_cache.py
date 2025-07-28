import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional
import logging

from rag_evaluator.config import get_config
from rag_evaluator.framework.evaluation_data import TestCase


class QuestionCache:
    def __init__(self):
        self.cache_dir = Path(get_config().question_cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger("rag_evaluator.question_cache")
    
    def _get_cache_filename(self, generation_config: Dict) -> str:
        config_str = json.dumps(generation_config, sort_keys=True)
        config_hash = hashlib.md5(config_str.encode()).hexdigest()[:12]
        
        index_name = get_config().get_pinecone_config().get('index_name', 'default')
        filename = f"{index_name}_{config_hash}.json"
        
        return filename
    
    def get_cached_questions(self, generation_config: Dict) -> Optional[List[TestCase]]:
        filename = self._get_cache_filename(generation_config)
        cache_file = self.cache_dir / filename
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                
                test_cases = []
                for item in data:
                    test_case = TestCase(
                        question=item['question'],
                        ground_truth=item['ground_truth'],
                        question_type=item.get('question_type', 'simple'),
                        entities=item.get('entities', [])
                    )
                    test_cases.append(test_case)
                
                self.logger.info(f"Loaded {len(test_cases)} cached test cases from {filename}")
                return test_cases
                
            except Exception as e:
                self.logger.error(f"Failed to load cached questions: {e}")
                return None
        return None
    
    def cache_questions(self, test_cases: List[TestCase], generation_config: Dict) -> None:
        filename = self._get_cache_filename(generation_config)
        cache_file = self.cache_dir / filename
        
        try:
            data = []
            for tc in test_cases:
                data.append({
                    'question': tc.question,
                    'ground_truth': tc.ground_truth,
                    'question_type': tc.question_type,
                    'entities': tc.entities
                })
            
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            self.logger.info(f"Cached {len(test_cases)} test cases to {filename}")
            
        except Exception as e:
            self.logger.error(f"Failed to cache questions: {e}")
    
    def clear_cache(self) -> None:
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
        self.logger.info("Cleared question cache")