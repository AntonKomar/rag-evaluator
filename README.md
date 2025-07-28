# RAG Evaluator: A GQM-based Framework for RAG System Evaluation

# Check Thesis Documentation
```
-> /docs/Master_Thesis.pdf
```

# Quick Setup
Prerequisites
- Python 3.8+
- Node.js 16+ (for dashboard)

## Clone and Install

```bash
# Clone the repository
git clone https://github.com/yourusername/rag-evaluator.git
cd rag-evaluator

# Create a virtual environment
python -m venv venv
source venv/bin/activate

# Install the package in development mode
pip install -e .

or 

# Install with all extras including dev tools
pip install -e ".[all]"
```

## Environment Configuration
Create .env file in project root:

```bash
# Required
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=your_index_name
GEMINI_API_KEY=your_gemini_api_key

# Optional
VOYAGE_API_KEY=your_voyage_api_key
HUGGINGFACE_API_KEY=your_hf_api_key

# Model Configuration
GEMINI_MODEL=gemini-2.5-flash
BERTSCORE_MODEL=microsoft/deberta-v3-large
RETURN_DETAILED_RESULTS=true
```

## Setup Dahboard UI
```bash
cd dashboard

npm install

# Start development server
npm run dev

# Or run both backend and frontend
python run.py
```


# Running Experiments

## RAG System Evaluation
```bash
python ./examples/rag_system_evaluation.py
```

Configure your evaluation by modifying the script:
```bash
MODEL_NAME = "llama3.2:3b"
embed_model_id = "sentence-transformers/all-MiniLM-L6-v2"
temperature = 0.1
K_DOCS = 3
```


## Question Generation
```bash
python ./examples/question_generation.py
```

Customize question generation:
```bash
question_types = [QuestionType.SIMPLE, QuestionType.COMPLEX]
counts_per_type = {
    QuestionType.SIMPLE: 10,
    QuestionType.COMPLEX: 5,
    QuestionType.CONVERSATIONAL: 5
}

# Force regenerate (ignore cache)
test_cases = generator.generate_questions(
    pinecone_config=pinecone_config,
    question_types=question_types,
    counts_per_type=counts_per_type,
    force_regenerate=True
)
```

Edit evaluation_config.yaml to customize goals and metrics