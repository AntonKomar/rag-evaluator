from typing import List, Any, Optional
from langchain.schema import Document, BaseRetriever
from dataclasses import dataclass
from langchain.chains.base import Chain

@dataclass
class RAGResult:
    query: str
    answer: str
    retrieved_documents: List[Document]

class LangChainRAGAdapter:
    def __init__(self, rag_pipeline: Chain, retriever: Optional[BaseRetriever] = None):
        self.rag_pipeline = rag_pipeline
        self.retriever = retriever
    
    def retrieve(self, query: str) -> List[Document]:
        return self.retriever.get_relevant_documents(query)
    
    def query(self, query: str) -> RAGResult:
        retrieved_documents = self.retrieve(query)
        
        response = self.rag_pipeline.invoke({"query": query})
        answer = self._extract_answer(response)
        
        return RAGResult(
            query=query,
            answer=answer,
            retrieved_documents=retrieved_documents
        )
    
    def _extract_answer(self, response: Any) -> str:
        if isinstance(response, dict):
            return response.get("result", response.get("answer", str(response)))
        return str(response)