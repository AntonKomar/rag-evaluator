import os
from typing import List
import numpy as np
import torch
from transformers import AutoModelForSequenceClassification
from bert_score import BERTScorer
import re
import logging

from rag_evaluator.clients.voyage_client import embed_texts
from rag_evaluator.config import get_config

from ..framework.evaluation_data import EvaluationData
from ..clients.gemini_client import GeminiClient, get_gemini_client


def get_optimal_device():
    if torch.cuda.is_available():
        return torch.device("cuda")
    elif torch.backends.mps.is_available():
        return torch.device("mps")
    else:
        return torch.device("cpu")


class HHEM:    
    def __init__(self):
        self.device = get_optimal_device()
        
        model_name = "vectara/hallucination_evaluation_model"
        self.model = AutoModelForSequenceClassification.from_pretrained(
            model_name,
            trust_remote_code=True
        )
        self.model.to(self.device)
        self.model.eval()

    def _score_pairs(self, premises: List[str], hypotheses: List[str]) -> List[float]:
        pairs = list(zip(premises, hypotheses))
        scores = self.model.predict(pairs)
        return scores.tolist()
    
    def score_claim(self, claim: str, context: str) -> float:
        score = self._score_pairs([context], [claim])[0]
        return score
    
    def batch_score(self, claims: List[str], contexts: List[str]) -> List[float]:
        return self._score_pairs(contexts, claims)
    

_hhem_instance = None

def get_hhem():
    global _hhem_instance
    if _hhem_instance is None:
        _hhem_instance = HHEM()
    return _hhem_instance

def clear_hhem():
    global _hhem_instance
    if _hhem_instance is not None:
        import gc
        import torch
        del _hhem_instance
        _hhem_instance = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        elif torch.backends.mps.is_available():
            torch.mps.empty_cache()


def _extract_claims_with_llm(text: str, model: GeminiClient) -> List[str]:
    prompt = f"""Extract only factual claims from this text.
Each claim should be a single, verifiable statement.
List only the claims, nothing else.

Text: {text}

Example claims:
1. [First claim]
2. [Second claim]
3. [Third claim]

Claims:"""
    
    try:
        response = model.generate_for_metrics(prompt)
        
        claims = []
        for line in response.split('\n'):
            if line.strip() and any(line.strip().startswith(str(i)) for i in range(1, 21)):
                claim = re.sub(r'^\d+\.\s*', '', line.strip())
                if claim:
                    claims.append(claim)
        
        return claims
        
    except Exception as e:
        return [text.strip()] if text.strip() else []


def faithfulness(evaluation_data: EvaluationData)  -> float | dict:
    model = get_gemini_client()
    
    hhem = get_hhem()
    
    total_faithfulness = 0.0
    count = 0
    detailed_results = []
    
    for result in evaluation_data.test_case_results:
        if not result.retrieved_documents or not result.generated_answer:
            total_faithfulness += 0.0
            count += 1
            continue
        
        claims = _extract_claims_with_llm(result.generated_answer, model)
        
        contexts = [
            doc.get_content() if hasattr(doc, "get_content") else str(doc)
            for doc in result.retrieved_documents
        ]
        combined_context = "\n\n".join(contexts)
        
        context_list = [combined_context] * len(claims)
        
        scores = hhem.batch_score(claims, context_list)
        
        weights = []
        for claim in claims:
            weight = len(claim.split())
            weights.append(weight)
        
        weights = np.array(weights)
        weights = weights / weights.sum() if weights.sum() > 0 else np.ones_like(weights) / len(weights)
        
        case_faithfulness = np.sum(weights * scores)
        
        total_faithfulness += case_faithfulness
        count += 1

        if get_config().return_detailed_results:
            detailed_results.append({
                "query": result.query,
                "generated_answer": result.generated_answer,
                "question_type": result.question_type,
                "score": case_faithfulness,
            })

    overall_score = total_faithfulness / count if count > 0 else 0.0

    clear_hhem()

    if get_config().return_detailed_results:
        return {
            "score": overall_score,
            "individual_scores": detailed_results
        }
    
    return overall_score


def factual_consistency(evaluation_data: EvaluationData)  -> float | dict:

    hhem = get_hhem()
    
    total_consistency = 0.0
    count = 0
    detailed_results = []
    
    for result in evaluation_data.test_case_results:
        if not result.retrieved_documents or not result.generated_answer:
            total_consistency += 0.0
            count += 1
            continue
        
        contexts = [
            doc.get_content() if hasattr(doc, "get_content") else str(doc)
            for doc in result.retrieved_documents
        ]
        combined_context = "\n\n".join(contexts)
        
        consistency_score = hhem.score_claim(
            result.generated_answer,
            combined_context
        )
        
        total_consistency += consistency_score
        count += 1

        if get_config().return_detailed_results:
            detailed_results.append({
                "query": result.query,
                "generated_answer": result.generated_answer,
                "question_type": result.question_type,
                "score": consistency_score,
            })

    overall_score = total_consistency / count if count > 0 else 0.0

    clear_hhem()

    if get_config().return_detailed_results:
        return {
            "score": overall_score,
            "individual_scores": detailed_results
        }
    
    return overall_score


