"""
veille/tendances.py - Fonctionnalité 12-A : Veille stratégique hebdomadaire
Détecte les tendances et génère un rapport de veille.
"""
import logging
from typing import List, Dict, Any
from collections import Counter
from datetime import datetime, timedelta

from ..llm_client import llm
from ..models import ProjetInvestissement
from ..prompts import PROMPT_VEILLE_HEBDO

logger = logging.getLogger(__name__)


def calculer_chiffres_cles(projets: List[ProjetInvestissement]) -> Dict[str, Any]:
    """Calcule les statistiques clés de la période (pas d'IA, juste agrégation)"""
    if not projets:
        return {
            "nb_projets": 0, "investissement_total": 0,
            "top_secteurs": [], "top_regions": [],
        }

    # Investissement total (uniquement les projets avec montant)
    total = sum(p.montant_mad for p in projets if p.montant_mad) or 0

    # Top secteurs
    secteurs_counter = Counter(p.secteur for p in projets)
    secteurs_montants = {}
    for p in projets:
        if p.montant_mad:
            secteurs_montants[p.secteur] = (
                secteurs_montants.get(p.secteur, 0) + p.montant_mad
            )
    top_secteurs = sorted(
        secteurs_montants.items(), key=lambda x: x[1], reverse=True
    )[:3]

    # Top régions
    regions_montants = {}
    for p in projets:
        if p.montant_mad and p.region:
            regions_montants[p.region] = (
                regions_montants.get(p.region, 0) + p.montant_mad
            )
    top_regions = sorted(
        regions_montants.items(), key=lambda x: x[1], reverse=True
    )[:3]

    # Stades d'avancement
    stades = Counter(p.stade_avancement for p in projets)

    return {
        "nb_projets": len(projets),
        "investissement_total": total,
        "investissement_total_mds": round(total / 1e9, 2),
        "top_secteurs": [
            {"secteur": s, "montant_mds": round(m / 1e9, 2)}
            for s, m in top_secteurs
        ],
        "top_regions": [
            {"region": r, "montant_mds": round(m / 1e9, 2)}
            for r, m in top_regions
        ],
        "distribution_stades": dict(stades),
        "score_fiabilite_moyen": round(
            sum(p.score_fiabilite or 0 for p in projets) / max(len(projets), 1), 1
        ),
    }


def generer_rapport_veille_hebdo(projets: List[ProjetInvestissement]) -> str:
    """
    Génère un rapport de veille stratégique sur les projets de la semaine.
    Format Markdown consommable par le Dashboard.
    """
    if not projets:
        return "# 📊 Rapport hebdomadaire\n\nAucun projet détecté cette semaine."

    chiffres = calculer_chiffres_cles(projets)

    # Sélection des top 5 projets par (fiabilité × montant)
    projets_top = sorted(
        projets,
        key=lambda p: (p.score_fiabilite or 50) * (p.montant_mad or 0),
        reverse=True,
    )[:5]

    # Format compact pour le LLM
    projets_str = "\n".join([
        f"- {p.titre[:80]} | {p.secteur} | {p.region} | "
        f"{p.montant_mad/1e9:.2f} Mds MAD | fiab={p.score_fiabilite}/100"
        for p in projets_top if p.montant_mad
    ])

    prompt = PROMPT_VEILLE_HEBDO.format(
        nb=len(projets),
        projets=f"""Chiffres clés calculés :
{chiffres}

Top 5 projets :
{projets_str}
""",
    )

    try:
        return llm.complete(prompt, max_tokens=2500, temperature=0.3)
    except Exception as e:
        logger.error(f"Erreur génération rapport : {e}")
        return _rapport_fallback(chiffres, projets_top)


def _rapport_fallback(chiffres: Dict, projets_top: List) -> str:
    """Rapport statique de secours"""
    lignes = [
        "# Rapport de veille hebdomadaire",
        "",
        "## 1. Chiffres clés",
        f"- Nombre de nouveaux projets : **{chiffres['nb_projets']}**",
        f"- Investissement total : **{chiffres['investissement_total_mds']} Mds MAD**",
        "",
        "### Top 3 secteurs",
    ]
    for s in chiffres["top_secteurs"]:
        lignes.append(f"- {s['secteur']} : {s['montant_mds']} Mds MAD")

    lignes.extend(["", "### Top 3 régions"])
    for r in chiffres["top_regions"]:
        lignes.append(f"- {r['region']} : {r['montant_mds']} Mds MAD")

    lignes.extend(["", "## 4. Projets à surveiller"])
    for p in projets_top:
        lignes.append(
            f"- **{p.titre[:80]}** ({p.secteur}, {p.region}) "
            f"- {(p.montant_mad or 0)/1e9:.2f} Mds MAD"
        )

    return "\n".join(lignes)


def detecter_tendances_emergentes(
    projets_actuels: List[ProjetInvestissement],
    projets_precedents: List[ProjetInvestissement],
) -> Dict[str, Any]:
    """
    Compare deux périodes pour détecter les tendances émergentes
    (secteurs en accélération, nouveaux porteurs, etc.)
    """
    secteurs_actuels = Counter(p.secteur for p in projets_actuels)
    secteurs_precedents = Counter(p.secteur for p in projets_precedents)

    accelerations = {}
    for secteur, count_actuel in secteurs_actuels.items():
        count_prec = secteurs_precedents.get(secteur, 0)
        if count_prec > 0:
            variation = ((count_actuel - count_prec) / count_prec) * 100
            if variation > 50:  # +50% : accélération significative
                accelerations[secteur] = round(variation, 1)
        elif count_actuel >= 3:
            accelerations[secteur] = "NOUVEAU"

    # Nouveaux porteurs (apparaissent pour la 1ère fois)
    porteurs_actuels = {p.porteur for p in projets_actuels if p.porteur}
    porteurs_precedents = {p.porteur for p in projets_precedents if p.porteur}
    nouveaux_porteurs = list(porteurs_actuels - porteurs_precedents)

    return {
        "secteurs_en_acceleration": accelerations,
        "nouveaux_porteurs": nouveaux_porteurs[:10],
        "nb_secteurs_actifs": len(secteurs_actuels),
    }
