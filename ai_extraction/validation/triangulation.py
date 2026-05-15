"""
validation/triangulation.py - Fonctionnalité 9 : Triangulation multi-sources
Plus un projet est confirmé par plusieurs sources officielles, plus il est fiable.
"""
import logging
from typing import List, Dict, Any
import numpy as np

from ..llm_client import llm
from ..models import ProjetInvestissement, SourceArticle
from ..dedup.embeddings_dedup import dedup_service
from ..config import SEUIL_TRIANGULATION, SOURCES_CONFIG

logger = logging.getLogger(__name__)


def trianguler(
    projet: ProjetInvestissement,
    articles_db: List[SourceArticle],
) -> List[Dict[str, Any]]:
    """
    Cherche dans la base d'articles bruts d'autres sources confirmant ce projet.

    Args:
        projet: projet à trianguler
        articles_db: tous les articles bruts indexés

    Returns:
        Liste des sources confirmées avec niveau de fiabilité
    """
    emb_projet = dedup_service.embed(projet)
    sources_confirmees = []
    sources_deja_vues = {projet.source_principale}

    for article in articles_db:
        # Skip article déjà vu de la même source
        if article.source in sources_deja_vues:
            continue

        # Calcul de similarité
        try:
            # On utilise le titre + snippet de l'article comme signature
            signature_article = f"{article.title} {article.snippet or ''} {article.source}"
            emb_article = dedup_service.model.encode(signature_article)
            similarity = dedup_service.cosine_similarity(emb_projet, emb_article)

            if similarity > SEUIL_TRIANGULATION:
                # Confirmation LLM
                if _llm_confirme_meme_projet(projet, article):
                    niveau = _get_niveau_source(article.source)
                    sources_confirmees.append({
                        "source": article.source,
                        "nom_source": _get_nom_source(article.source),
                        "niveau_fiabilite": niveau,
                        "url": article.url,
                        "similarity": round(similarity, 3),
                        "date": str(article.fetched_at),
                    })
                    sources_deja_vues.add(article.source)
        except Exception as e:
            logger.error(f"Erreur triangulation pour {article.source}: {e}")
            continue

    logger.info(
        f"Triangulation : {len(sources_confirmees)} sources confirmant "
        f"'{projet.titre[:50]}'"
    )
    return sources_confirmees


def _llm_confirme_meme_projet(
    projet: ProjetInvestissement,
    article: SourceArticle,
) -> bool:
    """Confirme via LLM que l'article parle bien du même projet"""
    prompt = f"""Cet article officiel parle-t-il du MÊME projet d'investissement ?

PROJET DÉJÀ EXTRAIT :
- Titre : {projet.titre}
- Porteur : {projet.porteur}
- Région : {projet.region}
- Secteur : {projet.secteur}
- Montant : {projet.montant_mad} MAD

ARTICLE À COMPARER (source : {article.source}) :
- Titre : {article.title}
- Extrait : {(article.snippet or article.content[:300])}

Réponds OUI ou NON uniquement."""
    try:
        return llm.binaire(prompt)
    except Exception:
        return False


def _get_niveau_source(source: str) -> int:
    """Niveau de fiabilité de la source (1-5)"""
    cfg = SOURCES_CONFIG.get(source, {})
    return cfg.get("niveau_fiabilite", 3)


def _get_nom_source(source: str) -> str:
    """Nom officiel de la source"""
    cfg = SOURCES_CONFIG.get(source, {})
    return cfg.get("nom", source)


def calculer_score_fiabilite(projet: ProjetInvestissement) -> float:
    """
    Calcule un score de fiabilité 0-100 basé sur :
    - Nombre de sources confirmant le projet
    - Niveau de fiabilité des sources
    - Score de confiance d'extraction
    - Anomalies détectées
    """
    # Base : score de confiance d'extraction (0-1 → 0-50)
    score = projet.score_confiance_extraction * 50

    # Bonus triangulation : +10 par source confirmée (max +30)
    bonus_sources = min(30, projet.nb_sources_confirmees * 10)
    score += bonus_sources

    # Bonus niveau des sources : moyenne des niveaux × 4 (max +20)
    if projet.sources:
        niveaux = [s.get("niveau_fiabilite", 3) for s in projet.sources]
        moyenne_niveau = sum(niveaux) / len(niveaux)
        score += moyenne_niveau * 4
    else:
        score += 12  # niveau 3 par défaut

    # Malus anomalies
    for anomalie in projet.anomalies:
        score += anomalie.get("impact_fiabilite", 0)

    # Bornage 0-100
    return max(0.0, min(100.0, round(score, 1)))
