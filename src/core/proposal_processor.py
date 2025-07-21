
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
import logging
from . import logging_config
from .ai_config_service import configure_ai

logger = logging.getLogger(__name__)
load_dotenv()

def analyze_proposal(text):
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

def predict_acceptance(structured_data):
    """
    Usa o Gemini para prever se a proposta será aceita, recusada ou pendente.
    """
    try:
        configure_ai()
        model = genai.GenerativeModel('gemini-1.5-flash')

        prompt = f"""
        Com base nos seguintes dados de uma proposta comercial, preveja se ela será 'aceita', 'recusada' ou 'pendente'.
        Considere o cliente, o valor, o tipo de proposta e as condições.
        Responda APENAS com uma das palavras: 'aceita', 'recusada' ou 'pendente'.

        Dados da Proposta:
        - Cliente: {structured_data.get('nome_cliente', 'N/A')}
        - Valor: R$ {structured_data.get('valor_proposta', 0.0):.2f}
        - Produto/Serviço: {structured_data.get('produto_servico', 'N/A')}
        - Tipo de Proposta: {structured_data.get('proposal_type', 'N/A')}
        - Condições: {structured_data.get('condicoes', 'N/A')}
        """
        response = model.generate_content(prompt)
        prediction = response.text.strip().lower()
        if prediction in ['aceita', 'recusada', 'pendente']:
            logger.info(f"Previsão de aceitação gerada: {prediction}")
            return prediction
        else:
            logger.warning(f"Previsão inesperada da IA: {prediction}. Retornando 'pendente'.")
            return "pendente"
    except Exception as e:
        logger.error(f"Erro ao prever aceitação com a IA: {e}", exc_info=True)
        return "pendente"

def summarize_pending_proposals(proposals_df):
    """
    Usa o Gemini para gerar um resumo das propostas pendentes.
    Recebe um DataFrame de propostas pendentes.
    """
    if proposals_df.empty:
        return "Não há propostas pendentes no momento."

    model = genai.GenerativeModel('gemini-1.5-flash')

    # Constrói uma string com os dados das propostas pendentes
    proposals_text = ""
    for index, row in proposals_df.iterrows():
        proposals_text += f"- Cliente: {row.get('nome_cliente', 'N/A')}, Valor: R$ {row.get('valor_proposta', 0.0):.2f}, Produto: {row.get('produto_servico', 'N/A')}, Status: {row.get('status', 'N/A')}\n"

    prompt = f"""
    Com base na lista de propostas pendentes abaixo, crie um resumo conciso (máximo 100 palavras)
    destacando o número total de propostas pendentes, o valor total envolvido e os principais clientes ou produtos/serviços.

    Propostas Pendentes:
    ---
    {proposals_text}
    ---

    Seja direto e informativo.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Erro ao gerar resumo de propostas pendentes com a IA: {e}", exc_info=True)
        return "Não foi possível gerar o resumo das propostas pendentes."

