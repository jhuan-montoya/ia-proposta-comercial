import streamlit as st
import os
import sys
import time
from pathlib import Path

# Adiciona o diretório raiz do projeto ao sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.core import pdf_extractor
from src.core import proposal_processor as analysis_processor
from src.core import database_service as database
from src.core import notification_service as notifier

# --- Configuração da Página ---
st.set_page_config(
    page_title="Processar Nova Proposta",
    page_icon="📄",
    layout="centered"
)

st.title("📄 Processar Nova Proposta Comercial")
st.markdown("Faça o upload de um arquivo PDF de proposta para que a IA possa extrair, resumir e prever o status.")

# --- Função para processar o arquivo ---
def process_uploaded_proposal(uploaded_file):
    st.info(f"Processando o arquivo: {uploaded_file.name}...")
    
    # Salvar o arquivo temporariamente para que o PyMuPDF possa abri-lo
    temp_dir = Path("temp_uploads")
    temp_dir.mkdir(exist_ok=True)
    pdf_path = temp_dir / uploaded_file.name
    
    with open(pdf_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    try:
        # Etapa 1: Extrair texto
        with st.spinner("1/4 - Extraindo texto do PDF..."):
            text = pdf_extractor.extract_text_from_pdf(pdf_path)
            if not text or len(text) < 50:
                st.error("Falha ao extrair texto do PDF. O arquivo pode estar em branco, ser uma imagem ou corrompido.")
                return
        st.success("1/4 - Texto extraído com sucesso!")

        # Etapa 2: Extrair dados e gerar resumo
        with st.spinner("2/4 - Analisando e gerando resumo inteligente..."):
            structured_data = analysis_processor.extract_structured_data(text)
            if not structured_data:
                st.error("Falha ao extrair dados estruturados. Verifique o console para mais detalhes.")
                return
            
            summary = analysis_processor.generate_summary(structured_data)
            structured_data['resumo_ia'] = summary
            structured_data['nome_arquivo'] = uploaded_file.name
            
        st.success("2/4 - Dados extraídos e resumo gerado!")

        # Etapa 3: Prever aceitação
        with st.spinner("3/4 - Prevendo aceitação da proposta..."):
            prediction = analysis_processor.predict_acceptance(structured_data)
            structured_data['status'] = prediction # Atualiza o status com a previsão
        st.success("3/4 - Previsão de aceitação concluída!")

        # Etapa 4: Armazenar no banco de dados
        with st.spinner("4/4 - Salvando no banco de dados e enviando notificação..."):
            database.insert_proposal(structured_data)
            notifier.send_notification(structured_data)
        st.success("4/4 - Informações salvas e notificação enviada!")
        st.success("Proposta processada e registrada com sucesso!")

        st.subheader("Resultados da Análise:")
        st.write(f"**Cliente:** {structured_data.get('nome_cliente', 'N/A')}")
        st.write(f"**Valor da Proposta:** R$ {structured_data.get('valor_proposta', 0.0):,.2f}")
        st.write(f"**Produto/Serviço:** {structured_data.get('produto_servico', 'N/A')}")
        st.write(f"**Tipo de Proposta:** {structured_data.get('proposal_type', 'N/A')}")
        st.write(f"**Previsão de Status:** **{prediction.upper()}**")
        
        st.markdown("---")
        st.subheader("Resumo Gerado pela IA:")
        st.info(summary)

        with st.expander("Ver todos os dados extraídos (JSON)"):
            st.json(structured_data)

    except Exception as e:
        st.error(f"Ocorreu um erro inesperado durante o processamento: {e}")
        st.exception(e) # Exibe o traceback completo para depuração
    finally:
        # Limpa o arquivo temporário
        if pdf_path.exists():
            pdf_path.unlink()

# --- Interface do Usuário ---
uploaded_file = st.file_uploader("Selecione um arquivo PDF", type="pdf", help="Faça o upload de um arquivo PDF de proposta comercial para que a IA possa extrair e analisar os dados.")

if uploaded_file is not None:
    if st.button("Analisar Proposta", use_container_width=True):
        process_uploaded_proposal(uploaded_file)

# Inicializa o banco de dados na primeira execução
database.setup_database()
