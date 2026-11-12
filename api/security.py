# api/security.py
import os
import re
import secrets
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

# Padrões comuns de Prompt Injection / Jailbreak
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"ignore\s+(todas\s+)?(as\s+)?instru[çc][õo]es\s+anteriores",
    r"system\s+prompt",
    r"forget\s+your\s+rules",
    r"esque[çc]a\s+suas\s+regras",
    r"aja\s+como\s+(um|uma)\s+(?!especialista\s+em\s+tr[âa]nsito)",
    r"act\s+as\s+",
    r"jailbreak",
    r"bypass",
]

# Vocabulário base do domínio de trânsito brasileiro (CTB)
TRAFFIC_DOMAIN_KEYWORDS = {
    "trânsito", "transito", "ctb", "veículo", "veiculo", "veículos", "veiculos",
    "carro", "moto", "motocicleta", "caminhão", "caminhao", "ônibus", "onibus",
    "bicicleta", "ciclista", "pedestre", "condutor", "motorista", "habilitação",
    "habilitacao", "cnh", "carteira", "permissão", "permissao", "ppd", "acc",
    "multa", "infração", "infracao", "penalidade", "pontos", "pontuação",
    "suspensão", "suspensao", "cassação", "cassacao", "recurso", "autuação",
    "via", "rodovia", "estrada", "avenida", "rua", "cruzamento", "rotatória",
    "semáforo", "semaforo", "placa", "sinalização", "sinalizacao", "faixa",
    "velocidade", "radar", "ultrapassagem", "estacionamento", "parada",
    "álcool", "alcool", "bafômetro", "bafometro", "etilômetro", "lei seca",
    "detran", "contran", "denatran", "senatran", "prf", "cet", "jari",
    "acidente", "sinistro", "colisão", "colisao", "atropelamento", "socorro",
    "capacete", "cinto", "cadeirinha", "farol", "luz", "buzina", "pneu",
    "licenciamento", "ipva", "crlv", "crv", "dpvat", "categoria", "classificação",
    "classificacao", "artigo", "art.", "lei 9.503", "9503"
}


def verify_api_key(api_key: str = Security(API_KEY_HEADER)) -> str:
    """Valida o header X-API-Key contra a variável de ambiente API_KEY."""
    expected_key = os.getenv("API_KEY")

    if not expected_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Configuração de autenticação ausente no servidor."
        )

    if not api_key or not secrets.compare_digest(api_key, expected_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credencial de acesso inválida ou ausente."
        )

    return api_key


def validate_traffic_guardrail(question: str) -> str:
    """Valida tamanho, bloqueia prompt injection e garante aderência ao domínio do CTB."""
    cleaned = question.strip()

    if len(cleaned) < 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Por favor, formule uma pergunta mais detalhada sobre o Código de Trânsito Brasileiro."
        )

    if len(cleaned) > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A pergunta excede o limite máximo permitido de 1000 caracteres."
        )

    lower_text = cleaned.lower()

    # 1. Bloqueio de Prompt Injection
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, lower_text):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sua consulta contém padrões não permitidos. Faça uma pergunta objetiva sobre legislação de trânsito."
            )

    # 2. Filtro de Domínio (CTB)
    tokens = set(re.findall(r"\w+", lower_text))
    has_domain_match = bool(tokens.intersection(TRAFFIC_DOMAIN_KEYWORDS)) or any(
        kw in lower_text for kw in ("lei seca", "lei 9.503", "art.")
    )

    if not has_domain_match:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sou um assistente especializado exclusivamente no Código de Trânsito Brasileiro (CTB). Por favor, faça perguntas sobre leis de trânsito, infrações, veículos ou habilitação."
        )

    return cleaned