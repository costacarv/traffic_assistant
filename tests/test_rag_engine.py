from unittest.mock import patch, MagicMock
from api.rag_engine import LegalRAGEngine

@patch("api.rag_engine.PyPDFLoader")
@patch("api.rag_engine.Chroma")
@patch("api.rag_engine.HuggingFaceEmbeddings")
@patch("api.rag_engine.ChatGroq")
def test_rag_engine_init_and_query(mock_groq, mock_embeddings, mock_chroma, mock_loader):
    """Testa a inicialização e a execução da consulta da engine RAG utilizando mocks."""
    # Instancia o LegalRAGEngine com os componentes mockados
    engine = LegalRAGEngine(pdf_path="dummy/path/ctb.pdf")
    
    # Configura o retorno simulado da chain
    mock_chain = MagicMock()
    mock_chain.invoke.return_value = {"answer": "Resposta legal simulada", "context": []}
    engine.chain = mock_chain

    # Executa a busca
    result = engine.query("Qual o limite de velocidade?")
    
    assert result["answer"] == "Resposta legal simulada"
    mock_chain.invoke.assert_called_once()