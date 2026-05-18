"""
ai_extraction - Module IA InvestiGator 43

Système d'extraction et d'enrichissement automatique des projets d'investissement
au Maroc, exploitant 15+ sources publiques et institutionnelles.
"""

__version__ = "1.0.0"
__author__ = "Equipe InvestiGator 43"

from .models import ProjetInvestissement, SourceArticle
from .pipeline import traiter_nouveau_document, traiter_batch
from .database import init_db, save_projet, get_all_projets

__all__ = [
    "ProjetInvestissement",
    "SourceArticle",
    "traiter_nouveau_document",
    "traiter_batch",
    "init_db",
    "save_projet",
    "get_all_projets",
]
