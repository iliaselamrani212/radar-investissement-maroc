"""
enrichissement/classifier_fin.py - Fonctionnalité 11 : Classification fine
Au-delà des 5 champs critiques, classifie selon plusieurs dimensions.
"""
import logging
from typing import Dict, Any

from ..llm_client import llm
from ..models import ProjetInvestissement
from ..prompts import PROMPT_CLASSIFICATION_FINE

logger = logging.getLogger(__name__)


# Validation : valeurs autorisées pour la classification
SOUS_SECTEURS_VALIDES = {
    "Énergie": ["Solaire", "Éolien", "Hydrogène vert", "Biomasse",
                "Hydraulique", "Gaz", "Pétrole"],
    "Industrie": ["Automobile", "Aéronautique", "Textile", "Agroalimentaire",
                  "Chimie", "Pharma", "Métallurgie"],
    "Tourisme": ["Hôtellerie", "Resort", "Tourisme culturel", "Tourisme nature"],
    "Tech & Digital": ["Data center", "Fintech", "E-commerce", "IA",
                       "SaaS", "Télécoms"],
}

STRATEGIES_VALIDES = [
    "Plan d'Accélération Industrielle",
    "Stratégie Énergétique Nationale",
    "Plan Maroc Digital 2030",
    "Maroc Vert",
    "Plan Halieutis",
    "Vision 2030 Tourisme",
    "Stratégie Hydrogène Vert",
    "Maroc 2030 (Mondial Football)",
]

TAGS_ESG_VALIDES = [
    "transition_energetique",
    "creation_emplois",
    "innovation_technologique",
    "developpement_regional",
    "souverainete_industrielle",
    "exportation",
]


def classifier_finement(projet: ProjetInvestissement) -> Dict[str, Any]:
    """
    Classifie le projet selon plusieurs dimensions :
    - sous_secteur (selon secteur principal)
    - type_projet
    - strategies_nationales
    - tags_esg
    """
    prompt = PROMPT_CLASSIFICATION_FINE.format(
        titre=projet.titre,
        description=projet.description[:1000],
        secteur=projet.secteur,
    )

    try:
        result = llm.complete_json(prompt)
        # Validation des valeurs
        result = _valider_classification(result, projet.secteur)
        return result
    except Exception as e:
        logger.error(f"Erreur classification fine: {e}")
        return {
            "sous_secteur": None,
            "type_projet": None,
            "strategies_nationales": [],
            "tags_esg": [],
        }


def _valider_classification(result: Dict, secteur: str) -> Dict:
    """Filtre les valeurs invalides retournées par le LLM"""
    # Sous-secteur : doit appartenir aux choix valides
    sous_secteur = result.get("sous_secteur")
    if secteur in SOUS_SECTEURS_VALIDES:
        if sous_secteur not in SOUS_SECTEURS_VALIDES[secteur]:
            sous_secteur = None
    result["sous_secteur"] = sous_secteur

    # Stratégies nationales : filtre les valides
    strategies = result.get("strategies_nationales", [])
    if isinstance(strategies, list):
        result["strategies_nationales"] = [
            s for s in strategies if s in STRATEGIES_VALIDES
        ][:3]
    else:
        result["strategies_nationales"] = []

    # Tags ESG : filtre les valides
    tags = result.get("tags_esg", [])
    if isinstance(tags, list):
        result["tags_esg"] = [t for t in tags if t in TAGS_ESG_VALIDES][:4]
    else:
        result["tags_esg"] = []

    # Type de projet
    types_valides = ["creation", "extension", "modernisation",
                     "partenariat", "fusion_acquisition"]
    if result.get("type_projet") not in types_valides:
        result["type_projet"] = "creation"

    return result


def appliquer_classification(
    projet: ProjetInvestissement,
    classification: Dict,
) -> ProjetInvestissement:
    """Applique la classification au projet"""
    if classification.get("sous_secteur"):
        projet.sous_secteur = classification["sous_secteur"]
    if classification.get("type_projet"):
        projet.type_projet = classification["type_projet"]
    projet.strategies_nationales = classification.get("strategies_nationales", [])
    projet.tags_esg = classification.get("tags_esg", [])
    return projet
