
# MLOps: Assistente Jurídico com RAG e Monitoramento (SRE)

Este projeto demonstra o ciclo de vida completo de uma aplicação de Inteligência Artificial baseada em LLMs, unindo conceitos de **Engenharia de IA, DevOps e Site Reliability Engineering (SRE)**. 

O sistema é um Assistente Jurídico (baseado em arquitetura RAG) desenhado para estar sempre disponível, ser facilmente implantado e totalmente monitorado.

---

## 🏛️ Arquitetura do Projeto

O ecossistema é dividido em 3 pilares principais:

### 1. O Core (Inteligência Artificial & Dados)
*   **Aplicação:** API desenvolvida em `FastAPI` (Python).
*   **Pipeline de IA:** Integração com `LangChain` para orquestração de LLMs e construção da arquitetura **RAG** (Retrieval-Augmented Generation).
*   **Caso de Uso:** O assistente recebe perguntas jurídicas, busca contexto em uma base de dados vetorizada (ex: leis, jurisprudências) e gera respostas precisas, mitigando alucinações.

### 2. A Esteira (Engenharia DevOps & CI/CD)
*   **Conteinerização:** A aplicação inteira roda em `Docker`, garantindo que o ambiente de desenvolvimento seja idêntico ao de produção.
*   **CI/CD:** Pipeline estruturado no `GitHub Actions`. Cada novo *commit* na *branch main* aciona rotinas de testes automatizados e o *build* da imagem Docker da API.
*   **Infraestrutura:** Preparado para orquestração em nuvem (ex: deploy em instâncias AWS EC2 ou cluster Kubernetes).

### 3. A Observabilidade (Site Reliability Engineering - SRE)
*   **Métricas (Prometheus):** A API exporta métricas em tempo real sobre a saúde do sistema de IA, como contagem total de requisições (`legal_queries_total`) e latência do LLM/RAG (`legal_query_latency_seconds`).
*   **Dashboards (Grafana):** Painel visual para monitoramento contínuo. Permite acompanhar se os tempos de resposta da IA estão dentro dos SLAs (Acordos de Nível de Serviço) esperados e detectar gargalos na integração com o banco vetorial ou API da OpenAI.

---

## 🚀 Como Executar Localmente

Você pode rodar todo o ecossistema (API + Prometheus + Grafana) localmente usando o Docker Compose.

```bash
# Clone o repositório
git clone https://github.com/SEU-USUARIO/mlops-legal-assistant.git
cd mlops-legal-assistant

# Suba os containers
docker-compose up --build
```

**Serviços Disponíveis:**
*   API (FastAPI): `http://localhost:8000/docs` (Swagger UI para testar o assistente)
*   Métricas expostas: `http://localhost:8000/metrics`
*   Prometheus: `http://localhost:9090`
*   Grafana: `http://localhost:3000`

---

## 🤝 Por que este projeto?
Este repositório foi criado para demonstrar que o desenvolvimento de IA não termina quando o script funciona no Jupyter Notebook. Ele engloba a capacidade de colocar modelos de linguagem em produção de forma sustentável, automatizada (DevOps) e confiável (SRE).
