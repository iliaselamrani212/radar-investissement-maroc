"""
filtres/pertinence.py - Fonctionnalité 1 : Filtrage IA de pertinence
Décide si un article mérite une extraction approfondie.
"""
import logging
from ..llm_client import llm
from ..prompts import PROMPT_FILTRE_PERTINENCE

logger = logging.getLogger(__name__)


# Mots-clés de pré-filtrage rapide (avant l'IA pour économiser)
MOTS_CLES_INVESTISSEMENT = [
    "investissement", "investir", "convention", "projet",
    "usine", "chantier", "lancement", "création", "extension",
    "milliards", "millions", "MAD", "DH", "dirhams",
    "joint-venture", "partenariat", "construction",
    "inauguration", "approbation", "approuvé",
]


def pre_filtre_keywords(titre: str, snippet: str) -> bool:
    """Pré-filtre rapide par mots-clés (économise des appels LLM)"""
    texte = f"{titre} {snippet}".lower()
    return any(mot.lower() in texte for mot in MOTS_CLES_INVESTISSEMENT)


def llm_filtre_pertinence(titre: str, snippet: str) -> bool:
    """
    Filtrage IA : décide si le contenu est un projet d'investissement.
    Retourne True si pertinent, False sinon.
    """
    # Étape 1 : pré-filtre rapide (économie LLM)
    if not pre_filtre_keywords(titre, snippet):
        logger.debug(f"Pré-filtre rejeté: {titre[:50]}")
        return False

    # Étape 2 : validation IA
    prompt = PROMPT_FILTRE_PERTINENCE.format(
        titre=titre[:200],
        snippet=snippet[:500],
    )

    try:
        return llm.binaire(prompt)
    except Exception as e:
        logger.error(f"Erreur filtre pertinence: {e}")
        # En cas d'erreur, on garde (false negative > false positive)
        return True


def batch_filtre(articles: list) -> list:
    """Filtrage en lot d'une liste d'articles"""
    pertinents = []
    for article in articles:
        if llm_filtre_pertinence(article["title"], article.get("snippet", "")):
            pertinents.append(article)
    logger.info(f"Filtre: {len(pertinents)}/{len(articles)} retenus")
    return pertinents
