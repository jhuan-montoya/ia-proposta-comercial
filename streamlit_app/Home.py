
import sys
import os

# Adiciona o diretório raiz do projeto ao sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import streamlit as st
import pandas as pd

from src.core import database_service as database
from src.core import proposal_processor as analysis_processor

database.setup_database()

DB_PATH = "src/app/data/propostas.db"

def get_all_proposals():
    """Busca todas as propostas do banco de dados e retorna como um DataFrame."""
    return database.get_all_proposals_as_dataframe()


# --- Configuração da Página Streamlit ---
st.set_page_config(page_title="Dashboard de Propostas", layout="wide", initial_sidebar_state="expanded")

with st.sidebar:
    st.header("⚙️ Configurações de Notificação WhatsApp")
    st.markdown("Configure o número de telefone e a API Key do WhatsApp para receber notificações.")

    # Inicializa session_state para as configurações do WhatsApp
    if 'whatsapp_phone_number' not in st.session_state:
        st.session_state.whatsapp_phone_number = os.getenv("WHATSAPP_PHONE_NUMBER", "")
    if 'whatsapp_api_key' not in st.session_state:
        st.session_state.whatsapp_api_key = os.getenv("WHATSAPP_API_KEY", "")

    whatsapp_phone_input = st.text_input(
        "Número de Telefone WhatsApp (com código do país, ex: 5511999998888)",
        value=st.session_state.whatsapp_phone_number,
        key="whatsapp_phone_input"
    )
    whatsapp_api_key_input = st.text_input(
        "API Key do WhatsApp (recebida do CallMeBot)",
        value=st.session_state.whatsapp_api_key,
        type="password", # Para esconder a chave
        key="whatsapp_api_key_input"
    )

    if st.button("Salvar Configurações WhatsApp", key="save_whatsapp_config_button"):
        st.session_state.whatsapp_phone_number = whatsapp_phone_input
        st.session_state.whatsapp_api_key = whatsapp_api_key_input
        st.success("Configurações do WhatsApp salvas na sessão!")

    st.markdown("---")
    st.markdown("""
    **Como obter sua API Key do CallMeBot:**
    1. Adicione o número `+34 644 94 21 74` aos seus contatos.
    2. Envie a mensagem `I allow callmebot to send me messages` para ele.
    3. Você receberá sua `APIKEY` como resposta.
    """)


st.title("Dashboard de Análise de Propostas Comerciais")
st.markdown("Visualize propostas processadas ou envie um novo PDF para análise.")

# --- Aviso de Propostas Pendentes (IA) ---
st.subheader("Status das Propostas Pendentes")
pending_proposals_df = database.get_all_proposals_as_dataframe()
pending_proposals_df = pending_proposals_df[pending_proposals_df['status'] == 'pendente']

if not pending_proposals_df.empty:
    st.warning(f"Você tem {len(pending_proposals_df)} proposta(s) pendente(s) de análise!")
else:
    st.success("🎉 Nenhuma proposta pendente no momento. Tudo em dia!")

st.markdown("---")

# --- Seções com Abas ---
tab1 = st.tabs(["Histórico de Propostas"])

with tab1[0]:
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
