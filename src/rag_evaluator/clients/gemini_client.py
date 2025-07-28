import logging
from typing import Optional, Dict

from rag_evaluator.config import get_config


class GeminiClient:
    
    def __init__(self):
        self.logger = logging.getLogger("rag_evaluator.gemini_client")
        self.config = get_config().get_gemini_config()

        self._init_gemini()
        self._setup_generation_configs()

    
    def _init_gemini(self):
        try:
            import google.generativeai as genai
            
            genai.configure(api_key=self.config['api_key'])
            
            self.model = genai.GenerativeModel(self.config['model'])
            
            self.logger.info("Successfully initialized Gemini API client")
            
        except ImportError:
            raise ImportError(
                "google-generativeai library is required. "
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize Gemini API: {e}")
            raise RuntimeError(f"Failed to initialize Gemini API: {e}")
    
    def _setup_generation_configs(self):
        self.default_generation_config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": 20000,
        }
        
        self.metric_mapping_config = {
            "temperature": 0.1,
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 20000,
        }
    
    def generate(self, prompt: str, generation_config: Optional[Dict] = None) -> str:
        self.logger.debug(f"Generating content with prompt: {prompt}")
        config = generation_config or self.default_generation_config
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=config
            )

            self.logger.debug(f"Gemini response: {response}")
            
            return response.text.strip()
            
        except Exception as e:
            self.logger.error(f"Gemini API error: {str(e)}")
            raise RuntimeError(f"Gemini API error: {str(e)}")
    
    def generate_for_questions(self, prompt: str) -> str:
        return self.generate(prompt)
    
    def generate_for_metrics(self, prompt: str) -> str:
        return self.generate(prompt, self.metric_mapping_config)


_gemini_client_instance = None


def create_gemini_client() -> GeminiClient:
    global _gemini_client_instance
    if _gemini_client_instance is not None:
        raise RuntimeError("Gemini client instance already exists")
    
    _gemini_client_instance = GeminiClient()
    
    return _gemini_client_instance


def get_gemini_client() -> Optional[GeminiClient]:
    global _gemini_client_instance
    if _gemini_client_instance is None:
        create_gemini_client()
    return _gemini_client_instance