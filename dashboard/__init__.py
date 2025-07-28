"""Dashboard integration for RAG Evaluator"""
import subprocess
import webbrowser
import time
import sys
from pathlib import Path
import logging

logger = logging.getLogger("rag_evaluator.dashboard")

class DashboardLauncher:
    
    def __init__(self):
        self.dashboard_dir = Path(__file__).parent.parent.parent.parent / "dashboard"
        self.process = None
    
    def launch(self, open_browser: bool = True):
        runner_path = self.dashboard_dir / "run.py"
        
        if not runner_path.exists():
            raise FileNotFoundError(f"Dashboard runner not found at {runner_path}")
        
        try:
            self.process = subprocess.Popen(
                [sys.executable, str(runner_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            logger.info("Dashboard servers starting...")
            
            time.sleep(5)
            
            if open_browser:
                webbrowser.open("http://localhost:5173")
                logger.info("Opened dashboard in browser")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to launch dashboard: {e}")
            return False
    
    def stop(self):
        if self.process:
            self.process.terminate()
            self.process.wait()
            logger.info("Dashboard servers stopped")