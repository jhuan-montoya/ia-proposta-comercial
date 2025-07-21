
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
import logging
import core.logging_config
from core.ai_config_service import configure_ai

logger = logging.getLogger(__name__)
load_dotenv()

def analyze_proposal_with_prediction(text):
    """
    Orquestra a análise completa: extração e resumo.
    """
    # 1. Extrair dados brutos com a IA
    structured_data = extract_structured_data(text)
    if not structured_data:
        return None

    # 2. Gerar resumo final com IA
    summary = generate_summary(structured_data)

    # 3. Combinar todos os dados em um resultado final
    final_result = structured_data
    final_result['resumo_ia'] = summary
    
    return final_result

def extract_structured_data(text):
    """
    Usa o Gemini para extrair informações estruturadas do texto de uma proposta.
    """
    try:
        configure_ai()
        model = genai.GenerativeModel('gemini-1.5-flash')

        prompt = f"""
        Você é um assistente especialista em análise de propostas comerciais. Sua tarefa é extrair as seguintes informações do texto abaixo e retorná-las em formato JSON.

        Texto da Proposta:
        ---
        {text}
        ---

        Extraia os seguintes campos:
        - "nome_cliente": O nome da empresa ou pessoa para quem a proposta é destinada.
        - "valor_proposta": O valor total da proposta. Extraia apenas o número (float), sem símbolos de moeda. Se houver múltiplos valores, pegue o valor total.
        - "produto_servico": Uma breve descrição do principal produto ou serviço ofertado.
        - "proposal_type": A categoria da proposta. Use uma das seguintes tags: "Desenvolvimento de Software", "Consultoria", "Manutenção", "Licenciamento" ou "Outros".
        - "condicoes": Um resumo das principais condições, como prazos de entrega, validade da proposta ou formas de pagamento.

        Se uma informação não for encontrada, use o valor "N/A" para strings ou 0.0 para o valor.
        Responda APENAS com o objeto JSON, sem nenhum texto ou formatação adicional.
        """

        response = model.generate_content(prompt)
        json_response = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(json_response)
    except Exception as e:
        logger.error("Erro ao extrair dados com a IA.", exc_info=True)
        logger.debug(f"Resposta recebida da API que causou o erro: {response.text if 'response' in locals() else 'N/A'}")
        return None

def generate_summary(structured_data):
    """
    Usa o Gemini para gerar um resumo inteligente da proposta.
    """
    try:
        configure_ai()
        model = genai.GenerativeModel('gemini-1.5-flash')

        prompt = f"""
        Com base nos seguintes dados de uma proposta comercial, crie um resumo executivo para um gerente de vendas ocupado.
        O resumo deve ser conciso (3-4 frases), em português, e destacar os pontos mais importantes para uma tomada de decisão rápida.

        Dados da Proposta:
        - Cliente: {structured_data.get('nome_cliente', 'N/A')}
        - Valor: R$ {structured_data.get('valor_proposta', 0.0):.2f}
        - Produto/Serviço: {structured_data.get('produto_servico', 'N/A')}
        - Condições/Prazos: {structured_data.get('condicoes', 'N/A')}

        Seja direto e informativo.
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error("Erro ao gerar resumo com a IA.", exc_info=True)
        return "Não foi possível gerar o resumo."

