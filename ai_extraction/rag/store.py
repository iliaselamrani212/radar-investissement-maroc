"""
rag/store.py - Vector store SQLite pour le RAG.

Stocke les chunks de texte + leur embedding (numpy float32 en BLOB).
Recherche par similarité cosine en mémoire (suffisant pour < 100k chunks).
Réutilise le modèle d'embeddings déjà chargé (paraphrase-multilingual-MiniLM-L12-v2).
"""
import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import List, Dict, Optional

import numpy as np

from ..database import DB_PATH
from ..dedup.embeddings_dedup import dedup_service

logger = logging.getLogger(__name__)

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS rag_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_type TEXT NOT NULL,          -- 'dataset' | 'projet'
    source TEXT,                     -- ex: 'data_gov_ma_finance'
    titre TEXT,
    url TEXT,
    ref_id TEXT,                     -- id du projet lié (si doc_type='projet')
    chunk_index INTEGER DEFAULT 0,
    contenu TEXT NOT NULL,
    embedding BLOB NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_rag_doctype ON rag_chunks(doc_type);
CREATE INDEX IF NOT EXISTS idx_rag_source ON rag_chunks(source);
CREATE INDEX IF NOT EXISTS idx_rag_ref ON rag_chunks(ref_id);
"""


@contextmanager
def _get_conn():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _embed(text: str) -> np.ndarray:
    """Embedding via le modèle sentence-transformers partagé."""
    vec = dedup_service.model.encode(text)
    return np.asarray(vec, dtype=np.float32)


# Cache mémoire de l'index complet (rechargé seulement si l'index change).
# Évite de relire + restacker tous les embeddings SQLite à chaque question.
_INDEX_CACHE: Dict[str, object] = {"meta": None, "matrix": None}


def _invalider_cache():
    _INDEX_CACHE["meta"] = None
    _INDEX_CACHE["matrix"] = None


def _charger_index():
    """Charge (une fois) toutes les lignes + matrice d'embeddings normalisée."""
    if _INDEX_CACHE["meta"] is not None:
        return _INDEX_CACHE["meta"], _INDEX_CACHE["matrix"]

    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT id, doc_type, source, titre, url, ref_id, contenu, embedding "
            "FROM rag_chunks"
        ).fetchall()

    if not rows:
        _INDEX_CACHE["meta"] = []
        _INDEX_CACHE["matrix"] = None
        return [], None

    meta = [
        {
            "id": r["id"],
            "doc_type": r["doc_type"],
            "source": r["source"],
            "titre": r["titre"],
            "url": r["url"],
            "ref_id": r["ref_id"],
            "contenu": r["contenu"],
        }
        for r in rows
    ]
    matrix = np.stack(
        [np.frombuffer(r["embedding"], dtype=np.float32) for r in rows]
    )
    matrix = matrix / (np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-9)

    _INDEX_CACHE["meta"] = meta
    _INDEX_CACHE["matrix"] = matrix
    return meta, matrix


class RagStore:
    """Vector store minimaliste adossé à SQLite."""

    def init(self):
        with _get_conn() as conn:
            conn.executescript(SCHEMA_SQL)
        logger.info("RAG store initialisé")

    def compter(self, doc_type: Optional[str] = None) -> int:
        with _get_conn() as conn:
            if doc_type:
                row = conn.execute(
                    "SELECT COUNT(*) FROM rag_chunks WHERE doc_type = ?", (doc_type,)
                ).fetchone()
            else:
                row = conn.execute("SELECT COUNT(*) FROM rag_chunks").fetchone()
            return row[0]

    def stats(self) -> Dict:
        with _get_conn() as conn:
            total = conn.execute("SELECT COUNT(*) FROM rag_chunks").fetchone()[0]
            par_source = [
                dict(r)
                for r in conn.execute(
                    "SELECT source, COUNT(*) as nb FROM rag_chunks GROUP BY source"
                ).fetchall()
            ]
        return {"total_chunks": total, "par_source": par_source}

    def purge(self, doc_type: Optional[str] = None):
        with _get_conn() as conn:
            if doc_type:
                conn.execute("DELETE FROM rag_chunks WHERE doc_type = ?", (doc_type,))
            else:
                conn.execute("DELETE FROM rag_chunks")
        _invalider_cache()
        logger.info(f"RAG store purgé ({doc_type or 'tout'})")

    def supprimer_doc(self, doc_type: str, ref_id: str):
        with _get_conn() as conn:
            conn.execute(
                "DELETE FROM rag_chunks WHERE doc_type = ? AND ref_id = ?",
                (doc_type, ref_id),
            )
        _invalider_cache()

    def supprimer_par_url(self, url: str):
        if not url:
            return
        with _get_conn() as conn:
            conn.execute("DELETE FROM rag_chunks WHERE url = ?", (url,))
        _invalider_cache()

    def ajouter_chunks(
        self,
        chunks: List[str],
        doc_type: str,
        source: str = "",
        titre: str = "",
        url: str = "",
        ref_id: str = "",
    ) -> int:
        """Embed et insère une liste de chunks. Retourne le nombre inséré."""
        chunks = [c.strip() for c in chunks if c and c.strip()]
        if not chunks:
            return 0

        rows = []
        for i, contenu in enumerate(chunks):
            emb = _embed(contenu)
            rows.append(
                (
                    doc_type,
                    source,
                    titre,
                    url,
                    ref_id,
                    i,
                    contenu,
                    emb.tobytes(),
                )
            )

        with _get_conn() as conn:
            conn.executemany(
                """INSERT INTO rag_chunks
                   (doc_type, source, titre, url, ref_id, chunk_index, contenu, embedding)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                rows,
            )
        _invalider_cache()
        logger.info(f"{len(rows)} chunk(s) indexé(s) [{doc_type}/{source}]")
        return len(rows)

    def rechercher(
        self,
        question: str,
        top_k: int = 5,
        doc_type: Optional[str] = None,
        ref_id: Optional[str] = None,
    ) -> List[Dict]:
        """
        Recherche les top_k chunks les plus proches de la question.
        Filtres optionnels par doc_type et/ou ref_id (projet précis).
        """
        meta, matrix = _charger_index()
        if not meta or matrix is None:
            return []

        q = _embed(question)
        q = q / (np.linalg.norm(q) + 1e-9)
        sims = matrix @ q  # cosine (matrice déjà normalisée, cache mémoire)

        # Filtrage en mémoire (indices conservés)
        indices = range(len(meta))
        if doc_type:
            indices = [i for i in indices if meta[i]["doc_type"] == doc_type]
        if ref_id:
            indices = [i for i in indices if meta[i]["ref_id"] == ref_id]
        indices = list(indices)
        if not indices:
            return []

        indices.sort(key=lambda i: sims[i], reverse=True)
        resultats = []
        for i in indices[:top_k]:
            r = dict(meta[i])
            r["score"] = round(float(sims[i]), 4)
            resultats.append(r)
        return resultats


rag_store = RagStore()
