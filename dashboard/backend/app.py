from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import json
from datetime import datetime

app = FastAPI(title="RAG Evaluator Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RESULTS_DIR = Path(__file__).parent.parent.parent / "evaluation_results"
QUESTIONS_DIR = Path(__file__).parent.parent.parent / "questions"

@app.get("/api/evaluations")
async def get_evaluations():
    if not RESULTS_DIR.exists():
        return []
    
    evaluations = []
    for file in RESULTS_DIR.glob("*.json"):
        try:
            mtime = datetime.fromtimestamp(file.stat().st_mtime)
            evaluations.append({
                "id": file.stem,
                "filename": file.name,
                "timestamp": mtime.isoformat(),
                "size": file.stat().st_size
            })
        except Exception as e:
            continue
    
    return sorted(evaluations, key=lambda x: x["timestamp"], reverse=True)

@app.get("/api/evaluations/{evaluation_id}")
async def get_evaluation_detail(evaluation_id: str):
    file_path = RESULTS_DIR / f"{evaluation_id}.json"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/questions")
async def get_question_sets():
    """List all question cache files"""
    if not QUESTIONS_DIR.exists():
        return []
    
    question_sets = []
    for file in QUESTIONS_DIR.glob("*.json"):
        try:
            with open(file, 'r') as f:
                data = json.load(f)
            
            question_types = {}
            for item in data:
                q_type = item.get('question_type', 'unknown')
                question_types[q_type] = question_types.get(q_type, 0) + 1
            
            question_sets.append({
                "id": file.stem,
                "filename": file.name,
                "total_questions": len(data),
                "question_types": question_types,
                "timestamp": datetime.fromtimestamp(file.stat().st_mtime).isoformat()
            })
        except Exception as e:
            continue
    
    return sorted(question_sets, key=lambda x: x["timestamp"], reverse=True)

@app.get("/api/questions/{question_set_id}")
async def get_questions_detail(question_set_id: str):
    """Get detailed questions from a set"""
    file_path = QUESTIONS_DIR / f"{question_set_id}.json"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Question set not found")
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/statistics/{evaluation_id}")
async def get_evaluation_statistics(evaluation_id: str):
    """Calculate statistics for an evaluation"""
    file_path = RESULTS_DIR / f"{evaluation_id}.json"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Calculate statistics
        stats = {
            "overall_score": data.get("overall_score", 0),
            "goals": [],
            "metrics_summary": {},
            "question_types_performance": {},
            "metric_question_type_performance": {}
        }
        
        metric_scores_by_testcase = {}
        
        metric_question_type_scores = {}
        
        for goal in data.get("goals", []):
            goal_stat = {
                "name": goal["name"],
                "score": goal["score"],
                "weight": goal["weight"],
                "questions_count": len(goal.get("questions", []))
            }
            stats["goals"].append(goal_stat)
            
            for question in goal.get("questions", []):
                for metric in question.get("metrics", []):
                    metric_id = metric["id"]
                    
                    if "individual_scores" in metric and metric["individual_scores"]:
                        if metric_id not in metric_scores_by_testcase:
                            metric_scores_by_testcase[metric_id] = {}
                        
                        for score_detail in metric["individual_scores"]:
                            test_case_key = f"{score_detail['query']}_{score_detail['question_type']}"
                            
                            if test_case_key not in metric_scores_by_testcase[metric_id]:
                                metric_scores_by_testcase[metric_id][test_case_key] = score_detail["score"]
                            
                            q_type = score_detail.get("question_type", "unknown")
                            if q_type not in stats["question_types_performance"]:
                                stats["question_types_performance"][q_type] = []
                            stats["question_types_performance"][q_type].append(score_detail["score"])
                            
                            if metric_id not in metric_question_type_scores:
                                metric_question_type_scores[metric_id] = {}
                            if q_type not in metric_question_type_scores[metric_id]:
                                metric_question_type_scores[metric_id][q_type] = []
                            metric_question_type_scores[metric_id][q_type].append(score_detail["score"])
        
        for metric_id, test_case_scores in metric_scores_by_testcase.items():
            scores = list(test_case_scores.values())
            
            if scores:
                stats["metrics_summary"][metric_id] = {
                    "average_score": sum(scores) / len(scores),
                    "min_score": min(scores),
                    "max_score": max(scores),
                    "count": len(scores),
                    "std_dev": calculate_std_dev(scores) if len(scores) > 1 else 0
                }
            else:
                stats["metrics_summary"][metric_id] = {
                    "average_score": 0,
                    "min_score": 0,
                    "max_score": 0,
                    "count": 0,
                    "std_dev": 0
                }
        
        if not metric_scores_by_testcase:
            processed_metrics = set()
            
            for goal in data.get("goals", []):
                for question in goal.get("questions", []):
                    for metric in question.get("metrics", []):
                        metric_id = metric["id"]
                        
                        if metric_id not in processed_metrics:
                            processed_metrics.add(metric_id)
                            
                            stats["metrics_summary"][metric_id] = {
                                "average_score": metric["value"],
                                "min_score": metric["value"],
                                "max_score": metric["value"],
                                "count": 1,
                                "std_dev": 0
                            }
        
        for q_type, scores in stats["question_types_performance"].items():
            if scores:
                stats["question_types_performance"][q_type] = {
                    "average": sum(scores) / len(scores),
                    "count": len(scores),
                    "min": min(scores),
                    "max": max(scores)
                }
        
        for metric_id, question_types in metric_question_type_scores.items():
            if metric_id not in stats["metric_question_type_performance"]:
                stats["metric_question_type_performance"][metric_id] = {}
            
            for q_type, scores in question_types.items():
                if scores:
                    stats["metric_question_type_performance"][metric_id][q_type] = {
                        "average": sum(scores) / len(scores),
                        "count": len(scores)
                    }
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def calculate_std_dev(scores):
    if len(scores) < 2:
        return 0
    mean = sum(scores) / len(scores)
    variance = sum((x - mean) ** 2 for x in scores) / (len(scores) - 1)
    return variance ** 0.5


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)