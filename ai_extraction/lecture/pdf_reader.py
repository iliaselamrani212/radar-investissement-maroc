"""
lecture/pdf_reader.py - Fonctionnalité 2 : Lecture intelligente PDF
Avec fallback OCR pour les PDFs scannés (Bulletin Officiel, etc.)
"""
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def extraire_texte_pdf(pdf_path: str, ocr_si_vide: bool = True) -> str:
    """
    Extraction intelligente de texte depuis PDF.
    - Essaye pdfplumber d'abord (rapide, précis)
    - Fallback OCR si page vide (PDF scanné)
    """
    try:
        import pdfplumber
    except ImportError:
        logger.error("pdfplumber non installé. pip install pdfplumber")
        return ""

    texte = ""
    nb_pages_ocr = 0

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                texte_page = page.extract_text() or ""

                # Fallback OCR si page vide
                if ocr_si_vide and len(texte_page.strip()) < 100:
                    texte_ocr = _ocr_page(pdf_path, i + 1)
                    if texte_ocr:
                        texte_page = texte_ocr
                        nb_pages_ocr += 1

                texte += texte_page + "\n"

        if nb_pages_ocr > 0:
            logger.info(f"OCR utilisé pour {nb_pages_ocr} pages de {pdf_path}")

    except Exception as e:
        logger.error(f"Erreur lecture PDF {pdf_path}: {e}")

    return texte.strip()


def _ocr_page(pdf_path: str, page_num: int) -> Optional[str]:
    """OCR d'une page spécifique (français + arabe)"""
    try:
        from pdf2image import convert_from_path
        import pytesseract

        images = convert_from_path(pdf_path, first_page=page_num, last_page=page_num)
        if images:
            return pytesseract.image_to_string(images[0], lang="fra+ara")
    except ImportError:
        logger.warning("OCR non disponible (pdf2image/pytesseract manquants)")
    except Exception as e:
        logger.error(f"Erreur OCR page {page_num}: {e}")
    return None


def extraire_metadata_pdf(pdf_path: str) -> dict:
    """Extrait les métadonnées du PDF (titre, auteur, date)"""
    try:
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            return {
                "nb_pages": len(pdf.pages),
                "metadata": pdf.metadata or {},
            }
    except Exception as e:
        logger.error(f"Erreur métadonnées: {e}")
        return {}
