"""
enrichissement/geocoder.py - Fonctionnalité 6 : Géocodage intelligent
Convertit une mention textuelle en coordonnées GPS pour la carte du dashboard.
"""
import logging
from typing import Optional, Dict

from ..llm_client import llm
from ..prompts import PROMPT_GEOCODAGE

logger = logging.getLogger(__name__)


# === RÉFÉRENTIEL DES VILLES MAROCAINES ===
VILLES_MAROC: Dict[str, Dict] = {
    # Casablanca-Settat
    "Casablanca": {"lat": 33.5731, "lng": -7.5898, "region": "Casablanca-Settat"},
    "Mohammedia": {"lat": 33.6864, "lng": -7.3830, "region": "Casablanca-Settat"},
    "El Jadida": {"lat": 33.2316, "lng": -8.5007, "region": "Casablanca-Settat"},
    "Settat": {"lat": 33.0010, "lng": -7.6164, "region": "Casablanca-Settat"},
    "Berrechid": {"lat": 33.2654, "lng": -7.5870, "region": "Casablanca-Settat"},

    # Rabat-Salé-Kénitra
    "Rabat": {"lat": 34.0209, "lng": -6.8416, "region": "Rabat-Salé-Kénitra"},
    "Salé": {"lat": 34.0531, "lng": -6.7985, "region": "Rabat-Salé-Kénitra"},
    "Kénitra": {"lat": 34.2610, "lng": -6.5802, "region": "Rabat-Salé-Kénitra"},
    "Témara": {"lat": 33.9287, "lng": -6.9067, "region": "Rabat-Salé-Kénitra"},

    # Tanger-Tétouan-Al Hoceïma
    "Tanger": {"lat": 35.7595, "lng": -5.8340, "region": "Tanger-Tétouan-Al Hoceïma"},
    "Tanger Med": {"lat": 35.8967, "lng": -5.5078, "region": "Tanger-Tétouan-Al Hoceïma"},
    "Tétouan": {"lat": 35.5785, "lng": -5.3684, "region": "Tanger-Tétouan-Al Hoceïma"},
    "Al Hoceïma": {"lat": 35.2475, "lng": -3.9372, "region": "Tanger-Tétouan-Al Hoceïma"},

    # Fès-Meknès
    "Fès": {"lat": 34.0181, "lng": -5.0078, "region": "Fès-Meknès"},
    "Meknès": {"lat": 33.8935, "lng": -5.5547, "region": "Fès-Meknès"},
    "Ifrane": {"lat": 33.5228, "lng": -5.1106, "region": "Fès-Meknès"},
    "Taza": {"lat": 34.2167, "lng": -4.0167, "region": "Fès-Meknès"},

    # Marrakech-Safi
    "Marrakech": {"lat": 31.6295, "lng": -7.9811, "region": "Marrakech-Safi"},
    "Safi": {"lat": 32.2994, "lng": -9.2372, "region": "Marrakech-Safi"},
    "Essaouira": {"lat": 31.5085, "lng": -9.7595, "region": "Marrakech-Safi"},

    # Oriental
    "Oujda": {"lat": 34.6814, "lng": -1.9086, "region": "Oriental"},
    "Nador": {"lat": 35.1681, "lng": -2.9335, "region": "Oriental"},
    "Berkane": {"lat": 34.9220, "lng": -2.3197, "region": "Oriental"},

    # Béni Mellal-Khénifra
    "Béni Mellal": {"lat": 32.3373, "lng": -6.3498, "region": "Béni Mellal-Khénifra"},
    "Khénifra": {"lat": 32.9342, "lng": -5.6685, "region": "Béni Mellal-Khénifra"},
    "Khouribga": {"lat": 32.8811, "lng": -6.9063, "region": "Béni Mellal-Khénifra"},

    # Souss-Massa
    "Agadir": {"lat": 30.4278, "lng": -9.5981, "region": "Souss-Massa"},
    "Tiznit": {"lat": 29.6974, "lng": -9.7322, "region": "Souss-Massa"},
    "Taroudant": {"lat": 30.4727, "lng": -8.8770, "region": "Souss-Massa"},

    # Drâa-Tafilalet
    "Ouarzazate": {"lat": 30.9335, "lng": -6.9370, "region": "Drâa-Tafilalet"},
    "Errachidia": {"lat": 31.9314, "lng": -4.4244, "region": "Drâa-Tafilalet"},
    "Midelt": {"lat": 32.6852, "lng": -4.7333, "region": "Drâa-Tafilalet"},
    "Tinghir": {"lat": 31.5147, "lng": -5.5325, "region": "Drâa-Tafilalet"},

    # Guelmim-Oued Noun
    "Guelmim": {"lat": 28.9870, "lng": -10.0574, "region": "Guelmim-Oued Noun"},
    "Tan-Tan": {"lat": 28.4378, "lng": -11.1031, "region": "Guelmim-Oued Noun"},

    # Laâyoune-Sakia El Hamra
    "Laâyoune": {"lat": 27.1418, "lng": -13.1875, "region": "Laâyoune-Sakia El Hamra"},
    "Boujdour": {"lat": 26.1259, "lng": -14.4848, "region": "Laâyoune-Sakia El Hamra"},

    # Dakhla-Oued Ed-Dahab
    "Dakhla": {"lat": 23.6848, "lng": -15.9579, "region": "Dakhla-Oued Ed-Dahab"},
}


