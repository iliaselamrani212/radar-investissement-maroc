"""
config.py - Configuration centrale du systeme InvestiGator 43
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

# ═══════════════════════════════════════════════════════════════
# SOURCES OFFICIELLES AUTORISÉES (15+)
# ═══════════════════════════════════════════════════════════════
# Sources STRICTEMENT publiques et institutionnelles
# JAMAIS de presse / RS / blogs
SOURCES_CONFIG = {
    "masen": {
        "nom": "MASEN — Moroccan Agency for Sustainable Energy",
        "url": "https://www.masen.ma/fr/actualites-masen",
        "type": "html",
        "selectors": {
            "articles": ".view-content .views-row, .views-row, article",
            "title": "h2, h3, .field-content",
            "content": "p",
            "date": ".date-display-single, time"
        },
        "frequence_h": 12,
        "niveau_fiabilite": 5,
    },

    "mef": {
        "nom": "MEF — Ministère de l'Économie et des Finances",
        "url": "https://www.finances.gov.ma/fr/Pages/index.aspx",
        "type": "html",
        "selectors": {
            "articles": "a[href*='detail-actualite.aspx'], .actualite, .news-item",
            "title": "a, h2, h3",
            "content": "p"
        },
        "frequence_h": 6,
        "niveau_fiabilite": 5,
    },

    "tangermed": {
        "nom": "Tanger Med — Communiqués de presse",
        "url": "https://www.tangermed.ma/fr/communiques-de-presse/",
        "type": "html",
        "selectors": {
            "articles": ".post, article, .communique, .elementor-post, .item",
            "title": "h2, h3",
            "content": "p",
            "date": "time, .date"
        },
        "frequence_h": 12,
        "niveau_fiabilite": 5,
    },

    "ammc_emetteurs": {
        "nom": "AMMC — Communiqués de presse des émetteurs",
        "url": "https://www.ammc.ma/fr/communiques-presse-emetteurs",
        "type": "html_pdf",
        "selectors": {
            "articles": ".views-row, article, li",
            "title": "h2, h3, a",
            "content": "p",
            "date": ".date-display-single, time"
        },
        "frequence_h": 6,
        "niveau_fiabilite": 5,
    },

    "ammc_actualites": {
        "nom": "AMMC — Communiqués de presse",
        "url": "https://www.ammc.ma/fr/actualites/communique-presse",
        "type": "html_pdf",
        "selectors": {
            "articles": ".views-row, article, li",
            "title": "h2, h3, a",
            "content": "p",
            "date": ".date-display-single, time"
        },
        "frequence_h": 6,
        "niveau_fiabilite": 5,
    },

    "casablanca_bourse_emetteurs": {
        "nom": "Bourse de Casablanca — Publications des émetteurs",
        "url": "https://www.casablanca-bourse.com/fr/publications-des-emetteurs",
        "type": "html_pdf",
        "selectors": {
            "articles": ".views-row, article, tr, .item",
            "title": "h2, h3, a",
            "content": "p, td",
            "date": "time, .date"
        },
        "frequence_h": 6,
        "niveau_fiabilite": 5,
    },

    "hcp_conjoncture": {
        "nom": "HCP — Conjoncture et prévision économique",
        "url": "https://www.hcp.ma/Actualite-Conjoncture-et-prevision-economique_r329.html",
        "type": "html",
        "selectors": {
            "articles": "article, .post, .item, .news, div",
            "title": "h2, h3, a",
            "content": "p",
            "date": "time, .date"
        },
        "frequence_h": 24,
        "niveau_fiabilite": 5,
    },

    "bkam_publications": {
        "nom": "Bank Al-Maghrib — Catalogue des publications",
        "url": "https://www.bkam.ma/Publications-et-recherche/Catalogue-des-publications",
        "type": "html_pdf",
        "selectors": {
            "articles": "article, .item, li",
            "title": "h2, h3, a",
            "content": "p"
        },
        "frequence_h": 24,
        "niveau_fiabilite": 5,
    },

    "ocp_group_actualites": {
        "nom": "OCP Group — Actualités",
        "url": "https://www.ocpgroup.ma/fr/media/actualites",
        "type": "html",
        "selectors": {
            "articles": ".views-row, article, .card, .item",
            "title": "h2, h3, a",
            "content": "p",
            "date": "time, .date"
        },
        "frequence_h": 12,
        "niveau_fiabilite": 5,
    },

    "onhym": {
        "nom": "ONHYM — Actualités",
        "url": "https://www.onhym.com/fr",
        "type": "html",
        "selectors": {
            "articles": ".news, .actualite, article, .item",
            "title": "h2, h3, a",
            "content": "p",
            "date": "time, .date"
        },
        "frequence_h": 24,
        "niveau_fiabilite": 5,
    },

    "cri_casablanca": {
        "nom": "CRI Casablanca-Settat — Actualités investissement",
        "url": "https://casainvest.ma/fr/actualites",
        "type": "html",
        "selectors": {
            "articles": "article, .item, .views-row, li",
            "title": "h2, h3, a",
            "content": "p",
            "date": "time, .date"
        },
        "frequence_h": 12,
        "niveau_fiabilite": 5,
    },

    "bulletin_officiel": {
        "nom": "Bulletin Officiel du Royaume",
        "url": "https://www.sgg.gov.ma/BulletinOfficiel.aspx",
        "type": "pdf",
        "extraction": "pdfplumber",
        "frequence_h": 24,
        "niveau_fiabilite": 5,
    },

    "data_gov_ma_finance": {
        "nom": "Open Data Finance",
        "url": "https://data.gov.ma/data/fr/group/finance",
        "type": "datasets",
        "formats": ["xlsx", "xls", "csv", "zip"],
        "frequence_h": 24,
        "niveau_fiabilite": 5,
    },

    "charika": {
        "nom": "Charika — Actualités entreprises",
        "url": "https://www.charika.ma/actualites",
        "type": "html",
        "selectors": {
            "articles": "article, .item, .post, li",
            "title": "h2, h3, a",
            "content": "p",
            "date": "time, .date"
        },
        "frequence_h": 6,
        "niveau_fiabilite": 4,
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
