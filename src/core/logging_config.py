
import logging
import sys

def setup_logging():
    """Configura o logging para salvar em arquivo, em vez de no console."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] [%(name)s] - %(message)s",
        handlers=[
            logging.FileHandler("app.log", mode='a', encoding='utf-8')
        ]
    )

# Configura o logging assim que este módulo for importado
setup_logging()
