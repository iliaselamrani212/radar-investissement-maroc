"""
enrichissement/macro_context.py - Fonctionnalité 7 : Enrichissement macroéconomique
Ajoute le contexte officiel (data.gov.ma, HCP, MEF) à chaque projet.
"""
import logging
from typing import Dict, Any, Optional

from ..llm_client import llm
from ..models import ProjetInvestissement
from ..prompts import PROMPT_ANALYSE_MACRO

logger = logging.getLogger(__name__)


# === RÉFÉRENTIELS MACROÉCONOMIQUES ===
# Données issues de data.gov.ma / HCP / MEF (valeurs indicatives, à actualiser)

REFERENTIEL_SECTEURS = {
    "Industrie": {
        "pib_pct": 17.5,
        "invest_moyen_mad": 250_000_000,
        "croissance_pct": 3.8,
        "source": "MEF - data.gov.ma",
    },
    "Énergie": {
        "pib_pct": 4.2,
        "invest_moyen_mad": 1_500_000_000,
        "croissance_pct": 8.1,
        "source": "MEF / MASEN",
    },
    "Agriculture": {
        "pib_pct": 12.0,
        "invest_moyen_mad": 80_000_000,
        "croissance_pct": 4.5,
        "source": "HCP",
    },
    "Pêche maritime": {
        "pib_pct": 2.3,
        "invest_moyen_mad": 50_000_000,
        "croissance_pct": 3.2,
        "source": "Plan Halieutis - MEF",
    },
    "Tourisme": {
        "pib_pct": 7.0,
        "invest_moyen_mad": 500_000_000,
        "croissance_pct": 5.5,
        "source": "Ministère du Tourisme",
    },
    "Tech & Digital": {
        "pib_pct": 5.5,
        "invest_moyen_mad": 150_000_000,
        "croissance_pct": 12.0,
        "source": "ADD / Maroc Digital 2030",
    },
    "Immobilier": {
        "pib_pct": 6.8,
        "invest_moyen_mad": 300_000_000,
        "croissance_pct": 2.5,
        "source": "HCP",
    },
    "Logistique": {
        "pib_pct": 5.0,
        "invest_moyen_mad": 200_000_000,
        "croissance_pct": 7.0,
        "source": "Ministère du Transport",
    },
    "Santé": {
        "pib_pct": 6.0,
        "invest_moyen_mad": 120_000_000,
        "croissance_pct": 6.5,
        "source": "Ministère de la Santé",
    },
    "Infrastructure": {
        "pib_pct": 9.5,
        "invest_moyen_mad": 800_000_000,
        "croissance_pct": 5.8,
        "source": "MEF",
    },
    "Mines": {
        "pib_pct": 10.0,
        "invest_moyen_mad": 600_000_000,
        "croissance_pct": 4.0,
        "source": "ONHYM / OCP",
    },
    "Finance": {
        "pib_pct": 6.5,
        "invest_moyen_mad": 100_000_000,
        "croissance_pct": 3.5,
        "source": "Bank Al-Maghrib",
    },
    "Commerce": {
        "pib_pct": 11.0,
        "invest_moyen_mad": 70_000_000,
        "croissance_pct": 4.0,
        "source": "HCP",
    },
    "BTP": {
        "pib_pct": 6.0,
        "invest_moyen_mad": 200_000_000,
        "croissance_pct": 3.5,
        "source": "HCP",
    },
    "Éducation": {
        "pib_pct": 5.0,
        "invest_moyen_mad": 80_000_000,
        "croissance_pct": 4.2,
        "source": "Ministère de l'Éducation",
    },
    "Autre": {
        "pib_pct": 1.0,
        "invest_moyen_mad": 50_000_000,
        "croissance_pct": 2.0,
        "source": "HCP",
    },
}


