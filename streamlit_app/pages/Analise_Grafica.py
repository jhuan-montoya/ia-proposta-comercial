import sys
import os

# Adiciona o diretório raiz do projeto ao sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import streamlit as st

import pandas as pd
from src.core.database_service import get_all_proposals_as_dataframe, update_proposal_status, get_proposal_details, update_proposal_details
import plotly.express as px

# --- Configuração da Página ---
st.set_page_config(
    page_title="Dashboard de Análise de Propostas",
    page_icon="📊",
    layout="wide"
)

# --- Funções de Callback ---
def refresh_data():
    """Recarrega os dados da sessão."""
    st.session_state.df_propostas = get_all_proposals_as_dataframe()

# --- Carregamento dos Dados ---
if 'df_propostas' not in st.session_state:
    st.session_state.df_propostas = get_all_proposals_as_dataframe()

df = st.session_state.df_propostas

# --- Título e Atualização ---
st.title("Análise Gráfica de Propostas")
st.button("Atualizar Dados", on_click=refresh_data)

# --- Sidebar de Filtros ---
st.sidebar.header("Filtros")
status_filter = st.sidebar.multiselect(
    "Filtrar por Status",
    options=df["status"].unique(),
    default=df["status"].unique()
)

client_filter = st.sidebar.multiselect(
    "Filtrar por Cliente",
    options=df["nome_cliente"].unique(),
    default=df["nome_cliente"].unique()
)

# Aplicar filtros
df_filtered = df[df["status"].isin(status_filter) & df["nome_cliente"].isin(client_filter)]

# --- KPIs ---
total_proposals = len(df_filtered)
total_value = df_filtered["valor_proposta"].sum()
acceptance_rate = (df_filtered[df_filtered["status"] == 'aceita'].shape[0] / total_proposals * 100) if total_proposals > 0 else 0

col1, col2, col3 = st.columns(3)
col1.metric("Total de Propostas", f"{total_proposals}")
col2.metric("Valor Total (R$)", f"{total_value:,.2f}")
col3.metric("Taxa de Aceitação", f"{acceptance_rate:.2f}%")

st.markdown("---")

# --- Gráficos ---
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.subheader("Propostas por Status")
    fig_status = px.pie(df_filtered, names='status', title='Distribuição de Status das Propostas', hole=.3)
    st.plotly_chart(fig_status, use_container_width=True)

with col_chart2:
    st.subheader("Valor por Cliente")
    df_client_value = df_filtered.groupby('nome_cliente')['valor_proposta'].sum().sort_values(ascending=False)
    fig_clients = px.bar(df_client_value, x=df_client_value.index, y='valor_proposta', title='Valor Total das Propostas por Cliente')
    st.plotly_chart(fig_clients, use_container_width=True)

# --- Tabela de Dados e Ações ---
st.markdown("---")

tab_table, tab_status, tab_edit = st.tabs(["Visualizar Tabela", "Atualizar Status", "Editar Detalhes"])

with tab_table:
    st.subheader("Detalhes das Propostas")
    # Criar uma cópia para exibição
    df_display = df_filtered.copy()
    # Selecionar colunas para exibir
    cols_to_display = ['id', 'nome_cliente', 'valor_proposta', 'produto_servico', 'status', 'data_processamento']
    st.dataframe(df_display[cols_to_display], use_container_width=True)

with tab_status:
    st.subheader("Atualizar Status da Proposta")
    col_update1, col_update2, col_update3 = st.columns([1, 2, 1])

    with col_update1:
        proposal_id_to_update = st.number_input("ID da Proposta", min_value=1, step=1, key="status_id_input")
    with col_update2:
        new_status = st.selectbox("Novo Status", options=['aceita', 'recusada', 'pendente'], key="new_status_select")
    with col_update3:
        st.write("") # Espaçador
        if st.button("Salvar Alteração de Status", key="save_status_button"):
            update_proposal_status(proposal_id_to_update, new_status)
            st.success(f"Status da proposta {proposal_id_to_update} atualizado para {new_status}!")
            refresh_data() # Recarrega os dados para refletir a mudança
            st.rerun()

with tab_edit:
    st.subheader("Editar Detalhes da Proposta")

    selected_id_edit = st.selectbox("Selecione o ID da Proposta para Editar", options=df_filtered['id'].unique(), key="edit_id_selector")

    if selected_id_edit:
        details_to_edit = get_proposal_details(selected_id_edit)
        if details_to_edit:
            with st.form(key=f"edit_form_{selected_id_edit}"):
                st.markdown(f"#### Editando Proposta: **{details_to_edit.get('nome_cliente', 'N/A')}** (ID: {selected_id_edit})")
                
                edited_nome_cliente = st.text_input("Nome do Cliente", value=details_to_edit.get('nome_cliente', ''), key=f"nome_cliente_{selected_id_edit}")
                edited_valor_proposta = st.number_input("Valor da Proposta (R$)", value=float(details_to_edit.get('valor_proposta', 0.0)), format="%.2f", key=f"valor_proposta_{selected_id_edit}")
                edited_produto_servico = st.text_input("Produto/Serviço", value=details_to_edit.get('produto_servico', ''), key=f"produto_servico_{selected_id_edit}")
                
                # Ensure the default value for selectbox is one of the options
                proposal_types = ["Desenvolvimento de Software", "Consultoria", "Manutenção", "Licenciamento", "Outros"]
                current_type = details_to_edit.get('proposal_type', 'Outros')
                if current_type not in proposal_types:
                    current_type = 'Outros' # Fallback if type is not in list
                edited_proposal_type = st.selectbox("Tipo de Proposta", options=proposal_types, index=proposal_types.index(current_type), key=f"proposal_type_{selected_id_edit}")
                
                edited_condicoes = st.text_area("Condições", value=details_to_edit.get('condicoes', ''), height=150, key=f"condicoes_{selected_id_edit}")
                edited_resumo_ia = st.text_area("Resumo IA", value=details_to_edit.get('resumo_ia', ''), height=200, key=f"resumo_ia_{selected_id_edit}")

                submit_edit_button = st.form_submit_button(label="Salvar Alterações dos Detalhes")

                if submit_edit_button:
                    updated_data = {
                        'nome_cliente': edited_nome_cliente,
                        'valor_proposta': edited_valor_proposta,
                        'produto_servico': edited_produto_servico,
                        'proposal_type': edited_proposal_type,
                        'condicoes': edited_condicoes,
                        'resumo_ia': edited_resumo_ia
                    }
                    update_proposal_details(selected_id_edit, updated_data)
                    st.success(f"Detalhes da proposta ID {selected_id_edit} atualizados com sucesso!")
                    refresh_data() # Recarrega os dados para refletir a mudança
                    st.rerun()
        else:
            st.warning("Não foi possível encontrar os detalhes para o ID selecionado para edição.")
