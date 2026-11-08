# api/main.py
import time
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import prometheus_client as prom
from prometheus_fastapi_instrumentator import Instrumentator

# Obtém o caminho base do projeto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_PATH = os.path.join(BASE_DIR, "files", "ctb.pdf")

# Importa a engine de RAG modularizada
from .rag_engine import LegalRAGEngine

app = FastAPI(title="Assistente Jurídico MLOps API")

# Instancia o mecanismo de IA
rag = LegalRAGEngine(pdf_path=PDF_PATH)

# Métricas customizadas do Prometheus
REQUEST_COUNT = prom.Counter('legal_queries_total', 'Total de consultas jurídicas realizadas')
LATENCY = prom.Histogram(
    'legal_query_latency_seconds', 
    'Tempo de resposta da consulta RAG',
    buckets=[0.5, 1.0, 2.5, 5.0, 10.0, 15.0, 30.0]
)
ERROR_COUNT = prom.Counter('legal_query_errors_total', 'Total de erros em consultas')

class QueryRequest(BaseModel):
    question: str

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/ask")
def ask_question(request: QueryRequest):
    REQUEST_COUNT.inc()
    start_time = time.time()
    
    try:
        # Executa a busca através do módulo RAG
        raw_result = rag.query(request.question)
        
        # Trata o retorno caso rag.query devolva um dicionário do LangChain
        if isinstance(raw_result, dict):
            answer_text = raw_result.get("answer") or raw_result.get("result") or str(raw_result)
            sources = raw_result.get("context") or raw_result.get("source_documents") or []
        else:
            answer_text = str(raw_result)
            sources = []

        # Formata os documentos do ChromaDB para JSON serializável
        formatted_sources = []
        for doc in sources:
            if hasattr(doc, "page_content"):
                formatted_sources.append({
                    "page_content": doc.page_content,
                    "metadata": getattr(doc, "metadata", {})
                })
            elif isinstance(doc, dict):
                formatted_sources.append(doc)
        
        # Registra a latência para o Prometheus
        LATENCY.observe(time.time() - start_time)
        
        return {
            "query": request.question,
            "answer": answer_text,
            "source_documents": formatted_sources
        }
    except Exception as e:
        ERROR_COUNT.inc()
        raise HTTPException(status_code=500, detail=str(e))

# Expõe as métricas padrão e customizadas na rota /metrics
Instrumentator().instrument(app).expose(app)