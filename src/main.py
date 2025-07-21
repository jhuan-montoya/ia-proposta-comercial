import os
import shutil
import time
from pathlib import Path
import logging
from core import logging_config

from core import database_service as database
from core import pdf_extractor
from core import proposal_processor as analysis_processor
from core import notification_service as notifier

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_DIR = BASE_DIR / "propostas_a_processar"
PROCESSED_DIR = BASE_DIR / "propostas_processadas"
POLL_INTERVAL = 10

def main():
    """Função principal que orquestra o pipeline de processamento de propostas."""
    logger.info("Iniciando o serviço de monitoramento de propostas...")
    
    database.setup_database()
    INPUT_DIR.mkdir(exist_ok=True)
    PROCESSED_DIR.mkdir(exist_ok=True)

    logger.info(f"Monitorando a pasta: '{INPUT_DIR.resolve()}'")

    while True:
        try:
            files_to_process = list(INPUT_DIR.glob("*.pdf"))
            
            if not files_to_process:
                time.sleep(POLL_INTERVAL)
                continue

            for pdf_path in files_to_process:
                logger.info(f"--- Nova proposta encontrada: {pdf_path.name} ---")
                
                try:
                    logger.info("1. Extraindo texto do PDF...")
                    text = pdf_extractor.extract_text_from_pdf(pdf_path)
                    if not text or len(text) < 50:
                        logger.warning("Falha: Texto não extraído ou muito curto. Pulando arquivo.")
                        move_file_to_processed(pdf_path, success=False)
                        continue

                    logger.info("2. Analisando para extrair dados...")
                    structured_data = analysis_processor.extract_structured_data(text)
                    if not structured_data:
                        logger.warning("Falha: Não foi possível extrair dados estruturados. Pulando arquivo.")
                        move_file_to_processed(pdf_path, success=False)
                        continue
                    
                    structured_data['nome_arquivo'] = pdf_path.name
                    logger.info(f"Dados extraídos: Cliente: {structured_data.get('nome_cliente')}, Valor: {structured_data.get('valor_proposta')}")

                    logger.info("3. Gerando resumo automático...")
                    summary = analysis_processor.generate_summary(structured_data)
                    structured_data['resumo_ia'] = summary
                    logger.info("Resumo gerado com sucesso.")

                    logger.info("4. Salvando no banco de dados...")
                    database.insert_proposal(structured_data)

                    logger.info("5. Enviando notificação...")
                    notifier.send_notification(structured_data)

                    move_file_to_processed(pdf_path, success=True)
                    logger.info(f"--- Processamento de {pdf_path.name} concluído com sucesso! ---")

                except Exception as e:
                    logger.error(f"Erro inesperado ao processar {pdf_path.name}.", exc_info=True)
                    move_file_to_processed(pdf_path, success=False)
            
            logger.info(f"Ciclo concluído. Aguardando novos arquivos...")

        except KeyboardInterrupt:
            logger.info("Serviço de monitoramento interrompido pelo usuário.")
            break
        except Exception as e:
            logger.critical("Um erro crítico ocorreu no loop principal do monitor.", exc_info=True)
            time.sleep(POLL_INTERVAL * 2) # Espera um pouco mais antes de tentar de novo

def move_file_to_processed(file_path, success=True):
    """Move o arquivo para a pasta de processados ou de erro."""
    try:
        if success:
            destination = PROCESSED_DIR / file_path.name
        else:
            error_dir = PROCESSED_DIR / "com_erro"
            error_dir.mkdir(exist_ok=True)
            destination = error_dir / file_path.name
            
        shutil.move(file_path, destination)
        status = "sucesso" if success else "erro"
        logger.info(f"Arquivo movido para a pasta de processados ({status}).")
    except Exception as e:
        logger.error(f"Falha ao mover o arquivo {file_path.name}", exc_info=True)

if __name__ == "__main__":
    main()
