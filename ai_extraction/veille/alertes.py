"""
veille/alertes.py - Fonctionnalité 12-B : Alertes personnalisées
L'IA évalue chaque nouveau projet selon le profil de l'analyste SDG.
"""
import logging
from typing import Dict, Any, List, Optional

from ..llm_client import llm
from ..models import ProjetInvestissement, AlertePersonnalisee
from ..prompts import PROMPT_ALERTE_PERSONNALISEE

logger = logging.getLogger(__name__)


# Profil par défaut (à personnaliser par utilisateur dans le dashboard)
PROFIL_DEFAULT = {
    "secteurs": ["Énergie", "Tech & Digital", "Industrie"],
    "regions": ["Casablanca-Settat", "Tanger-Tétouan-Al Hoceïma",
                "Rabat-Salé-Kénitra"],
    "montant_min": 100_000_000,  # 100 M MAD
    "stades": ["convention_signee", "en_construction"],
}


def evaluer_pertinence_alerte(
    projet: ProjetInvestissement,
    profil: Optional[Dict[str, Any]] = None,
) -> Optional[AlertePersonnalisee]:
    """
    Évalue si un projet mérite une alerte pour ce profil utilisateur.

    Returns:
        AlertePersonnalisee si pertinent (score >= 50), None sinon
    """
    profil = profil or PROFIL_DEFAULT

    # === Pré-filtrage rapide (économise LLM) ===
    if not _pre_filtre_profil(projet, profil):
        return None

    # === Évaluation IA ===
    prompt = PROMPT_ALERTE_PERSONNALISEE.format(
        secteurs=profil["secteurs"],
        regions=profil["regions"],
        montant_min=profil["montant_min"],
        stades=profil["stades"],
        projet=_format_projet_court(projet),
    )

    try:
        result = llm.complete_json(prompt)
        score = int(result.get("pertinence_score", 0))

        if score >= 50:
            return AlertePersonnalisee(
                projet_id=projet.id or "",
                user_id=profil.get("user_id", "default"),
                pertinence_score=score,
                urgence=result.get("urgence", "moyenne"),
                raison_alerte=result.get("raison_alerte", ""),
                actions_suggerees=result.get("actions_suggerees", []),
            )
        return None

    except Exception as e:
        logger.error(f"Erreur évaluation alerte: {e}")
        return None


def _pre_filtre_profil(
    projet: ProjetInvestissement,
    profil: Dict[str, Any],
) -> bool:
    """Pré-filtre rapide avant appel LLM"""
    # Filtre secteur
    if projet.secteur not in profil.get("secteurs", []):
        return False

    # Filtre région (si renseignée)
    if projet.region and projet.region not in profil.get("regions", []):
        return False

    # Filtre montant minimum
    montant_min = profil.get("montant_min", 0)
    if projet.montant_mad and projet.montant_mad < montant_min:
        return False

    return True


def _format_projet_court(projet: ProjetInvestissement) -> str:
    """Format compact pour réduire les tokens"""
    return f"""Titre : {projet.titre}
Secteur : {projet.secteur} / {projet.sous_secteur or 'N/A'}
Région : {projet.region}
Porteur : {projet.porteur}
Montant : {projet.montant_mad} MAD
Stade : {projet.stade_avancement}
Description : {projet.description[:300]}"""


def notifier_utilisateurs_pertinents(
    projet: ProjetInvestissement,
    profils: List[Dict[str, Any]],
) -> List[AlertePersonnalisee]:
    """
    Évalue le projet contre tous les profils et retourne les alertes générées.
    """
    alertes = []
    for profil in profils:
        alerte = evaluer_pertinence_alerte(projet, profil)
        if alerte:
            alertes.append(alerte)
            logger.info(
                f"🔔 Alerte générée pour user={alerte.user_id} "
                f"(score={alerte.pertinence_score}, urgence={alerte.urgence})"
            )
    return alertes
