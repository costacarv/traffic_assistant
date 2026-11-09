import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Mock do RAGEngine antes de importar o app para evitar instanciar o modelo durante os testes
from api.main import app

client = TestClient(app)

def test_health_check():
    """Testa o endpoint de health check."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

@patch("api.main.rag")
def test_ask_question_success_dict(mock_rag):
    """Testa a rota /ask quando o RAG retorna um dicionário estruturado do LangChain."""
    mock_rag.query.return_value = {
        "answer": "O Artigo 28 do CTB estabelece...",
        "context": [
            MagicMock(page_content="Trecho do CTB", metadata={"page": 12})
        ]
    }

    payload = {"question": "Quais as regras de condução?"}
    response = client.post("/ask", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "O Artigo 28 do CTB estabelece..."
    assert len(data["source_documents"]) == 1
    assert data["source_documents"][0]["metadata"]["page"] == 12

@patch("api.main.rag")
def test_ask_question_success_string(mock_rag):
    """Testa a rota /ask quando o RAG retorna apenas uma string limpa."""
    mock_rag.query.return_value = "Resposta em string pura"

    payload = {"question": "Pergunta simples"}
    response = client.post("/ask", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "Resposta em string pura"
    assert data["source_documents"] == []

@patch("api.main.rag")
def test_ask_question_exception(mock_rag):
    """Testa a captura de exceções e incremento de métricas de erro na rota /ask."""
    mock_rag.query.side_effect = Exception("Falha de conexão com a Groq")

    payload = {"question": "Erro forçado"}
    response = client.post("/ask", json=payload)
    
    assert response.status_code == 500
    assert "Falha de conexão com a Groq" in response.json()["detail"]