# Coordonnées par défaut au centre de chaque région
CENTRES_REGIONS = {
    "Casablanca-Settat": {"lat": 33.5731, "lng": -7.5898},
    "Rabat-Salé-Kénitra": {"lat": 34.0209, "lng": -6.8416},
    "Tanger-Tétouan-Al Hoceïma": {"lat": 35.5, "lng": -5.5},
    "Fès-Meknès": {"lat": 34.0, "lng": -5.0},
    "Marrakech-Safi": {"lat": 31.6295, "lng": -7.9811},
    "Oriental": {"lat": 34.6814, "lng": -1.9086},
    "Béni Mellal-Khénifra": {"lat": 32.3373, "lng": -6.3498},
    "Souss-Massa": {"lat": 30.4278, "lng": -9.5981},
    "Drâa-Tafilalet": {"lat": 31.5, "lng": -5.5},
    "Guelmim-Oued Noun": {"lat": 28.9870, "lng": -10.0574},
    "Laâyoune-Sakia El Hamra": {"lat": 27.1418, "lng": -13.1875},
    "Dakhla-Oued Ed-Dahab": {"lat": 23.6848, "lng": -15.9579},
}


def geocoder_intelligent(texte: str, region_connue: Optional[str] = None) -> Optional[Dict]:
    """
    Géocodage en cascade :
    1. Match direct par ville
    2. Identification IA de la ville
    3. Fallback centre de région
    """
    if not texte:
        if region_connue and region_connue in CENTRES_REGIONS:
            return {
                **CENTRES_REGIONS[region_connue],
                "ville": None,
                "region": region_connue,
                "source": "centre_region",
            }
        return None

    texte_lower = texte.lower()

    # === Étape 1 : Match direct ===
    for ville, coords in VILLES_MAROC.items():
        if ville.lower() in texte_lower:
            return {**coords, "ville": ville, "source": "match_direct"}

    # === Étape 2 : Identification IA ===
    try:
        result = llm.complete_json(PROMPT_GEOCODAGE.format(texte=texte[:500]))
        ville_norm = result.get("ville_normalisee")

        if ville_norm and ville_norm in VILLES_MAROC:
            return {
                **VILLES_MAROC[ville_norm],
                "ville": ville_norm,
                "source": "ia_match",
                "confiance": result.get("confiance", 0.7),
            }
    except Exception as e:
        logger.error(f"Erreur géocodage IA: {e}")

    # === Étape 3 : Fallback centre de région ===
    if region_connue and region_connue in CENTRES_REGIONS:
        return {
            **CENTRES_REGIONS[region_connue],
            "ville": None,
            "region": region_connue,
            "source": "centre_region_fallback",
        }

    return None
