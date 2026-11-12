# tests/conftest.py
import os

os.environ.setdefault("GROQ_API_KEY", "test_groq_key")
os.environ.setdefault("API_KEY", "test_key_for_ci")