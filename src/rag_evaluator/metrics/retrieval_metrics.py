import json
import logging
import re
from typing import List, Set
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import spacy

from rag_evaluator.clients.gemini_client import GeminiClient, get_gemini_client
from rag_evaluator.clients.voyage_client import embed_texts
from rag_evaluator.config import get_config

from ..framework.evaluation_data import EvaluationData


_nlp_model = None


def _get_nlp_model():
    global _nlp_model
    if _nlp_model is None:
        try:
            spacy.prefer_gpu()
        except Exception:
            pass
        try:
            _nlp_model = spacy.load("en_core_web_trf")
        except OSError:
            import subprocess
            try:
                subprocess.run(["python", "-m", "spacy", "download", "en_core_web_trf"], check=True)
                _nlp_model = spacy.load("en_core_web_trf")
            except Exception:
                try:
                    _nlp_model = spacy.load("en_core_web_sm")
                except OSError:
                    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"], check=False)
                    _nlp_model = spacy.load("en_core_web_sm")
    return _nlp_model


def _extract_entities(text: str) -> Set[str]:
    nlp = _get_nlp_model()
    doc = nlp(text)
    return {ent.text.lower().strip() for ent in doc.ents if ent.text.strip()}


def context_precision(evaluation_data: EvaluationData) -> float | dict:
    logger = logging.getLogger("rag_evaluator.context_precision")
    model = get_gemini_client()

    total_precision = 0.0
    count = 0
    detailed_results = []
    
    for result in evaluation_data.test_case_results:
        if not result.retrieved_documents or not result.query:
            continue
        
        contexts = _extract_document_texts(result.retrieved_documents)[:5]
        
        contexts_text = "\n\n".join([f"{i+1}. {ctx[:200]}..." for i, ctx in enumerate(contexts)])
        
        prompt = f"""Evaluate the relevance of each retrieved context to the query.

Query: {result.query}

Retrieved Contexts:
{contexts_text}

For each context, determine if it contains information that would be useful for answering the query.

Respond with ONLY a JSON array of 1 (relevant) or 0 (not relevant), one for each context in order.

Example response: [1, 0, 1, 0, 1]

Response:"""
        
        try:
            response = model.generate_for_metrics(prompt)
            
            match = re.search(r'\[[\d,\s]+\]', response)
            relevance = json.loads(match.group())
            
            precision_sum = 0.0
            relevant_count = 0
            
            for k, is_relevant in enumerate(relevance, 1):
                if is_relevant:
                    relevant_count += 1
                    precision_sum += relevant_count / k
            
            precision = precision_sum / sum(relevance) if sum(relevance) > 0 else 0.0
            
        except Exception as e:
            logger.warning(f"LLM evaluation failed: {e}")
            precision = 0.0
        
        total_precision += precision
        count += 1

        if get_config().return_detailed_results:
            detailed_results.append({
                "query": result.query,
                "generated_answer": result.generated_answer,
                "question_type": result.question_type,
                "score": precision,
            })
    
    overall_score = total_precision / count if count > 0 else 0.0
    
    if get_config().return_detailed_results:
        return {
            "score": overall_score,
            "individual_scores": detailed_results
        }
    
    return overall_score


def _extract_document_texts(documents) -> List[str]:
    return [
        doc.get_content() if hasattr(doc, "get_content") else str(doc)
        for doc in documents
    ]


def context_recall(evaluation_data: EvaluationData)  -> float | dict:
    logger = logging.getLogger("rag_evaluator.context_recall")
    model = get_gemini_client()
    
    total_recall = 0.0
    count = 0
    detailed_results = []
    
    for result in evaluation_data.test_case_results:
        ground_truth = result.ground_truth
        if not ground_truth or not result.retrieved_documents:
            total_recall += 0.0
            count += 1
            continue
        
        try:
            retrieved_texts = _extract_document_texts(result.retrieved_documents)
            contexts_text = "\n\n".join([f"Context {i+1}: {text[:300]}..." 
                                       for i, text in enumerate(retrieved_texts)])
            
            recall_score = _compute_claim_attribution(ground_truth, contexts_text, model, logger)
            
            total_recall += recall_score
            count += 1
            
        except Exception as e:
            logger.error(f"Failed to compute recall for query '{result.query}': {e}")
            total_recall += 0.0
            recall_score = 0.0
            count += 1

        if get_config().return_detailed_results:
            detailed_results.append({
                "query": result.query,
                "generated_answer": result.generated_answer,
                "question_type": result.question_type,
                "score": recall_score,
            })
    
    overall_score = total_recall / count if count > 0 else 0.0
    
    if get_config().return_detailed_results:
        return {
            "score": overall_score,
            "individual_scores": detailed_results
        }
    
    return overall_score


