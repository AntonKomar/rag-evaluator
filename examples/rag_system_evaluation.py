from datetime import datetime
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path)) 

import os
import time
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
from langchain.chains import RetrievalQA
import torch
from huggingface_hub import login
from langchain_ollama import OllamaLLM

from rag_evaluator.adapters.langchain import LangChainRAGAdapter
from rag_evaluator.config import EvaluationConfig
from rag_evaluator.framework.pipeline import EvaluationPipeline
import logging


device = 'cpu'
if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
    device = 'mps'
    torch.backends.mps.fallback_to_cpu_kernels_on_unsupported_ops = True

# Setup constants

# 1 Experiment
# MODEL_NAME = "phi4-mini"
# embed_model_id = "BAAI/bge-small-en-v1.5"
# temperature = 0.1
# K_DOCS = 3

# 2 Experiment
# MODEL_NAME = "llama3.2:3b"
# embed_model_id = "sentence-transformers/all-MiniLM-L6-v2"
# temperature = 0.1
# K_DOCS = 3

# 3 Experiment
MODEL_NAME = "llama2:7b"
embed_model_id = "sentence-transformers/all-MiniLM-L12-v2"
temperature = 0.1
K_DOCS = 3



OLLAMA_BASE_URL = "http://localhost:11434"


def setup_logging():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"evaluation_log_{timestamp}.log"
    
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_filepath = log_dir / log_filename
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filepath),
            logging.StreamHandler()
        ]
    )
    
    logging.info(f"Evaluation session started. Logs will be saved to: {log_filepath}")

    return log_filepath

def setup_embeddings():
    print("Setting up embeddings model...")
    embed_model = HuggingFaceEmbeddings(
        model_name=embed_model_id,
        model_kwargs={'device': device},
        encode_kwargs={'device': device, 'batch_size': 8}
    )
    print("Embeddings model setup complete.")
    return embed_model

def setup_pinecone():
    print("Setting up Pinecone...")
    pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
    index_name = 'llama-2-7b-rag'
    index = pc.Index(index_name)
    return pc, index

def setup_ollama_llm():
    print(f"Setting up Ollama with model: {MODEL_NAME}")
    llm = OllamaLLM(
        model=MODEL_NAME,
        base_url=OLLAMA_BASE_URL,
        temperature=temperature,
        num_predict=2000,
    )
    print(f"Ollama LLM setup complete with model: {MODEL_NAME}")
    return llm

def setup_rag_pipeline(llm, index, embed_model):
    print("Setting up RAG pipeline...")
    text_field = 'text'
    vectorstore = PineconeVectorStore(
        index=index,
        embedding=embed_model,
        text_key=text_field
    )
    retriever = vectorstore.as_retriever(search_kwargs={"k": K_DOCS})
    rag_pipeline = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type='stuff',
        retriever=retriever
    )
    
    print("RAG pipeline setup complete.")
    return rag_pipeline, retriever

def main():
    setup_logging()
    
    if "HUGGINGFACE_API_KEY" in os.environ:
        try:
            login(token=os.environ["HUGGINGFACE_API_KEY"])
        except Exception as e:
            print(f"HuggingFace login failed: {e}")
    
    embed_model = setup_embeddings()
    pc, index = setup_pinecone()
    llm = setup_ollama_llm()
    rag_pipeline, retriever = setup_rag_pipeline(llm, index, embed_model)
    
    rag_adapter = LangChainRAGAdapter(
        rag_pipeline=rag_pipeline,
        retriever=retriever
    )
    
    config_path = Path(__file__).parent / "evaluation_config.yaml"
    config = EvaluationConfig.from_yaml(config_path)
    
    eval_pipeline = EvaluationPipeline(config)
    
    print("\nStarting evaluation...")
    start_time = time.time()
    
    results = eval_pipeline.evaluate(
        rag_system=rag_adapter,
        force_regenerate_questions=False
    )
    
    eval_time = time.time() - start_time
    
    eval_pipeline.save_results(results, "evaluation_results")
    
    print(f"\nEvaluation completed in {eval_time:.2f} seconds")
    print(f"Overall Score: {results.score:.4f}")
    
    print("\nGoal Scores:")
    for goal in results.goals:
        print(f"  {goal.goal_name}: {goal.score:.4f}")
    
    if eval_pipeline.launch_dashboard():
        print("Dashboard running at http://localhost:5173  (Ctrl-C to stop)")
    else:
        print("Dashboard failed to start – check logs.")
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping dashboard...")

if __name__ == "__main__":
    main()