def answer_relevance(evaluation_data: EvaluationData)  -> float | dict:    
    logger = logging.getLogger("rag_evaluator.answer_relevance")
    model = get_gemini_client()
    
    total_relevance = 0.0
    count = 0
    detailed_results = []
    
    for result in evaluation_data.test_case_results:
        if not result.generated_answer:
            total_relevance += 0.0
            count += 1
            continue
        
        prompt = f"""Given this answer, generate 3 questions that this answer directly addresses.
Each question should capture different aspects of the answer.
Questions should be natural and specific.

Answer: {result.generated_answer}

Format each question on a new line starting with the number. Output only list of the questions, nothing else.

Example questions:
1. [First question]
2. [Second question]
3. [Third question]

Questions:"""
        
        try:
            response = model.generate_for_metrics(prompt)
            
            generated_questions = []
            for line in response.split('\n'):
                if line.strip() and any(line.strip().startswith(str(i)) for i in range(1, 4)):
                    question = re.sub(r'^\d+\.\s*', '', line.strip())
                    if question:
                        generated_questions.append(question)
            
            if not generated_questions:
                generated_questions = [response.strip()]
            
            all_texts = [result.query] + generated_questions
            embeddings = embed_texts(all_texts)
            
            original_embedding = embeddings[0]
            generated_embeddings = embeddings[1:]
            
            similarities = []
            for gen_emb in generated_embeddings:
                sim = np.dot(original_embedding, gen_emb) / (
                    np.linalg.norm(original_embedding) * np.linalg.norm(gen_emb)
                )
                similarities.append(float(sim))
            
            similarities_sorted = sorted(similarities, reverse=True)
            if len(similarities_sorted) >= 3:
                relevance_score = (0.5 * similarities_sorted[0] + 
                                 0.3 * similarities_sorted[1] + 
                                 0.2 * similarities_sorted[2])
            else:
                relevance_score = np.mean(similarities)
            
        except Exception as e:
            logger.error(f"Multi-question generation failed: {e}")
            relevance_score = 0.0
        
        total_relevance += relevance_score
        count += 1

        if get_config().return_detailed_results:
            detailed_results.append({
                "query": result.query,
                "generated_answer": result.generated_answer,
                "question_type": result.question_type,
                "score": relevance_score,
            })

    overall_score = total_relevance / count if count > 0 else 0.0

    if get_config().return_detailed_results:
        return {
            "score": overall_score,
            "individual_scores": detailed_results
        }
    
    return overall_score


def bertscore(evaluation_data):
    logger = logging.getLogger("rag_evaluator.bertscore")
    device = get_optimal_device().type
    model_type = get_config().bertscore_model

    scorer = BERTScorer(
        model_type=model_type, 
        lang="en",
        device=device,
        use_fast_tokenizer=True, 
        batch_size=8,
        idf=False,
        rescale_with_baseline=False)
    
    all_scores = []
    detailed_results = []
    all_zero = True

    for test in evaluation_data.test_case_results:
        answer = test.generated_answer
        docs = test.retrieved_documents
        if not answer or not docs:
            continue

        contexts = []
        for doc in docs:
            text = doc.get_content() if hasattr(doc, "get_content") else str(doc)
            if text is None: 
                text = ""
            text = text.strip()
            if text == "":
                logger.warning(f"Warning: empty context for query '{test.query}' will be skipped.")
                continue
            contexts.append(text)
        if not contexts:
            logger.warning(f"Warning: no valid context text for query '{test.query}'. Skipping BERTScore.")
            continue

        try:
            P, R, F = scorer.score([answer] * len(contexts), contexts)
        except Exception as e:
            if device == "mps":
                logger.info(f"Error on MPS (will retry on CPU): {e}")
                scorer = BERTScorer(model_type="roberta-large", lang="en", 
                                    device="cpu", use_fast_tokenizer=True, 
                                    batch_size=4, idf=False, rescale_with_baseline=False)
                P, R, F = scorer.score([answer] * len(contexts), contexts)
            else:
                logger.info(f"Error computing score for query '{test.query}': {e}")
                continue

        F1_scores = F.tolist() if hasattr(F, 'tolist') else list(F)
        max_F1 = max(F1_scores) if F1_scores else 0.0
        all_scores.append(max_F1)
        if max_F1 > 0:
            all_zero = False

        if get_config().return_detailed_results:
            detailed_results.append({
                "query": test.query,
                "generated_answer": answer,
                "question_type": test.question_type,
                "score": max_F1,
            })
    
    if all_scores:
        overall_score = sum(all_scores) / len(all_scores)
    else:
        overall_score = 0.0

    if all_zero and all_scores:
        logger.warning("WARNING: All BERTScore F1 scores are 0.0. This may indicate a configuration issue (e.g., IDF or device problems).")
    elif not all_scores:
        logger.warning("WARNING: No BERTScore could be computed (all test cases skipped or failed).")

    if get_config().return_detailed_results:
        return {"score": overall_score, "individual_scores": detailed_results}
    else:
        return overall_score


