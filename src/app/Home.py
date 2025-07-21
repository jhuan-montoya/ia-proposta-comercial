
import sys
import os
import streamlit as st

# Adiciona o diretório 'src' ao sys.path para encontrar os módulos 'core' e 'ml'
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import pandas as pd
import sqlite3
from pathlib import Path
import time

from core import database_service as database
from core import pdf_extractor
from core import proposal_processor as analysis_processor
from core import notification_service as notifier

DB_PATH = "data/propostas.db"

def get_all_proposals():
    """Busca todas as propostas do banco de dados e retorna como um DataFrame."""
    return database.get_all_proposals_as_dataframe()

def process_new_proposal(uploaded_file):
    """
    Processa um novo arquivo PDF enviado pelo usuário.
    Esta função replica a lógica do `main.py` para um único arquivo.
    """
    st.info(f"Processando o arquivo: {uploaded_file.name}...")
    
    # Salvar o arquivo temporariamente para que o PyMuPDF possa abri-lo
    temp_dir = Path("temp_uploads")
    temp_dir.mkdir(exist_ok=True)
    pdf_path = temp_dir / uploaded_file.name
    
    with open(pdf_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    try:
        # Etapa 1: Extrair texto
        with st.spinner("1/5 - Extraindo texto do PDF..."):
            text = pdf_extractor.extract_text_from_pdf(pdf_path)
            if not text or len(text) < 50:
                st.error("Falha ao extrair texto do PDF. O arquivo pode estar em branco, ser uma imagem ou corrompido.")
                return
        st.success("1/5 - Texto extraído com sucesso!")

        # Etapa 2: Extrair dados com o assistente
        with st.spinner("2/5 - Analisando para extrair dados..."):
            structured_data = analysis_processor.extract_structured_data(text)
            if not structured_data:
                st.error("Falha ao extrair dados estruturados. Verifique o console para mais detalhes.")
                return
        structured_data['nome_arquivo'] = uploaded_file.name
        st.success("2/5 - Dados extraídos!")

        # Etapa 3: Gerar resumo automático
        with st.spinner("3/5 - Gerando resumo inteligente..."):
            summary = analysis_processor.generate_summary(structured_data)
            structured_data['resumo_ia'] = summary
        st.success("3/5 - Resumo gerado!")

        # Etapa 4: Armazenar no banco de dados
        with st.spinner("4/5 - Salvando no banco de dados..."):
            database.insert_proposal(structured_data)
        st.success("4/5 - Informações salvas no banco de dados!")

        # Etapa 5: Enviar notificação
        with st.spinner("5/5 - Enviando notificação..."):
            time.sleep(1) # Pequena pausa para dar sensação de trabalho
            notifier.send_notification(structured_data)
        st.success("5/5 - Notificação enviada!")
        st.success("Proposta processada e registrada com sucesso!")

    except Exception as e:
        st.error(f"Ocorreu um erro inesperado durante o processamento: {e}")
    finally:
        # Limpa o arquivo temporário
        if pdf_path.exists():
            pdf_path.unlink()


# --- Configuração da Página Streamlit ---
st.set_page_config(page_title="Dashboard de Propostas", layout="wide", initial_sidebar_state="expanded")

with st.sidebar:
    st.header("⚙️ Conectar WhatsApp")
    st.markdown("""
    Para receber as notificações das propostas diretamente no seu WhatsApp, siga os 3 passos abaixo (leva menos de 1 minuto!):
    """)

    st.markdown("""
    **1. Adicione o Contato do Bot**
    Adicione o número `+34 644 94 21 74` aos seus contatos do celular. Você pode nomeá-lo como `Assistente IA`.
    """)

    st.markdown("""
    **2. Ative o Bot**
    Envie a seguinte mensagem (exatamente como está escrita) para o contato que você acabou de salvar:
    `I allow callmebot to send me messages`
    """)

    st.markdown("""
    **3. Configure sua API Key**
    Você receberá uma `APIKEY` como resposta. Crie ou edite o arquivo `.env` na pasta do projeto e adicione sua chave e número de telefone:
    """)

    st.code("""
# Arquivo .env
GOOGLE_API_KEY="SUA_CHAVE_GEMINI_AQUI"
WHATSAPP_PHONE_NUMBER="SEU_NUMERO_COM_CODIGO_DO_PAIS"
WHATSAPP_API_KEY="SUA_APIKEY_RECEBIDA_DO_BOT"
    """, language="bash")
    
    st.warning("Lembre-se de incluir o código do país no seu número (ex: 5511999998888 para o Brasil).")


st.title("Dashboard de Análise de Propostas Comerciais")
st.markdown("Visualize propostas processadas ou envie um novo PDF para análise.")

# --- Seções com Abas ---
tab1, tab2 = st.tabs(["Processar Nova Proposta", "Histórico de Propostas"])

with tab1:
    st.header("Envie um Novo PDF para Análise")
    uploaded_file = st.file_uploader("Selecione um arquivo PDF", type="pdf", help="Faça o upload de um arquivo PDF de proposta comercial para que a IA possa extrair e analisar os dados.")

    if uploaded_file is not None:
        if st.button("Analisar Proposta", use_container_width=True):
            process_new_proposal(uploaded_file)

with tab2:
    st.header("Histórico de Propostas Processadas")
    st.markdown("Aqui você pode visualizar todas as propostas que já foram processadas.")

    if st.button("Atualizar Lista de Propostas", key="refresh_home_proposals"):
        st.rerun()

    proposals_df = get_all_proposals()

    if proposals_df.empty:
        st.info("Nenhuma proposta processada ainda. Envie um arquivo na aba 'Processar Nova Proposta' para começar.")
    else:
        st.dataframe(proposals_df, use_container_width=True)

        st.subheader("Detalhes da Proposta Selecionada")
        selected_id = st.selectbox("Selecione o ID da Proposta para ver detalhes", options=proposals_df['id'].unique(), key="home_details_selector")

        if selected_id:
            details = database.get_proposal_details(selected_id)
            if details:
                st.markdown(f"#### Resumo da Proposta: **{details['nome_cliente']}**")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(label="Valor da Proposta", value=f"R$ {details['valor_proposta']:.2f}")
                with col2:
                    st.metric(label="Data do Processamento", value=pd.to_datetime(details['data_processamento']).strftime('%d/%m/%Y %H:%M'))

                st.metric(label="Tipo de Proposta", value=details.get('proposal_type', 'N/A'))

                st.markdown("##### Resumo Automático Gerado pela IA")
                st.info(details['resumo_ia'])

                with st.expander("Ver todos os dados extraídos (JSON)"):
                    st.json(details)
            else:
                st.warning("Não foi possível encontrar os detalhes para o ID selecionado.")

# Inicializa o banco de dados na primeira execução
database.setup_database()
