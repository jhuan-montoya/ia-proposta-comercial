
import fitz  # PyMuPDF
import logging
from . import logging_config

logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_path):
    """
    Extrai o texto de todas as páginas de um arquivo PDF.
    """
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        logger.error(f"Erro ao processar o PDF {pdf_path}", exc_info=True)
        return None

