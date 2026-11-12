# api/main.py
import time
import os
import logging
from fastapi import FastAPI, HTTPException, Depends, Request
from pydantic import BaseModel
import prometheus_client as prom
from prometheus_fastapi_instrumentator import Instrumentator

# Obtém o caminho base do projeto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_PATH = os.path.join(BASE_DIR, "files", "ctb.pdf")

# Importa a engine de RAG e o módulo de segurança/guardrails
from .rag_engine import LegalRAGEngine
from .security import verify_api_key, validate_traffic_guardrail

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Assistente Jurídico MLOps API")


# Middleware para adicionar cabeçalhos de segurança (resolve alertas do OWASP ZAP)
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
    response.headers["X-Frame-Options"] = "DENY"
    return response


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


@app.post("/ask", dependencies=[Depends(verify_api_key)])
def ask_question(request: QueryRequest):
    # Valida tamanho, bloqueia prompt injection e filtra domínio antes de gastar tokens
    validated_question = validate_traffic_guardrail(request.question)

    REQUEST_COUNT.inc()
    start_time = time.time()

    try:
        # Executa a busca através do módulo RAG usando a pergunta validada
        raw_result = rag.query(validated_question)

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
            "query": validated_question,
            "answer": answer_text,
            "source_documents": formatted_sources
        }
    except HTTPException:
        raise
    except Exception as e:
        ERROR_COUNT.inc()
        logger.error(f"Erro interno ao processar consulta RAG: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Erro interno ao consultar a base jurídica. Tente novamente."
        )


# Expõe as métricas padrão e customizadas na rota /metrics
Instrumentator().instrument(app).expose(app)