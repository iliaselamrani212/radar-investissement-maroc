"""
database.py - Couche de persistance
Aligné avec LIVRABLE 2 : "Base de données structurée des projets"

Utilise SQLite par défaut (zero-config, parfait pour MVP 48h).
Migrable vers PostgreSQL en production via DATABASE_URL.
"""
import json
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from .models import ProjetInvestissement, SourceArticle

logger = logging.getLogger(__name__)

DB_PATH = str(Path(__file__).resolve().parent.parent / "data" / "radar_sdg.db")


# ═══════════════════════════════════════════════════════════════
# SCHÉMA DE LA BASE
# ═══════════════════════════════════════════════════════════════

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS projets (
    id TEXT PRIMARY KEY,
    -- 5 champs critiques
    montant_mad REAL,
    secteur TEXT NOT NULL,
    region TEXT,
    porteur TEXT,
    stade_avancement TEXT DEFAULT 'annonce',
    -- Métadonnées
    titre TEXT NOT NULL,
    description TEXT,
    date_annonce TEXT,
    devise_originale TEXT DEFAULT 'MAD',
    -- Enrichissements
    sous_secteur TEXT,
    type_projet TEXT,
    nombre_emplois INTEGER,
    horizon_temporel_annees INTEGER,
    tags_esg TEXT,                -- JSON list
    strategies_nationales TEXT,   -- JSON list
    -- Géocodage
    ville TEXT,
    latitude REAL,
    longitude REAL,
    -- Fiabilité
    score_confiance_extraction REAL DEFAULT 0.5,
    score_fiabilite REAL,
    score_details TEXT,
    sources TEXT,                 -- JSON list
    nb_sources_confirmees INTEGER DEFAULT 1,
    source_principale TEXT,
    url_source TEXT,
    -- Contexte
    contexte_macro TEXT,          -- JSON dict
    fiche_synthetique TEXT,
    anomalies TEXT,               -- JSON list
    -- Horodatage
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS articles_bruts (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    url TEXT,
    title TEXT,
    content TEXT,
    snippet TEXT,
    type_document TEXT,
    fetched_at TEXT DEFAULT CURRENT_TIMESTAMP,
    processed INTEGER DEFAULT 0,
    niveau_fiabilite INTEGER DEFAULT 5
);

CREATE TABLE IF NOT EXISTS alertes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    projet_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    pertinence_score INTEGER,
    urgence TEXT,
    raison_alerte TEXT,
    actions_suggerees TEXT,       -- JSON list
    lue INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS profils_utilisateurs (
    user_id TEXT PRIMARY KEY,
    secteurs TEXT,                -- JSON list
    regions TEXT,                 -- JSON list
    montant_min REAL DEFAULT 0,
    stades TEXT,                  -- JSON list
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS scoring_config (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    poids_source REAL NOT NULL DEFAULT 0.30,
    poids_triangulation REAL NOT NULL DEFAULT 0.30,
    poids_precision REAL NOT NULL DEFAULT 0.15,
    poids_fraicheur REAL NOT NULL DEFAULT 0.15,
    poids_llm REAL NOT NULL DEFAULT 0.10,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS veille_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    status TEXT NOT NULL,
    nb_projets INTEGER DEFAULT 0,
    rapport_markdown TEXT,
    error TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_secteur ON projets(secteur);
CREATE INDEX IF NOT EXISTS idx_region ON projets(region);
CREATE INDEX IF NOT EXISTS idx_stade ON projets(stade_avancement);
CREATE INDEX IF NOT EXISTS idx_montant ON projets(montant_mad);
CREATE INDEX IF NOT EXISTS idx_fiabilite ON projets(score_fiabilite);
"""


# ═══════════════════════════════════════════════════════════════
# CONNEXION
# ═══════════════════════════════════════════════════════════════

@contextmanager
def get_conn():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def init_db():
    """Initialise la base de données (à appeler au démarrage)"""
    with get_conn() as conn:
        conn.executescript(SCHEMA_SQL)
        try:
            conn.execute("ALTER TABLE projets ADD COLUMN score_details TEXT")
        except sqlite3.OperationalError:
            pass
        conn.execute("""
            INSERT OR IGNORE INTO scoring_config (
                id, poids_source, poids_triangulation, poids_precision,
                poids_fraicheur, poids_llm
            ) VALUES (1, 0.30, 0.30, 0.15, 0.15, 0.10)
        """)
    logger.info(f"✅ Base initialisée : {DB_PATH}")


# ═══════════════════════════════════════════════════════════════
# OPÉRATIONS PROJETS
# ═══════════════════════════════════════════════════════════════

def save_projet(projet: ProjetInvestissement) -> str:
    """Sauvegarde ou met à jour un projet"""
    if not projet.id:
        projet.id = _generer_id(projet)

    projet.updated_at = datetime.now()

    data = projet.model_dump()
    # Sérialisation JSON pour les champs complexes
    data["tags_esg"] = json.dumps(data.get("tags_esg", []))
    data["strategies_nationales"] = json.dumps(data.get("strategies_nationales", []))
    data["sources"] = json.dumps(data.get("sources", []))
    data["anomalies"] = json.dumps(data.get("anomalies", []))
    data["contexte_macro"] = json.dumps(data.get("contexte_macro", {}))
    data["score_details"] = json.dumps(data.get("score_details") or {})
    # Dates en string ISO
    if data.get("date_annonce"):
        data["date_annonce"] = str(data["date_annonce"])
    data["created_at"] = data["created_at"].isoformat() if hasattr(data["created_at"], "isoformat") else str(data["created_at"])
    data["updated_at"] = data["updated_at"].isoformat() if hasattr(data["updated_at"], "isoformat") else str(data["updated_at"])

    with get_conn() as conn:
        colonnes = ", ".join(data.keys())
        placeholders = ", ".join(f":{k}" for k in data.keys())
        sql = f"INSERT OR REPLACE INTO projets ({colonnes}) VALUES ({placeholders})"
        conn.execute(sql, data)

    logger.info(f"💾 Projet sauvegardé : {projet.id} - {projet.titre[:50]}")
    return projet.id


def get_projet(projet_id: str) -> Optional[ProjetInvestissement]:
    """Récupère un projet par ID"""
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM projets WHERE id = ?", (projet_id,)).fetchone()
        if not row:
            return None
        return _row_to_projet(row)


def get_all_projets(
    limit: int = 1000,
    secteur: Optional[str] = None,
    region: Optional[str] = None,
    stade: Optional[str] = None,
    montant_min: Optional[float] = None,
) -> List[ProjetInvestissement]:
    """Récupère tous les projets avec filtres optionnels"""
    sql = "SELECT * FROM projets WHERE 1=1"
    params = []

    if secteur:
        sql += " AND secteur = ?"
        params.append(secteur)
    if region:
        sql += " AND region = ?"
        params.append(region)
    if stade:
        sql += " AND stade_avancement = ?"
        params.append(stade)
    if montant_min is not None:
        sql += " AND montant_mad >= ?"
        params.append(montant_min)

    sql += " ORDER BY score_fiabilite DESC, montant_mad DESC LIMIT ?"
    params.append(limit)

    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
        return [_row_to_projet(r) for r in rows]


def delete_projet(projet_id: str):
    """Supprime un projet"""
    with get_conn() as conn:
        conn.execute("DELETE FROM projets WHERE id = ?", (projet_id,))


# ═══════════════════════════════════════════════════════════════
# OPÉRATIONS ARTICLES BRUTS
# ═══════════════════════════════════════════════════════════════

def save_article_brut(article: SourceArticle) -> str:
    """Sauvegarde un article brut (pour triangulation future)"""
    if not article.id:
        import hashlib
        article.id = hashlib.md5(
            f"{article.source}-{article.url}-{article.title}".encode()
        ).hexdigest()[:12]

    data = article.model_dump()
    data["fetched_at"] = data["fetched_at"].isoformat()
    data["processed"] = int(data["processed"])

    with get_conn() as conn:
        sql = """
            INSERT OR REPLACE INTO articles_bruts 
            (id, source, url, title, content, snippet, type_document,
             fetched_at, processed, niveau_fiabilite)
            VALUES (:id, :source, :url, :title, :content, :snippet, :type_document,
                    :fetched_at, :processed, :niveau_fiabilite)
        """
        conn.execute(sql, data)
    return article.id


def get_articles_bruts(processed: bool = None) -> List[SourceArticle]:
    """Récupère les articles bruts"""
    sql = "SELECT * FROM articles_bruts"
    params = []
    if processed is not None:
        sql += " WHERE processed = ?"
        params.append(int(processed))

    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
        articles = []
        for r in rows:
            d = dict(r)
            d["processed"] = bool(d["processed"])
            articles.append(SourceArticle(**d))
        return articles


# ═══════════════════════════════════════════════════════════════
# OPÉRATIONS ALERTES
# ═══════════════════════════════════════════════════════════════

def save_alerte(alerte) -> int:
    """Sauvegarde une alerte"""
    data = alerte.model_dump()
    data["actions_suggerees"] = json.dumps(data.get("actions_suggerees", []))
    data["created_at"] = data["created_at"].isoformat()

    with get_conn() as conn:
        cursor = conn.execute("""
            INSERT INTO alertes 
            (projet_id, user_id, pertinence_score, urgence, raison_alerte,
             actions_suggerees, created_at)
            VALUES (:projet_id, :user_id, :pertinence_score, :urgence,
                    :raison_alerte, :actions_suggerees, :created_at)
        """, data)
        return cursor.lastrowid


def get_alertes_user(user_id: str, non_lues_seulement: bool = False) -> List[Dict]:
    """Récupère les alertes d'un utilisateur"""
    sql = "SELECT * FROM alertes WHERE user_id = ?"
    if non_lues_seulement:
        sql += " AND lue = 0"
    sql += " ORDER BY created_at DESC"

    with get_conn() as conn:
        rows = conn.execute(sql, (user_id,)).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["actions_suggerees"] = json.loads(d.get("actions_suggerees") or "[]")
            result.append(d)
        return result


def get_scoring_config() -> Dict[str, Any]:
    """Retourne la configuration active du scoring."""
    init_db()
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM scoring_config WHERE id = 1").fetchone()
        return dict(row)


def update_scoring_config(config: Dict[str, float]) -> Dict[str, Any]:
    """Met a jour les ponderations du scoring."""
    champs = [
        "poids_source", "poids_triangulation", "poids_precision",
        "poids_fraicheur", "poids_llm",
    ]
    valeurs = {champ: float(config.get(champ, 0)) for champ in champs}
    total = sum(valeurs.values())
    if abs(total - 1.0) > 0.001:
        raise ValueError("La somme des poids doit etre egale a 1.0")

    with get_conn() as conn:
        conn.execute("""
            UPDATE scoring_config
            SET poids_source = :poids_source,
                poids_triangulation = :poids_triangulation,
                poids_precision = :poids_precision,
                poids_fraicheur = :poids_fraicheur,
                poids_llm = :poids_llm,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
        """, valeurs)
    return get_scoring_config()


def save_veille_run(status: str, nb_projets: int = 0, rapport_markdown: str = "", error: str = "") -> int:
    """Journalise une execution de veille automatique."""
    with get_conn() as conn:
        cursor = conn.execute("""
            INSERT INTO veille_runs (status, nb_projets, rapport_markdown, error)
            VALUES (?, ?, ?, ?)
        """, (status, nb_projets, rapport_markdown, error))
        return cursor.lastrowid


def get_last_veille_run() -> Optional[Dict[str, Any]]:
    init_db()
    with get_conn() as conn:
        row = conn.execute("""
            SELECT * FROM veille_runs ORDER BY created_at DESC, id DESC LIMIT 1
        """).fetchone()
        return dict(row) if row else None


# ═══════════════════════════════════════════════════════════════
# STATISTIQUES POUR DASHBOARD (LIVRABLE 1)
# ═══════════════════════════════════════════════════════════════

def stats_globales() -> Dict[str, Any]:
    """Statistiques globales pour le dashboard"""
    with get_conn() as conn:
        # Compteurs
        total = conn.execute("SELECT COUNT(*) FROM projets").fetchone()[0]
        total_montant = conn.execute(
            "SELECT SUM(montant_mad) FROM projets WHERE montant_mad IS NOT NULL"
        ).fetchone()[0] or 0

        # Par secteur
        par_secteur = [
            dict(r) for r in conn.execute("""
                SELECT secteur,
                       COUNT(*) as nb,
                       COALESCE(SUM(montant_mad), 0) as total_mad
                FROM projets
                GROUP BY secteur
                ORDER BY total_mad DESC
            """).fetchall()
        ]

        # Par région
        par_region = [
            dict(r) for r in conn.execute("""
                SELECT region,
                       COUNT(*) as nb,
                       COALESCE(SUM(montant_mad), 0) as total_mad
                FROM projets
                WHERE region IS NOT NULL
                GROUP BY region
                ORDER BY total_mad DESC
            """).fetchall()
        ]

        # Par stade
        par_stade = [
            dict(r) for r in conn.execute("""
                SELECT stade_avancement, COUNT(*) as nb
                FROM projets
                GROUP BY stade_avancement
            """).fetchall()
        ]

        return {
            "total_projets": total,
            "total_investissement_mad": total_montant,
            "total_investissement_mds": round(total_montant / 1e9, 2),
            "par_secteur": par_secteur,
            "par_region": par_region,
            "par_stade": par_stade,
        }


# ═══════════════════════════════════════════════════════════════
# UTILS
# ═══════════════════════════════════════════════════════════════

def _generer_id(projet: ProjetInvestissement) -> str:
    """Génère un ID stable basé sur le contenu"""
    import hashlib
    base = f"{projet.titre}-{projet.porteur}-{projet.region}-{projet.secteur}"
    return hashlib.md5(base.encode()).hexdigest()[:12]


def _row_to_projet(row) -> ProjetInvestissement:
    """Convertit une row SQLite en ProjetInvestissement"""
    d = dict(row)
    # Désérialise les JSON
    for champ in ["tags_esg", "strategies_nationales", "sources", "anomalies"]:
        try:
            d[champ] = json.loads(d.get(champ) or "[]")
        except Exception:
            d[champ] = []
    for champ in ["contexte_macro", "score_details"]:
        try:
            d[champ] = json.loads(d.get(champ) or "{}")
        except Exception:
            d[champ] = {}

    return ProjetInvestissement(**{k: v for k, v in d.items() if v is not None})
