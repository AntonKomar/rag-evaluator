# RAG Evaluator

A framework for evaluating Retrieval-Augmented Generation (RAG) systems using the Goal-Question-Metric (GQM) methodology.

## Technologies

### Backend
- **Python 3.13+** - Core framework
- **LangChain** - RAG system integration
- **Pinecone** - Vector database for document retrieval
- **Google Gemini** - LLM for question generation and evaluation
- **Voyage AI** - Text embeddings for semantic metrics
- **BERTScore** - Semantic similarity evaluation
- **spaCy** - NLP and Named Entity Recognition
- **FastAPI** - Dashboard backend API
- **Pydantic** - Data validation

### Frontend (Dashboard)
- **React 18** - UI framework
- **TypeScript** - Type-safe JavaScript
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Styling
- **Chart.js** - Data visualization
- **Axios** - HTTP client

## Quick Start

```bash
# 1. Clone and install
git clone https://github.com/yourusername/rag-evaluator.git
cd rag-evaluator
python -m venv venv && source venv/bin/activate
pip install -e .

# 2. Configure
cp .env.example .env
# Edit .env with your API keys

# 3. Run evaluation
python examples/rag_system_evaluation.py
```

## Prerequisites

- Python 3.13+
- Node.js 16+ (for dashboard)
- 8GB+ RAM recommended
- API keys for Pinecone and Google Gemini

## Installation

```bash
# Clone and navigate
git clone https://github.com/yourusername/rag-evaluator.git
cd rag-evaluator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install package
pip install -e .
```

## Configuration

### Environment Variables

Create a `.env` file in the project root (use [.env.example](.env.example) as template):

```bash
# Required API Keys
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=your_index_name
GEMINI_API_KEY=your_gemini_api_key

# Optional API Keys
VOYAGE_API_KEY=your_voyage_api_key  # For semantic diversity and answer relevance

# Model Configuration
VOYAGE_MODEL=voyage-3-large
GEMINI_MODEL=gemini-2.0-flash
BERTSCORE_MODEL=roberta-large

# Paths
QUESTION_CACHE_DIR=questions
OUTPUT_DIR=evaluation_results

# Feature Flags
RETURN_DETAILED_RESULTS=true
USE_METRIC_MAPPER=false
TOKENIZERS_PARALLELISM=false
```

### API Keys Setup

