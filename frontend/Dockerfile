FROM python:3.10-slim

# Evita a gravação de arquivos .pyc e força o stdout em buffer direto
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instala as dependências copiando primeiro apenas o arquivo de requisitos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia explicitamente apenas os arquivos necessários da aplicação
COPY app.py .

# Cria e alterna para um usuário sem privilégios de root por segurança
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]