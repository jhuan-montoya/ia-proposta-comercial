import os
import requests
from dotenv import load_dotenv
from urllib.parse import quote
import logging
from . import logging_config

logger = logging.getLogger(__name__)
load_dotenv()

def send_notification(data, whatsapp_phone_number=None, whatsapp_api_key=None):
    """
    Prepara e envia a notificação para o WhatsApp.
    """
    # Prioriza os parâmetros passados, senão usa as variáveis de ambiente
    phone_to_use = whatsapp_phone_number if whatsapp_phone_number else os.getenv("WHATSAPP_PHONE_NUMBER")
    api_key_to_use = whatsapp_api_key if whatsapp_api_key else os.getenv("WHATSAPP_API_KEY")

    if not api_key_to_use or not phone_to_use:
        logger.warning("Chaves de API ou número de telefone do WhatsApp não configurados. Pulando notificação.")
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
    
    send_whatsapp_message(api_key_to_use, phone_to_use, message)

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
