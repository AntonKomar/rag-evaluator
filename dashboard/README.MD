# RAG Evaluator Dashboard

## Setup

### Prerequisites

- Python 3.13+
- Node.js 16+ and npm

### Installation

1. Install backend dependencies:
```bash
cd dashboard/backend
pip install -r requirements.txt
```

2. Install frontend dependencies:
```bash
cd dashboard/frontend
npm install
```

## Running the Dashboard

From the dashboard directory:
```bash
python run.py

or

python -m dashboard
```

This will:
- Start the FastAPI backend on http://localhost:8000
- Start the Vue frontend on http://localhost:5173
- Open your browser automatically

### Option 2: Run Servers Separately

Backend:
```bash
cd dashboard/backend
uvicorn app:app --reload --port 8000
```

Frontend:
```bash
cd dashboard/frontend
npm run dev
```

### Option 3: From Your Evaluation Script

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