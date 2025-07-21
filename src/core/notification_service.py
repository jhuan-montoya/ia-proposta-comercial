import os
import requests
from dotenv import load_dotenv
from urllib.parse import quote
import logging
import core.logging_config

logger = logging.getLogger(__name__)
load_dotenv()

def send_notification(data):
    """
    Prepara e envia a notificação para o WhatsApp.
    """
    whatsapp_api_key = os.getenv("WHATSAPP_API_KEY")
    whatsapp_phone_number = os.getenv("WHATSAPP_PHONE_NUMBER")

    if not whatsapp_api_key or not whatsapp_phone_number:
        logger.warning("Chaves de API ou número de telefone do WhatsApp não configurados no .env. Pulando notificação.")
        return

    resumo = data.get('resumo_ia', 'Resumo não disponível.')
    cliente = data.get('nome_cliente', 'N/A')
    valor = data.get('valor_proposta', 0.0)
    
    message = (
        f"🤖 *Nova Proposta Processada* 🤖\n\n"
        f"👤 *Cliente:* {cliente}\n"
        f"💰 *Valor:* R$ {valor:.2f}\n\n"
        f"📄 *Resumo Automático:*\n_{resumo}_"
    )
    
    send_whatsapp_message(whatsapp_api_key, whatsapp_phone_number, message)

def send_whatsapp_message(api_key, phone_number, text):
    """
    Envia uma mensagem de texto para um número do WhatsApp usando a API CallMeBot.
    """
    encoded_text = quote(text)
    url = f"https://api.callmebot.com/whatsapp.php?phone={phone_number}&text={encoded_text}&apikey={api_key}"
    
    logger.info(f"Enviando notificação para o WhatsApp número: {phone_number}")
    try:
        response = requests.get(url, verify=False)
        response.raise_for_status()
        
        if "ERROR" in response.text.upper():
             logger.error(f"Erro retornado pela API CallMeBot: {response.text}")
        else:
             logger.info("Notificação enviada para o WhatsApp com sucesso.")

    except requests.exceptions.RequestException as e:
        logger.error("Erro ao conectar com a API do CallMeBot.", exc_info=True)
