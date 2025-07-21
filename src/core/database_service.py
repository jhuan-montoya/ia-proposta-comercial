import sqlite3
import pandas as pd
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

DB_NAME = "data/propostas.db"

def setup_database():
    """Configura o banco de dados SQLite, criando a tabela se não existir."""
    Path("data").mkdir(parents=True, exist_ok=True) # Garante que a pasta 'data' existe
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS propostas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome_cliente TEXT NOT NULL,
                valor_proposta REAL,
                produto_servico TEXT,
                proposal_type TEXT,
                condicoes TEXT,
                resumo_ia TEXT,
                analise_preditiva TEXT,
                nome_arquivo TEXT,
                data_processamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        logger.info("Banco de dados configurado e tabela 'propostas' verificada/criada.")
    except sqlite3.Error as e:
        logger.error(f"Erro ao configurar o banco de dados: {e}", exc_info=True)
    finally:
        if conn:
            conn.close()

def insert_proposal(data):
    """Insere uma nova proposta no banco de dados."""
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO propostas (nome_cliente, valor_proposta, produto_servico, proposal_type, condicoes, resumo_ia, analise_preditiva, nome_arquivo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('nome_cliente'),
            data.get('valor_proposta'),
            data.get('produto_servico'),
            data.get('proposal_type'),
            data.get('condicoes'),
            data.get('resumo_ia'),
            str(data.get('analise_preditiva')), # Armazenar como string JSON
            data.get('nome_arquivo')
        ))
        conn.commit()
        logger.info(f"Proposta para '{data.get('nome_cliente')}' inserida com sucesso.")
    except sqlite3.Error as e:
        logger.error(f"Erro ao inserir proposta: {e}", exc_info=True)
    finally:
        if conn:
            conn.close()

def get_training_data():
    """
    Busca todas as propostas com status 'aceita' ou 'recusada' para usar como
    dados de treinamento para o modelo preditivo.
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        query = "SELECT * FROM propostas WHERE status IN ('aceita', 'recusada')"
        df = pd.read_sql_query(query, conn)
        conn.close()
        logger.info(f"Buscados {len(df)} registros para treinamento.")
        return df
    except Exception as e:
        logger.error("Falha ao buscar dados de treinamento do banco.", exc_info=True)
        return pd.DataFrame()

def get_all_proposals_as_dataframe():
    """
    Busca todas as propostas no banco de dados e retorna como um DataFrame do pandas.
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        df = pd.read_sql_query("SELECT * FROM propostas", conn)
        logger.info(f"Buscados {len(df)} registros de propostas.")
        return df
    except sqlite3.Error as e:
        logger.error(f"Erro ao buscar todas as propostas como DataFrame: {e}", exc_info=True)
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()

def update_proposal_status(proposal_id, new_status):
    """
    Atualiza o status de uma proposta no banco de dados.
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE propostas
            SET status = ?
            WHERE id = ?
        """, (new_status, proposal_id))
        conn.commit()
        logger.info(f"Status da proposta ID {proposal_id} atualizado para '{new_status}'.")
    except sqlite3.Error as e:
        logger.error(f"Erro ao atualizar status da proposta ID {proposal_id}: {e}", exc_info=True)
    finally:
        if conn:
            conn.close()

def update_proposal_details(proposal_id, new_data):
    """
    Atualiza os detalhes de uma proposta no banco de dados.
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Construir a query de forma dinâmica para atualizar apenas os campos fornecidos
        set_clauses = []
        values = []
        for key, value in new_data.items():
            if key in ['nome_cliente', 'valor_proposta', 'produto_servico', 'proposal_type', 'condicoes', 'resumo_ia', 'analise_preditiva']: # Adicione todos os campos que podem ser atualizados
                set_clauses.append(f"{key} = ?")
                values.append(value)
        
        if not set_clauses:
            logger.warning(f"Nenhum campo válido fornecido para atualização da proposta ID {proposal_id}.")
            return

        query = f"UPDATE propostas SET {', '.join(set_clauses)} WHERE id = ?"
        values.append(proposal_id)

        cursor.execute(query, tuple(values))
        conn.commit()
        logger.info(f"Detalhes da proposta ID {proposal_id} atualizados com sucesso.")
    except sqlite3.Error as e:
        logger.error(f"Erro ao atualizar detalhes da proposta ID {proposal_id}: {e}", exc_info=True)
    finally:
        if conn:
            conn.close()

def get_proposal_details(proposal_id):
    """
    Busca os detalhes completos de uma proposta específica.
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row # Permite acessar colunas pelo nome
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM propostas WHERE id = ?", (proposal_id,))
        details = cursor.fetchone()
        return dict(details) if details else None
    except sqlite3.Error as e:
        logger.error(f"Erro ao buscar detalhes da proposta: {e}", exc_info=True)
        return None
    finally:
        if conn:
            conn.close()
