from unittest.mock import patch
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200

@patch("api.main.rag.query")
def test_ask_question_success(mock_rag_query):
    # Mock do retorno do RAG para evitar chamada real de API no teste
    mock_rag_query.return_value = {
        "answer": "O veículo é...",
        "source_documents": []
    }
    
    response = client.post("/ask", json={"question": "O que é um veículo?"})
    assert response.status_code == 200
    assert "answer" in response.json()