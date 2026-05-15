"""
validation/anomalies.py - Fonctionnalité 8 : Détection d'anomalies
Signale les projets avec données suspectes ou incohérentes.
"""
import logging
from typing import List, Dict, Any

from ..llm_client import llm
from ..models import ProjetInvestissement, Anomalie

logger = logging.getLogger(__name__)


# Incohérences secteur ↔ région (régions intérieures vs maritimes)
INCOHERENCES_SECTEUR_REGION = {
    "Pêche maritime": [
        "Drâa-Tafilalet", "Fès-Meknès", "Béni Mellal-Khénifra"
    ],
}


def detecter_anomalies(
    projet: ProjetInvestissement,
    enrichissement: Dict[str, Any],
) -> List[Anomalie]:
    """
    Détecte les anomalies dans un projet.
    Retourne une liste d'anomalies trouvées.
    """
    anomalies = []

    # === Anomalie 1 : Montant disproportionné ===
    if projet.montant_mad and enrichissement.get("contexte_secteur"):
        moyenne = enrichissement["contexte_secteur"]["investissement_moyen"]
        if moyenne > 0 and projet.montant_mad > moyenne * 50:
            anomalies.append(Anomalie(
                type="MONTANT_DISPROPORTIONNE",
                severite="elevee",
                message=f"Montant {projet.montant_mad/1e9:.1f} Mds MAD soit "
                        f"{projet.montant_mad/moyenne:.0f}x supérieur à la moyenne du secteur",
                impact_fiabilite=-15,
            ))
        elif projet.montant_mad < moyenne * 0.01 and projet.montant_mad > 0:
            anomalies.append(Anomalie(
                type="MONTANT_TROP_FAIBLE",
                severite="moyenne",
                message="Montant très faible vs moyenne du secteur",
                impact_fiabilite=-5,
            ))

    # === Anomalie 2 : Secteur/région incohérent ===
    if projet.secteur in INCOHERENCES_SECTEUR_REGION:
        if projet.region in INCOHERENCES_SECTEUR_REGION[projet.secteur]:
            anomalies.append(Anomalie(
                type="SECTEUR_REGION_INCOHERENT",
                severite="moyenne",
                message=f"{projet.secteur} en région intérieure ({projet.region})",
                impact_fiabilite=-10,
            ))

    # === Anomalie 3 : Porteur inconnu sur très gros montant ===
    if projet.montant_mad and projet.montant_mad > 1_000_000_000:
        if projet.porteur and _porteur_inconnu_llm(projet.porteur):
            anomalies.append(Anomalie(
                type="PORTEUR_INCONNU_GROS_MONTANT",
                severite="elevee",
                message=f"Porteur '{projet.porteur}' non identifié pour un projet > 1 Md MAD",
                impact_fiabilite=-20,
            ))

    # === Anomalie 4 : Données incomplètes critiques ===
    champs_manquants = []
    if not projet.montant_mad:
        champs_manquants.append("montant")
    if not projet.region:
        champs_manquants.append("region")
    if not projet.porteur:
        champs_manquants.append("porteur")

    if len(champs_manquants) >= 2:
        anomalies.append(Anomalie(
            type="DONNEES_INCOMPLETES",
            severite="moyenne",
            message=f"Champs critiques manquants : {', '.join(champs_manquants)}",
            impact_fiabilite=-10,
        ))

    # === Anomalie 5 : Score de confiance très bas ===
    if projet.score_confiance_extraction < 0.4:
        anomalies.append(Anomalie(
            type="EXTRACTION_PEU_FIABLE",
            severite="moyenne",
            message=f"Score de confiance d'extraction faible : {projet.score_confiance_extraction:.2f}",
            impact_fiabilite=-15,
        ))

    return anomalies


def _porteur_inconnu_llm(porteur: str) -> bool:
    """Demande à l'IA si l'entreprise est connue au Maroc"""
    prompt = f"""L'entreprise '{porteur}' est-elle une entreprise connue au Maroc 
(grande entreprise, multinationale, organisme public marocain) ?
Réponds OUI ou NON uniquement."""
    try:
        return not llm.binaire(prompt)
    except Exception:
        return False