1. **Pinecone**: Sign up at [pinecone.io](https://www.pinecone.io/), create an index, and get your API key
2. **Google Gemini**: Get your API key from [Google AI Studio](https://ai.google.dev/)
3. **Voyage AI** (optional): Sign up at [voyageai.com](https://www.voyageai.com/) for embeddings

### Pinecone Index Setup

Your Pinecone index should contain your document corpus:
- Choose dimensions based on your embedding model (e.g., 384 for `all-MiniLM-L6-v2`, 1024 for `voyage-3-large`)
- Upload chunked documents with metadata
- Set `PINECONE_INDEX_NAME` to your index name

### Ollama Setup (Optional)

For local LLM inference used in the examples:

1. Install Ollama from [ollama.ai](https://ollama.ai/)
2. Pull a model:
   ```bash
   ollama pull llama3.2:3b
   # or
   ollama pull phi4-mini
   ```
3. Verify it's running:
   ```bash
   ollama serve  # Usually runs automatically
   ```

## Dashboard Setup (Optional)

The dashboard provides a web UI for visualizing evaluation results with interactive charts and comprehensive analytics.

### Features

**Visualizations & Charts:**
- **Overall Score Card** - Color-coded performance indicator
- **Goal Radar Chart** - Spider chart showing performance across evaluation goals
- **Metrics Summary** - Bar chart of all metric scores
- **Metric Distribution** - Min/Average/Max scores for each metric
- **Correlation Heatmap** - Metric correlation matrix with color coding
- **Retrieval vs Generation Scatter** - Compare retrieval and generation performance
- **Time Series Analysis** - Performance trends over time
- **Score Distribution Histogram** - Distribution of test case scores

**Analytics:**
- Overall evaluation scores with hierarchical breakdown
- Goal-level performance with weights
- Per-metric statistics (mean, min, max, std dev)
- Question type performance analysis
- Metric × Question type cross-analysis
- Individual test case results with detailed metrics

**Comparison Features:**
- Compare up to 2 evaluations side-by-side
- Component-wise comparison (Retrieval, Generation, System)
- Multi-evaluation metric heatmaps
- Side-by-side performance analysis

**Question Management:**
- Browse generated question sets
- Filter questions by type
- View ground truth answers and entities
- Question type distribution statistics

### Install Python Dependencies

```bash
pip install -r dashboard/backend/requirements.txt
```

### Run Dashboard

**Recommended: Run both backend and frontend together**
```bash
python dashboard/run.py

or

python -m dashboard
```
*Note: This automatically installs frontend dependencies on first run*

- Backend API: http://localhost:8000
- Frontend UI: http://localhost:5173
- API docs: http://localhost:8000/docs

**Alternative 1: Run separately**
```bash
# Terminal 1: Frontend
cd dashboard/frontend
npm install  # First time only
npm run dev

# Terminal 2: Backend
cd dashboard/backend
uvicorn app:app --reload --port 8000
```

### Alternative 2: From Your Evaluation Script

```python
from rag_evaluator.framework.pipeline import EvaluationPipeline
from rag_evaluator.dashboard import extend_pipeline

# Run your evaluation
eval_pipeline = EvaluationPipeline(config)
results = eval_pipeline.evaluate(rag_system)
eval_pipeline.save_results(results)

# Launch dashboard
eval_pipeline.launch_dashboard()
```

## Usage

### RAG System Evaluation

```bash
python examples/rag_system_evaluation.py
```

Configure by editing the script:
```python
MODEL_NAME = "llama3.2:3b"
embed_model_id = "sentence-transformers/all-MiniLM-L6-v2"
temperature = 0.1
K_DOCS = 3
```

### Question Generation

```bash
python examples/question_generation.py
```

Customize question generation:
```python
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

Edit [examples/evaluation_config.yaml](examples/evaluation_config.yaml) to customize evaluation goals and metrics.

## Available Metrics

The framework provides comprehensive metrics organized into three categories:

### Retrieval Metrics
- **Context Precision** - Precision of retrieved documents
- **Context Recall** - Coverage of relevant information
- **Context Relevance** - Relevance of retrieved context to query
- **Context Entities Recall** - Entity coverage in retrieved docs
- **Semantic Diversity** - Diversity of retrieved content

### Generation Metrics
- **Faithfulness** - Answer grounding in context
- **Factual Consistency** - Consistency with source documents
- **Answer Relevance** - Relevance to the question
- **BERTScore** - Semantic similarity to reference
- **Attribution Score** - Source attribution quality
- **Answer Completeness** - Coverage of expected answer
- **Self-Consistency** - Multi-sample consistency

### System Metrics
- **Answer Correctness** - Overall accuracy
- **Multi-Hop Reasoning** - Complex reasoning ability
- **Context Utilization** - Effective use of context

## Project Structure

```
rag-evaluator/
├── src/rag_evaluator/          # Core package
│   ├── framework/              # GQM evaluation framework
│   ├── metrics/                # Metric implementations
│   ├── adapters/               # RAG system adapters
│   ├── generators/             # Question generation
│   └── clients/                # API clients (Gemini, Voyage)
├── examples/                   # Usage examples
│   ├── rag_system_evaluation.py
│   ├── question_generation.py
│   └── evaluation_config.yaml
├── dashboard/                  # Web dashboard
│   ├── backend/                # FastAPI server
│   └── frontend/               # React app
├── evaluation_results/         # Output directory
├── questions/                  # Cached questions
└── logs/                       # Evaluation logs
```

## Output

Evaluation results are saved as JSON files in the `evaluation_results/` directory with:
- Hierarchical structure (goals → questions → metrics)
- Per-test-case scores and aggregated results
- Metadata (model, timestamp, configuration)
- Detailed metrics breakdown

Results can be viewed via the dashboard or processed programmatically.

## Troubleshooting

### Common Issues

**spaCy model not found**
- The framework automatically downloads required models on first use
- If download fails, manually install: `python -m spacy download en_core_web_sm`

**Pinecone connection errors**
- Verify `PINECONE_API_KEY` and `PINECONE_INDEX_NAME` in `.env`
- Ensure your Pinecone index exists and is active
- Check API key permissions

**Gemini API errors**
- Verify `GEMINI_API_KEY` is valid
- Check rate limits on your API key
- Ensure model name is correct (e.g., `gemini-2.0-flash`)

**Ollama connection refused**
- Start Ollama: `ollama serve`
- Verify model is pulled: `ollama list`
- Check Ollama is running on `http://localhost:11434`

**Dashboard not starting**
- Ensure Node.js and npm are installed: `npm --version`
- Install FastAPI dependencies: `pip install fastapi uvicorn python-multipart`
- Check ports 8000 and 5173 are not in use

**Memory issues**
- The framework includes automatic memory cleanup
- Reduce batch sizes in evaluation config
- Use smaller models or enable GPU acceleration

### Logs

Check the `logs/` directory for detailed error messages and execution traces.