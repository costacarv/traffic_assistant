# api/rag_engine.py
from dotenv import load_dotenv
import os

import time
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.globals import set_verbose

# Ativa os logs detalhados do LangChain
set_verbose(True)
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

class LegalRAGEngine:
    def __init__(self, pdf_path: str = None):
        self.pdf_path = pdf_path
        self.chain = None
        if self.pdf_path:
            self._setup_rag()

    def _setup_rag(self):
        # 1. Carrega o documento jurídico (ex: Código Civil ou contrato)
        loader = PyPDFLoader(self.pdf_path)
        docs = loader.load()

        # 2. Divide em pedaços (chunks)
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = text_splitter.split_documents(docs)

        embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
        # Dica para português: "neuralmind/bert-base-portuguese-cased"
            )

        # 3. Cria o Vector Store
        vectorstore = Chroma.from_documents(documents=splits, embedding=embeddings)
        retriever = vectorstore.as_retriever()

        # 4. Configura o LLM e o Prompt Jurídico
        llm = ChatGroq(
            model="openai/gpt-oss-120b", # Você também pode usar "llama-3.1-8b-instant"
            temperature=0.2,
            api_key=groq_api_key
            )
        
        system_prompt = (
            "Você é um assistente especialista no código de trânsito brasileiro. "
            "Use os seguintes trechos de contexto recuperados para responder à pergunta. "
            "Se você não souber a resposta, diga que não sabe com base nos documentos.\n\n"
            "{context}"
        )
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
        ])

        # 5. Constrói o Chain final de RAG
        question_answer_chain = create_stuff_documents_chain(llm, prompt)
        self.chain = create_retrieval_chain(retriever, question_answer_chain)

    def query(self, question: str):
        if not self.chain:
            return {"answer": "Engine não inicializada.", "source_documents": []}
        
        # Invoca a chain RAG
        response = self.chain.invoke({"input": question})
        
        # Extrai os documentos recuperados do ChromaDB
        raw_docs = response.get("context", [])
        source_docs = []
        for doc in raw_docs:
            source_docs.append({
                "page_content": getattr(doc, "page_content", str(doc)),
                "metadata": getattr(doc, "metadata", {})
            })
        
        return {
            "answer": response.get("answer", ""),
            "source_documents": source_docs
        }