def _compute_claim_attribution(reference: str, contexts_text: str, model: GeminiClient, logger: logging.Logger) -> float:
    claims_prompt = f"""Extract all factual claims from this reference answer.
Each claim should be a single, verifiable statement.

Reference Answer: {reference}

List each claim on a separate line starting with a number. Output only list of the claims, nothing else.

Example claims:
1. [First claim]
2. [Second claim]
3. [Third claim]

Claims:"""
    
    try:
        claims_response = model.generate_for_metrics(claims_prompt)
        
        claims = []
        for line in claims_response.split('\n'):
            if line.strip() and any(line.strip().startswith(str(i)) for i in range(1, 21)):
                claim = re.sub(r'^\d+\.\s*', '', line.strip())
                if claim:
                    claims.append(claim)
        
        if not claims:
            return 0.0
        
        attribution_prompt = f"""For each claim below, determine if it can be supported/attributed to the provided contexts.

Contexts:
{contexts_text}

Claims to check:
{chr(10).join([f"{i+1}. {claim}" for i, claim in enumerate(claims)])}

For each claim, respond with 1 (can be attributed) or 0 (cannot be attributed).
Respond with only a JSON array: [1, 0, 1, 0, ...]

Response:"""
        
        attribution_response = model.generate_for_metrics(attribution_prompt)
        
        match = re.search(r'\[[\d,\s]+\]', attribution_response)
        if match:
            attributions = json.loads(match.group())
            if len(attributions) == len(claims):
                return sum(attributions) / len(claims)
        
        return len(claims) / 3.0
        
    except Exception as e:
        logger.warning(f"Claim attribution failed: {e}")
        return 0.0


def context_relevance(evaluation_data: EvaluationData)  -> float | dict:
    logger = logging.getLogger("rag_evaluator.context_relevance")
    model = get_gemini_client()
    
    total_relevance = 0.0
    count = 0
    detailed_results = []
    
    for result in evaluation_data.test_case_results:
        if not result.retrieved_documents or not result.query:
            total_relevance += 0.0
            count += 1
            continue
        
        try:
            retrieved_texts = _extract_document_texts(result.retrieved_documents)
            contexts_text = "\n\n".join([f"Context {i+1}: {text[:400]}..." 
                                       for i, text in enumerate(retrieved_texts[:5])])
            
            relevance_score = _compute_statement_relevance(result.query, contexts_text, model, logger)
            
            total_relevance += relevance_score
            count += 1
            
        except Exception as e:
            logger.error(f"Failed to compute context relevance for query '{result.query}': {e}")
            total_relevance += 0.0
            relevance_score = 0.0
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


def _compute_statement_relevance(query: str, contexts_text: str, model, logger: logging.Logger)  -> float | dict:
    extraction_prompt = f"""Extract all meaningful statements from the provided contexts.
Each statement should be a single, complete fact or piece of information.

Contexts:
{contexts_text}

List each statement on a separate line starting with a number. Output only list of the statements, nothing else.

Example statements:
1. [First statement]
2. [Second statement]
3. [Third statement]

Statements:"""
    
    try:
        extraction_response = model.generate_for_metrics(extraction_prompt)
        
        statements = []
        for line in extraction_response.split('\n'):
            if line.strip() and any(line.strip().startswith(str(i)) for i in range(1, 21)):
                statement = re.sub(r'^\d+\.\s*', '', line.strip())
                if statement:
                    statements.append(statement)
        
        if not statements:
            return 0.0
        
        statements_text = "\n".join([f"{i+1}. {stmt}" for i, stmt in enumerate(statements)])
        
        classification_prompt = f"""For each statement below, determine if it is relevant to answering this query.

Query: {query}

Statements:
{statements_text}

For each statement, respond with 1 (relevant) or 0 (not relevant).
Respond with only a JSON array: [1, 0, 1, 0, ...]

Response:"""
        
        classification_response = model.generate_for_metrics(classification_prompt)
        
        match = re.search(r'\[[\d,\s]+\]', classification_response)
        if match:
            relevance_scores = json.loads(match.group())
            if len(relevance_scores) == len(statements):
                return sum(relevance_scores) / len(relevance_scores)
        
        return len(statements) / 5.0
        
    except Exception as e:
        logger.warning(f"Statement relevance computation failed: {e}")
        return 0.0


