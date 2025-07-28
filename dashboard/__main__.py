#!/usr/bin/env python3
"""
CLI entry point for RAG Evaluator Dashboard

Usage:
    python -m dashboard
    python -m rag_evaluator.dashboard
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dashboard.run import main

if __name__ == "__main__":
    main()