import os
import google.generativeai as genai
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)
load_dotenv()

def configure_ai():
    """Configura a API do Google AI com a chave do .env."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.error("A chave da API do Google não foi encontrada. Verifique seu arquivo .env.")
        raise ValueError("A chave da API do Google não foi encontrada. Verifique seu arquivo .env.")
    genai.configure(api_key=api_key)
