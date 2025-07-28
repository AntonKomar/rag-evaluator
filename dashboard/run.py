#!/usr/bin/env python3
import subprocess
import sys
import time
import signal
from pathlib import Path

processes = []

def signal_handler(sig, frame):
    print("\n\nShutting down servers...")
    for process in processes:
        try:
            process.terminate()
            process.wait(timeout=5)
        except:
            process.kill()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def check_npm():
    try:
        subprocess.run(["npm", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_frontend_deps():
    frontend_dir = Path(__file__).parent / "frontend"
    node_modules = frontend_dir / "node_modules"
    
    if not node_modules.exists():
        print("Installing frontend dependencies...")
        subprocess.run(["npm", "install"], cwd=frontend_dir, check=True)
        print("Frontend dependencies installed.")

def start_backend():
    backend_dir = Path(__file__).parent / "backend"
    print("Starting backend server on http://localhost:8000...")
    
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
        cwd=backend_dir
    )
    processes.append(process)
    return process

def start_frontend():
    frontend_dir = Path(__file__).parent / "frontend"
    print("Starting frontend server on http://localhost:5173...")
    
    process = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=frontend_dir
    )
    processes.append(process)
    return process

def main():
    print("RAG Evaluator Dashboard")
    
    if not check_npm():
        print("Error: npm is not installed. Please install Node.js and npm first.")
        print("Visit: https://nodejs.org/")
        sys.exit(1)
    
    install_frontend_deps()
    
    backend_process = start_backend()
    time.sleep(2)
    
    frontend_process = start_frontend()
    time.sleep(3)
    
    print("\nDashboard is running!")
    print("Open http://localhost:5173 in your browser")
    print("API docs available at http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop all servers\n")
    
    try:
        backend_process.wait()
        frontend_process.wait()
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    main()