import logging
from typing import List, Optional
import numpy as np
import voyageai

from rag_evaluator.config import get_config

_voyage_client = None

def get_voyage_client():
    global _voyage_client
    if _voyage_client is None:
        config = get_config()
        _voyage_client = voyageai.Client(api_key=config.voyage_api_key)
        logging.getLogger("rag_evaluator.embeddings").info(
            f"Initialized Voyage AI client with model: {config.voyage_model}"
        )
    return _voyage_client

def embed_texts(texts: List[str], batch_size: int = 128) -> np.ndarray:
    client = get_voyage_client()
    config = get_config()
    
    all_embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        try:
            response = client.embed(batch, model=config.voyage_model)
            all_embeddings.extend(response.embeddings)
        except Exception as e:
            logging.getLogger("rag_evaluator.embeddings").error(
                f"Failed to embed batch {i//batch_size}: {e}"
            )
            raise
    
    return np.array(all_embeddings)