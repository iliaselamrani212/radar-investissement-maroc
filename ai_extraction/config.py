"""
config.py - Configuration centrale du système Radar SDG Capital
Sources STRICTEMENT publiques et institutionnelles.
LLM : Ollama Qwen 2.5 7B en LOCAL (zéro coût, zéro clé API).
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ═══════════════════════════════════════════════════════════════
# OLLAMA - LLM LOCAL
# ═══════════════════════════════════════════════════════════════

# URL du serveur Ollama (défaut : localhost:11434)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Modèle utilisé - Qwen 2.5 7B (excellent multilingue, supporte le français)
# Variantes possibles : qwen2.5:7b, qwen2.5:7b-instruct, qwen2.5:14b
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

# Timeout pour les requêtes (en secondes)
# Qwen 7B sur GPU récent : ~5-15s par extraction
# Qwen 7B sur CPU : ~30-90s
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "180"))


# ═══════════════════════════════════════════════════════════════
# BASE DE DONNÉES
# ═══════════════════════════════════════════════════════════════

# SQLite par défaut (zero-config). PostgreSQL pour la production.
DATABASE_URL = os.getenv(
    "DATABASE_URL", "sqlite:///data/radar_sdg.db"
)


# ═══════════════════════════════════════════════════════════════
# SOURCES OFFICIELLES AUTORISÉES (15+)
# ═══════════════════════════════════════════════════════════════
# Sources STRICTEMENT publiques et institutionnelles
# JAMAIS de presse / RS / blogs

SOURCES_CONFIG = {
    "amdie": {
        "nom": "Agence Marocaine de Développement des Investissements",
        "url": "https://www.amdie.gov.ma/fr/actualites",
        "type": "html",
        "selectors": {"articles": "article.news", "title": "h2", "content": ".content"},
        "frequence_h": 1,
        "niveau_fiabilite": 5,
    },
    "data_gov_ma": {
        "nom": "Portail Open Data du Maroc",
        "url": "https://data.gov.ma/data/fr/group/finance",
        "type": "datasets",
        "formats": ["xlsx", "xls", "csv"],
        "frequence_h": 24,
        "niveau_fiabilite": 5,
    },
    "bulletin_officiel": {
        "nom": "Bulletin Officiel du Royaume",
        "url": "https://www.sgg.gov.ma/Legislation/BulletinsOfficiels",
        "type": "pdf",
        "extraction": "pdfplumber",
        "frequence_h": 24,
        "niveau_fiabilite": 5,
    },
    "mef": {
        "nom": "Ministère de l'Économie et des Finances",
        "url": "https://www.finances.gov.ma/fr/Pages/actualites.aspx",
        "type": "html",
        "frequence_h": 6,
        "niveau_fiabilite": 5,
    },
    "hcp": {
        "nom": "Haut-Commissariat au Plan",
        "url": "https://www.hcp.ma/Publications-recentes_a232.html",
        "type": "html",
        "frequence_h": 24,
        "niveau_fiabilite": 5,
    },
    "bkam": {
        "nom": "Bank Al-Maghrib",
        "url": "https://www.bkam.ma/Publications-et-recherche",
        "type": "html",
        "frequence_h": 24,
        "niveau_fiabilite": 5,
    },
    "casablanca_bourse": {
        "nom": "Bourse de Casablanca",
        "url": "https://www.casablanca-bourse.com/bourseweb/Actualite.aspx",
        "type": "html",
        "frequence_h": 6,
        "niveau_fiabilite": 5,
    },
    "ammc": {
        "nom": "Autorité Marocaine du Marché des Capitaux",
        "url": "https://www.ammc.ma/fr/espace-emetteurs/communiques",
        "type": "html",
        "frequence_h": 6,
        "niveau_fiabilite": 5,
    },
    "charika": {
        "nom": "Charika - Registre du commerce",
        "url": "https://www.charika.ma/actualites",
        "type": "js_dynamic",
        "tool": "playwright",
        "frequence_h": 6,
        "niveau_fiabilite": 5,
    },
    "masen": {
        "nom": "Moroccan Agency for Sustainable Energy",
        "url": "https://www.masen.ma/fr/actualites",
        "type": "html",
        "frequence_h": 12,
        "niveau_fiabilite": 5,
    },
    "onhym": {
        "nom": "Office National des Hydrocarbures et des Mines",
        "url": "https://www.onhym.com/actualites",
        "type": "html",
        "frequence_h": 24,
        "niveau_fiabilite": 5,
    },
    "tangermed": {
        "nom": "Autorité Portuaire Tanger Med",
        "url": "https://www.tangermed.ma/communiques",
        "type": "html",
        "frequence_h": 12,
        "niveau_fiabilite": 5,
    },
    "ocp_group": {
        "nom": "OCP Group - Communiqués",
        "url": "https://www.ocpgroup.ma/fr/media-center/communiques-de-presse",
        "type": "html",
        "frequence_h": 12,
        "niveau_fiabilite": 5,
    },
    "conseil_concurrence": {
        "nom": "Conseil de la Concurrence",
        "url": "https://www.conseil-concurrence.ma/fr/decisions",
        "type": "html",
        "frequence_h": 24,
        "niveau_fiabilite": 5,
    },
    "cri_casablanca": {
        "nom": "Centre Régional d'Investissement Casablanca-Settat",
        "url": "https://www.casainvest.ma/actualites",
        "type": "html",
        "frequence_h": 12,
        "niveau_fiabilite": 5,
    },
}


# ═══════════════════════════════════════════════════════════════
# SEUILS IA
# ═══════════════════════════════════════════════════════════════

SEUIL_CONFIANCE_MIN = 0.3        # En-dessous : projet rejeté
SEUIL_DEDUPLICATION = 0.85       # Cosine similarity pour doublons
SEUIL_TRIANGULATION = 0.80       # Cosine similarity pour triangulation


# ═══════════════════════════════════════════════════════════════
# TAUX DE CHANGE (référence)
# ═══════════════════════════════════════════════════════════════

TAUX_CHANGE = {
    "EUR": 11.0,    # 1 EUR ≈ 11 MAD
    "USD": 10.0,    # 1 USD ≈ 10 MAD
    "MAD": 1.0,
}


# ═══════════════════════════════════════════════════════════════
# MODÈLE D'EMBEDDINGS (pour déduplication / similarité)
# ═══════════════════════════════════════════════════════════════
# Local, gratuit, multilingue. ~120 MB téléchargé au premier usage.

EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