def context_entities_recall(evaluation_data: EvaluationData)  -> float | dict:    
    total_recall = 0.0
    count = 0
    detailed_results = []
    
    for result in evaluation_data.test_case_results:
        expected_entities = result.entities
        if not expected_entities:
            continue
        
        if not result.retrieved_documents:
            total_recall += 0.0
            count += 1
            continue
        
        retrieved_texts = _extract_document_texts(result.retrieved_documents)
        combined_text = " ".join(retrieved_texts)
        
        retrieved_entities_raw = _extract_entities(combined_text)
        
        expected_entities_normalized = {
            _normalize_entity(entity) for entity in expected_entities
        }
        retrieved_entities_normalized = {
            _normalize_entity(entity) for entity in retrieved_entities_raw
        }
        
        intersection = retrieved_entities_normalized & expected_entities_normalized
        recall = len(intersection) / len(expected_entities_normalized)
        
        total_recall += recall
        count += 1

        if get_config().return_detailed_results:
            detailed_results.append({
                "query": result.query,
                "generated_answer": result.generated_answer,
                "question_type": result.question_type,
                "score": recall,
            })
    
    overall_score = total_recall / count if count > 0 else 0.0
    
    if get_config().return_detailed_results:
        return {
            "score": overall_score,
            "individual_scores": detailed_results
        }
    
    return overall_score


def _normalize_entity(entity: str) -> str:
    normalized = entity.lower().strip()
    
    articles = ['the ', 'a ', 'an ']
    for article in articles:
        if normalized.startswith(article):
            normalized = normalized[len(article):]
            break
    
    normalized = ' '.join(normalized.split())
    normalized = normalized.rstrip("’'s")
    normalized = normalized.strip(".,;:")
    
    return normalized


def semantic_diversity(
    evaluation_data: EvaluationData,
    lambda_param: float = 0.5,
    top_k: int = 5
)  -> float | dict:
    logger = logging.getLogger("rag_evaluator.semantic_diversity")
    
    total_mmr_score = 0.0
    count = 0
    detailed_results = []
    
    for result in evaluation_data.test_case_results:
        if not result.retrieved_documents or len(result.retrieved_documents) < 2:
            continue
        
        query = result.query
        retrieved_texts = [
            doc.get_content() if hasattr(doc, "get_content") else str(doc)
            for doc in result.retrieved_documents[:top_k]
        ]
        
        try:
            all_texts = [query] + retrieved_texts
            embeddings = embed_texts(all_texts)
            
            query_embedding = embeddings[0:1]
            doc_embeddings = embeddings[1:]
            
            mmr_scores = []
            selected_docs = []
            
            for i, doc_emb in enumerate(doc_embeddings):
                query_sim = cosine_similarity(
                    doc_emb.reshape(1, -1), query_embedding
                )[0][0]
                
                if selected_docs:
                    selected_embeddings = np.array([doc_embeddings[j] for j in selected_docs])
                    max_sim_to_selected = np.max(cosine_similarity(
                        doc_emb.reshape(1, -1), selected_embeddings
                    ))
                else:
                    max_sim_to_selected = 0.0
                
                mmr_score = (lambda_param * query_sim - 
                           (1 - lambda_param) * max_sim_to_selected)
                
                mmr_scores.append(mmr_score)
                selected_docs.append(i)
            
            avg_mmr = np.mean(mmr_scores)
            normalized_mmr = (avg_mmr + 1) / 2
            
            total_mmr_score += normalized_mmr
            count += 1

            if get_config().return_detailed_results:
                detailed_results.append({
                    "query": result.query,
                    "generated_answer": result.generated_answer,
                    "question_type": result.question_type,
                    "score": normalized_mmr,
                })
            
        except Exception as e:
            logger.warning(f"Failed to compute MMR for query '{query[:50]}...': {e}")
            continue
    

    overall_score = total_mmr_score / count if count > 0 else 0.0
    
    if get_config().return_detailed_results:
        return {
            "score": overall_score,
            "individual_scores": detailed_results
        }
    
    return overall_score