def attribution_score(evaluation_data: EvaluationData)  -> float | dict:
    logger = logging.getLogger("rag_evaluator.attribution_score")
    model = get_gemini_client()
    
    total_scores = []
    detailed_results = []
    
    for result in evaluation_data.test_case_results:
        if not result.generated_answer or not result.retrieved_documents:
            continue
        
        sources = [
            doc.get_content() if hasattr(doc, "get_content") else str(doc)
            for doc in result.retrieved_documents
        ]
        source_text = "\n\n".join([f"[Source {i+1}]\n{src[:500]}" for i, src in enumerate(sources)])
        
        prompt = f"""Evaluate attribution quality.

Query: {result.query}

Answer: {result.generated_answer}

Sources:
{source_text}

Score (0-10) based on:
- Are factual claims attributed to sources?
- Do cited sources actually contain the information?
- Are attributions clear and specific?

Output only the numeric score."""

        try:
            response = model.generate_for_metrics(prompt)
            score = float(re.search(r'(\d+(?:\.\d+)?)', response).group(1)) / 10.0
            total_scores.append(score)

            if get_config().return_detailed_results:
                detailed_results.append({
                    "query": result.query,
                    "generated_answer": result.generated_answer,
                    "question_type": result.question_type,
                    "score": score,
                })
        except Exception as e:
            logger.warning(f"Failed to parse attribution score: {e}")
    
    overall_score = np.mean(total_scores) if total_scores else 0.0

    if get_config().return_detailed_results:
        return {
            "score": overall_score,
            "individual_scores": detailed_results
        }
    
    return overall_score


def answer_completeness(evaluation_data: EvaluationData)  -> float | dict:
    logger = logging.getLogger("rag_evaluator.attribution_score")
    model = get_gemini_client()
    
    total_completeness = 0.0
    count = 0
    detailed_results = []
    
    for result in evaluation_data.test_case_results:
        if not result.generated_answer:
            continue
        
        prompt = f"""Analyze answer completeness.

Query: {result.query}

Answer: {result.generated_answer}

First, identify all aspects/sub-questions in the query.
Then, check which aspects are addressed in the answer.

Provide completeness score (0-10) based on:
1. All query aspects addressed
2. Sufficient depth for each aspect
3. No important information missing

Output only the numeric score.

Score:"""
        
        try:
            response = model.generate_for_metrics(prompt)
            score = float(re.search(r'(\d+(?:\.\d+)?)', response).group(1))
            completeness = score / 10.0
        except Exception as e:
            logger.warning(f"Failed to parse answer completeness score: {e}")
        
        total_completeness += completeness
        count += 1

        if get_config().return_detailed_results:
            detailed_results.append({
                "query": result.query,
                "generated_answer": result.generated_answer,
                "question_type": result.question_type,
                "score": completeness,
            })
    
    overall_score = total_completeness / count if count > 0 else 0.0

    if get_config().return_detailed_results:
        return {
            "score": overall_score,
            "individual_scores": detailed_results
        }
    
    return overall_score


def self_consistency_score(evaluation_data: EvaluationData)  -> float | dict:
    logger = logging.getLogger("rag_evaluator.attribution_score")
    model = get_gemini_client()
    
    total_consistency = 0.0
    count = 0
    detailed_results = []
    
    for result in evaluation_data.test_case_results:
        if not result.generated_answer:
            continue
        
        if len(result.generated_answer.split()) < 20:
            total_consistency += 1.0
            count += 1
            continue
        
        prompt = f"""Check for internal consistency in this answer.

Answer: {result.generated_answer}

Look for:
1. Contradictory statements
2. Logical inconsistencies
3. Conflicting facts or claims
4. Unclear or ambiguous statements

Rate consistency (0-10), where 10 is perfectly consistent.
Output only the numeric score.

Score:"""
        
        try:
            response = model.generate_for_metrics(prompt)
            score = float(re.search(r'(\d+(?:\.\d+)?)', response).group(1))
            consistency = score / 10.0
        except Exception as e:
            logger.warning(f"Failed to parse answer self consistency score: {e}")
        
        total_consistency += consistency
        count += 1

        if get_config().return_detailed_results:
            detailed_results.append({
                "query": result.query,
                "generated_answer": result.generated_answer,
                "question_type": result.question_type,
                "score": consistency,
            })

    overall_score = total_consistency / count if count > 0 else 0.0

    if get_config().return_detailed_results:
        return {
            "score": overall_score,
            "individual_scores": detailed_results
        }
    
    return overall_score