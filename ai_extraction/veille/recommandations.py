"""
veille/recommandations.py - Fonctionnalité 12-C : Recommandations de projets similaires
Suggère des projets liés via embeddings (pour le Dashboard).
"""
import logging
from typing import List, Dict, Any
import numpy as np

from ..llm_client import llm
from ..models import ProjetInvestissement
from ..dedup.embeddings_dedup import dedup_service

logger = logging.getLogger(__name__)


def recommander_similaires(
    projet_consulte: ProjetInvestissement,
    tous_projets: List[ProjetInvestissement],
    top_n: int = 5,
    avec_explications: bool = True,
) -> List[Dict[str, Any]]:
    """
    Retourne les top_n projets les plus similaires au projet consulté.

    Args:
        projet_consulte: projet vu actuellement
        tous_projets: base complète de projets
        top_n: nombre de recommandations
        avec_explications: si True, génère une explication IA pour chaque suggestion

    Returns:
        Liste de dicts {projet, similarity, raison}
    """
    if not tous_projets:
        return []

    # Embedding du projet consulté
    emb_consulte = dedup_service.embed(projet_consulte)

    # Calcul des similarités
    scored = []
    for p in tous_projets:
        if p.id == projet_consulte.id:
            continue
        try:
            emb_p = dedup_service.embed(p)
            sim = dedup_service.cosine_similarity(emb_consulte, emb_p)
            scored.append((p, sim))
        except Exception as e:
            logger.error(f"Erreur similarité pour {p.id}: {e}")
            continue

    # Tri et top N
    scored.sort(key=lambda x: x[1], reverse=True)
    top_similaires = scored[:top_n]

    # Génération d'explications par IA
    recommendations = []
    for proj, score in top_similaires:
        rec = {
            "projet": {
                "id": proj.id,
                "titre": proj.titre,
                "secteur": proj.secteur,
                "region": proj.region,
                "porteur": proj.porteur,
                "montant_mad": proj.montant_mad,
                "stade": proj.stade_avancement,
            },
            "similarity": round(score, 3),
        }

        if avec_explications:
            rec["raison"] = _expliquer_similarite(projet_consulte, proj)

        recommendations.append(rec)

    return recommendations


def _expliquer_similarite(
    p1: ProjetInvestissement,
    p2: ProjetInvestissement,
) -> str:
    """Génère une explication courte de la similarité entre 2 projets"""
    prompt = f"""En 1 phrase concise, explique pourquoi ces 2 projets d'investissement
au Maroc sont liés (secteur, région, porteur, stratégie...).

Projet A :
- {p1.titre}
- Secteur : {p1.secteur}, Région : {p1.region}, Porteur : {p1.porteur}

Projet B :
- {p2.titre}
- Secteur : {p2.secteur}, Région : {p2.region}, Porteur : {p2.porteur}

Réponse : 1 phrase, max 25 mots."""
    try:
        return llm.complete(prompt, max_tokens=100, temperature=0.3)
    except Exception:
        # Fallback : explication mécanique
        points = []
        if p1.secteur == p2.secteur:
            points.append(f"même secteur ({p1.secteur})")
        if p1.region == p2.region:
            points.append(f"même région ({p1.region})")
        if p1.porteur and p1.porteur == p2.porteur:
            points.append(f"même porteur ({p1.porteur})")
        return f"Projets liés par : {', '.join(points)}" if points else "Projets contextuellement liés."


def recommander_par_filtres(
    projets: List[ProjetInvestissement],
    secteurs: List[str] = None,
    regions: List[str] = None,
    montant_min: float = 0,
    stades: List[str] = None,
    top_n: int = 10,
) -> List[ProjetInvestissement]:
    """
    Filtrage simple par critères (pour le Dashboard).
    Aligné avec LIVRABLE 4 : "Outils de filtrage et de priorisation"
    """
    resultats = []
    for p in projets:
        if secteurs and p.secteur not in secteurs:
            continue
        if regions and p.region not in regions:
            continue
        if p.montant_mad and p.montant_mad < montant_min:
            continue
        if stades and p.stade_avancement not in stades:
            continue
        resultats.append(p)

    # Tri par fiabilité × montant
    resultats.sort(
        key=lambda p: (p.score_fiabilite or 50) * (p.montant_mad or 0),
        reverse=True,
    )
    return resultats[:top_n]
