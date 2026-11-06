# api/main.py
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import prometheus_client as prom
from prometheus_fastapi_instrumentator import Instrumentator

import os

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
LATENCY = prom.Summary('legal_query_latency_seconds', 'Tempo de resposta da consulta RAG')
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
        # Executa a busca através do módulo RAG separado
        answer = rag.query(request.question)
        
        # Registra a latência para o Prometheus
        LATENCY.observe(time.time() - start_time)
        return {
            "query": request.question,
            "answer": answer
        }
    except Exception as e:
        ERROR_COUNT.inc()
        raise HTTPException(status_code=500, detail=str(e))

# Expõe as métricas padrão e customizadas na rota /metrics
Instrumentator().instrument(app).expose(app)