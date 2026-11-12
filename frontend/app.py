# frontend/app.py
import streamlit as st
import requests
import os
import logging

# Log para análise de SRE/DevOps no container
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Assistente Jurídico CTB",
    page_icon="⚖️",
    layout="centered"
)

st.title("⚖️ Assistente Jurídico - Código de Trânsito Brasileiro")
st.subheader("Consultas inteligentes baseadas em RAG com monitoramento SRE")

API_URL = os.getenv("API_URL", "http://localhost:8000")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Exibe o histórico de mensagens
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sources" in message and message["sources"]:
            with st.expander("📚 Ver trechos do CTB consultados no ChromaDB"):
                for idx, doc in enumerate(message["sources"], 1):
                    page = doc.get("metadata", {}).get("page", "N/A")
                    st.write(f"**Trecho {idx} (Página {page}):**")
                    st.info(doc.get("page_content", ""))

# Entrada do usuário
if prompt := st.chat_input("Pergunte algo sobre o Código de Trânsito..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Buscando na legislação e processando via Groq..."):
            try:
                response = requests.post(
                    f"{API_URL}/ask",
                    json={"question": prompt},
                    timeout=30
                )

                if response.status_code == 200:
                    data = response.json()
                    
                    answer = data.get("answer", "Sem resposta da API.")
                    if isinstance(answer, dict):
                        answer = answer.get("answer", str(answer))
                        
                    sources = data.get("source_documents", [])

                    st.markdown(answer)

                    if sources:
                        with st.expander("📚 Ver trechos do CTB consultados no ChromaDB"):
                            for idx, doc in enumerate(sources, 1):
                                page = doc.get("metadata", {}).get("page", "N/A")
                                st.write(f"**Trecho {idx} (Página {page}):**")
                                st.info(doc.get("page_content", ""))

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "sources": sources
                    })
                else:
                    logger.error(f"Erro HTTP {response.status_code} na API: {response.text}")
                    st.error("⚠️ Ocorreu uma falha temporária ao processar sua consulta. Por favor, tente novamente.")

            except requests.exceptions.ConnectionError as e:
                logger.error(f"Erro de Conexão com a API ({API_URL}): {e}")
                st.error("⚠️ O serviço de inteligência está temporariamente indisponível ou inicializando. Tente novamente em instantes.")

            except requests.exceptions.Timeout as e:
                logger.warning(f"Timeout na requisição para a API: {e}")
                st.error("⏱️ A consulta demorou mais do que o esperado. Por favor, tente refazer a pergunta.")

            except requests.exceptions.RequestException as e:
                logger.error(f"Erro na requisição HTTP: {e}")
                st.error("⚠️ Não foi possível comunicar com o servidor no momento.")