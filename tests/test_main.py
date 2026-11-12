from urllib import response

from fastapi.testclient import TestClient
from unittest.mock import patch
from api.main import app

client = TestClient(app)

def test_health_check():
    """Garante que a rota de health check responde 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

@patch("api.main.rag.query")
def test_ask_question_mocked(mock_rag_query):
    """Testa a rota /ask usando Mock para não gastar a API Key da Groq nos testes."""
    mock_rag_query.return_value = "Resposta simulada para teste unitário."

    response = client.post("/ask", json={"question": "Qual a velocidade máxima nas vias urbanas?"}, headers = {"X-API-Key": "test_key_for_ci"})
    
    assert response.status_code == 200
    assert response.json()["query"] == "Qual a velocidade máxima nas vias urbanas?"
    assert response.json()["answer"] == "Resposta simulada para teste unitário."

@patch("api.main.rag.query")
def test_ask_endpoint_failure(mock_rag_query):
    """Garante que falhas internas na IA retornam HTTP 500 corretamente."""
    mock_rag_query.side_effect = Exception("Erro na API da Groq")

    payload = {"question": "Pergunta sobre multa no CTB que vai falhar"}
    response = client.post("/ask", json=payload, headers = {"X-API-Key": "test_key_for_ci"})

    assert response.status_code == 500
    assert "Erro interno ao consultar a base jurídica" in response.json()["detail"]