REFERENTIEL_REGIONS = {
    "Casablanca-Settat": {
        "budget_alloue": 45_000_000_000,
        "pib_regional_pct": 32.0,
        "secteurs_dominants": ["Industrie", "Finance", "Tech & Digital"],
    },
    "Rabat-Salé-Kénitra": {
        "budget_alloue": 25_000_000_000,
        "pib_regional_pct": 15.0,
        "secteurs_dominants": ["Industrie", "Tech & Digital", "Tourisme"],
    },
    "Tanger-Tétouan-Al Hoceïma": {
        "budget_alloue": 22_000_000_000,
        "pib_regional_pct": 10.0,
        "secteurs_dominants": ["Industrie", "Logistique", "Tourisme"],
    },
    "Fès-Meknès": {
        "budget_alloue": 15_000_000_000,
        "pib_regional_pct": 8.5,
        "secteurs_dominants": ["Agriculture", "Industrie", "Tourisme"],
    },
    "Marrakech-Safi": {
        "budget_alloue": 18_000_000_000,
        "pib_regional_pct": 9.0,
        "secteurs_dominants": ["Tourisme", "Mines", "Agriculture"],
    },
    "Oriental": {
        "budget_alloue": 12_000_000_000,
        "pib_regional_pct": 5.0,
        "secteurs_dominants": ["Agriculture", "Énergie", "Logistique"],
    },
    "Béni Mellal-Khénifra": {
        "budget_alloue": 10_000_000_000,
        "pib_regional_pct": 4.5,
        "secteurs_dominants": ["Mines", "Agriculture"],
    },
    "Souss-Massa": {
        "budget_alloue": 14_000_000_000,
        "pib_regional_pct": 7.0,
        "secteurs_dominants": ["Pêche maritime", "Agriculture", "Tourisme"],
    },
    "Drâa-Tafilalet": {
        "budget_alloue": 8_000_000_000,
        "pib_regional_pct": 2.5,
        "secteurs_dominants": ["Énergie", "Tourisme", "Mines"],
    },
    "Guelmim-Oued Noun": {
        "budget_alloue": 5_000_000_000,
        "pib_regional_pct": 1.0,
        "secteurs_dominants": ["Pêche maritime", "Énergie"],
    },
    "Laâyoune-Sakia El Hamra": {
        "budget_alloue": 6_000_000_000,
        "pib_regional_pct": 2.0,
        "secteurs_dominants": ["Pêche maritime", "Énergie"],
    },
    "Dakhla-Oued Ed-Dahab": {
        "budget_alloue": 5_500_000_000,
        "pib_regional_pct": 1.5,
        "secteurs_dominants": ["Pêche maritime", "Tourisme", "Énergie"],
    },
}


def enrichir_avec_macro(projet: ProjetInvestissement) -> Dict[str, Any]:
    """
    Enrichit un projet avec le contexte macroéconomique officiel.
    """
    enrichissement = {}

    # 1. Contexte sectoriel
    if projet.secteur in REFERENTIEL_SECTEURS:
        secteur_data = REFERENTIEL_SECTEURS[projet.secteur]
        enrichissement["contexte_secteur"] = {
            "secteur": projet.secteur,
            "pib_pct": secteur_data["pib_pct"],
            "investissement_moyen": secteur_data["invest_moyen_mad"],
            "croissance_annuelle": secteur_data["croissance_pct"],
            "source": secteur_data["source"],
            "ratio_au_moyen": (
                round(projet.montant_mad / secteur_data["invest_moyen_mad"], 2)
                if projet.montant_mad else None
            ),
        }

    # 2. Contexte régional
    if projet.region and projet.region in REFERENTIEL_REGIONS:
        region_data = REFERENTIEL_REGIONS[projet.region]
        enrichissement["contexte_region"] = {
            "region": projet.region,
            "budget_public": region_data["budget_alloue"],
            "pib_regional_pct": region_data["pib_regional_pct"],
            "secteurs_dominants": region_data["secteurs_dominants"],
            "secteur_aligne": projet.secteur in region_data["secteurs_dominants"],
            "source": "data.gov.ma / HCP",
        }

    # 3. Analyse contextuelle générée par IA
    if enrichissement.get("contexte_secteur"):
        analyse = _generer_analyse_macro(projet, enrichissement)
        enrichissement["analyse_contextuelle"] = analyse

    return enrichissement


def _generer_analyse_macro(
    projet: ProjetInvestissement,
    enrichissement: Dict,
) -> str:
    """Génère une analyse contextuelle de 2 phrases par IA"""
    ctx_sect = enrichissement.get("contexte_secteur", {})
    ctx_reg = enrichissement.get("contexte_region", {})

    prompt = PROMPT_ANALYSE_MACRO.format(
        titre=projet.titre,
        montant=projet.montant_mad or "non précisé",
        secteur=projet.secteur,
        pib_pct=ctx_sect.get("pib_pct", "?"),
        region=projet.region or "non précisée",
        budget_region=ctx_reg.get("budget_public", "?"),
    )
    try:
        return llm.complete(prompt, max_tokens=200)
    except Exception as e:
        logger.error(f"Erreur analyse macro: {e}")
        return ""
