from dataclasses import dataclass
import logging
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv
from pydantic import BaseModel, Field


class QuestionConfig(BaseModel):
    text: str
    weight: float = 1.0
    metrics: Dict[str, float] = Field(default_factory=dict)


class GoalConfig(BaseModel):
    name: str
    weight: float = 1.0
    questions: List[QuestionConfig]


class EvaluationConfig(BaseModel):
    goals: List[GoalConfig]
    test_case_generation: Dict[str, Any] = Field(default_factory=dict)
    
    @classmethod
    def from_yaml(cls, yaml_path: str) -> "EvaluationConfig":
        import yaml
        with open(yaml_path, "r") as f:
            config_dict = yaml.safe_load(f)
        return cls(**config_dict)


@dataclass
class Config:
    pinecone_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    voyage_api_key: Optional[str] = None
    voyage_model: str = 'voyage-3-large'
    gemini_model: str = 'gemini-2.5-flash'
    bertscore_model: str = 'microsoft/deberta-v3-large'
    question_cache_dir: str = 'questions'
    output_dir: str = 'evaluation_results'
    pinecone_index_name: Optional[str] = None
    return_detailed_results: bool = False
    use_metric_mapper: bool = False
    tokenizers_parallelism: bool = False
    
    def validate(self) -> None:
        errors = []
        
        if not self.pinecone_api_key:
            errors.append("PINECONE_API_KEY is required")
        
        if not self.gemini_model:
            errors.append("GEMINI_MODEL is required")

        if not self.gemini_api_key:
            errors.append("GEMINI_API_KEY is required")
            
        if not self.pinecone_index_name:
            errors.append("PINECONE_INDEX_NAME is required")
        
        if errors:
            raise ValueError(f"Missing required configuration: {', '.join(errors)}")
    
    def get_model_config(self) -> Dict[str, Any]:
        return {
            "voyage_api_key": self.voyage_api_key,
            "bertscore_model": self.bertscore_model,
        }
    
    def get_pinecone_config(self) -> Dict[str, Optional[str]]:
        return {
            "api_key": self.pinecone_api_key,
            "index_name": self.pinecone_index_name
        }
    
    def get_gemini_config(self) -> Dict[str, Optional[str]]:
        return {
            "api_key": self.gemini_api_key,
            "model": self.gemini_model
        }


class ConfigLoader:    
    def __init__(self, env_path: Optional[Path] = None):
        self.env_path = env_path or Path(__file__).parent.parent.parent / '.env'
        self.logger = logging.getLogger("rag_evaluator.config")
    
    @staticmethod
    def _get_bool_env(key: str, default: bool = False) -> bool:
        value = os.getenv(key)
        if value is None:
            return default
        return value.lower() in ('true', '1', 't', 'yes', 'on')
    
    def load(self) -> Config:
        load_dotenv(self.env_path, override=True)
        
        self.logger.info(f"Loading environment variables from {self.env_path}")
        self.logger.info(f"Environment file exists: {self.env_path.exists()}")
        
        config = Config(
            pinecone_api_key=os.getenv('PINECONE_API_KEY'),
            gemini_api_key=os.getenv('GEMINI_API_KEY'),
            voyage_api_key=os.getenv('VOYAGE_API_KEY'),
            voyage_model=os.getenv('VOYAGE_MODEL', 'voyage-3-large'),
            gemini_model=os.getenv('GEMINI_MODEL', 'gemini-2.5-flash'),
            bertscore_model=os.getenv('BERTSCORE_MODEL', 'roberta-large'),
            question_cache_dir=os.getenv('QUESTION_CACHE_DIR', 'questions'),
            output_dir=os.getenv('OUTPUT_DIR', 'evaluation_results'),
            pinecone_index_name=os.getenv('PINECONE_INDEX_NAME'),
            return_detailed_results=self._get_bool_env('RETURN_DETAILED_RESULTS'),
            use_metric_mapper=self._get_bool_env('USE_METRIC_MAPPER'),
            tokenizers_parallelism=self._get_bool_env('TOKENIZERS_PARALLELISM', False)
        )

        config.validate()
        
        self.logger.info("Environment variables loaded successfully")
        return config


_config: Optional[Config] = None


def get_config() -> Config:
    global _config
    if _config is None:
        loader = ConfigLoader()
        _config = loader.load()
    return _config