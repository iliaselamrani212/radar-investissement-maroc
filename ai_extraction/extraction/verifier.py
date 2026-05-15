"""
extraction/verifier.py - Fonctionnalité 4 : Auto-vérification
L'IA vérifie sa propre extraction pour éviter les hallucinations.
"""
import logging
from typing import Tuple, Dict

from ..llm_client import llm
from ..models import ProjetInvestissement
from ..prompts import PROMPT_AUTO_VERIFICATION

logger = logging.getLogger(__name__)


def auto_verifier(
    document_original: str,
    extraction: ProjetInvestissement,
) -> Tuple[ProjetInvestissement, Dict[str, str]]:
    """
    Vérifie chaque champ extrait par rapport au document original.

    Returns:
        (projet ajusté, dict de vérification par champ)
    """
    prompt = PROMPT_AUTO_VERIFICATION.format(
        document=document_original[:3000],
        montant=extraction.montant_mad,
        secteur=extraction.secteur,
        region=extraction.region,
        porteur=extraction.porteur,
        stade=extraction.stade_avancement,
    )

    try:
        verification = llm.complete_json(prompt)

        # Ajustement du score selon les vérifications
        nb_errone = sum(1 for v in verification.values() if v == "ERRONE")
        nb_incertain = sum(1 for v in verification.values() if v == "INCERTAIN")
        nb_deduit = sum(1 for v in verification.values() if v == "DEDUIT_LOGIQUE")

        if nb_errone > 0:
            extraction.score_confiance_extraction *= 0.3
            logger.warning(f"⚠️  {nb_errone} champ(s) ERRONÉ(s) détecté(s)")
        elif nb_incertain > 1:
            extraction.score_confiance_extraction *= 0.6
        elif nb_incertain > 0:
            extraction.score_confiance_extraction *= 0.8
        elif nb_deduit > 2:
            extraction.score_confiance_extraction *= 0.9

        extraction.score_confiance_extraction = max(
            0.0, min(1.0, extraction.score_confiance_extraction)
        )

        return extraction, verification

    except Exception as e:
        logger.error(f"Erreur auto-vérification: {e}")
        return extraction, {}
