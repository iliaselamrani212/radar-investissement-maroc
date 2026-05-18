"""
rag/ingestion.py - Alimente le vector store RAG.

Source principale : datasets du groupe "finance" de data.gov.ma (portail CKAN).
On télécharge les ressources (xlsx/xls/csv), on les transforme en passages
texte lisibles, puis on les indexe.

On indexe aussi les projets détectés pour que le RAG puisse répondre à des
questions croisant un projet et les données macro-financières officielles.
"""
import io
import logging
from typing import List, Dict, Optional

import requests

from .store import rag_store
from ..config import SOURCES_CONFIG

logger = logging.getLogger(__name__)

CKAN_BASE = "https://data.gov.ma/data"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9",
}
TIMEOUT = 30
LIGNES_PAR_CHUNK = 12
MAX_DATASETS = 20
MAX_RESSOURCES_PAR_DATASET = 3

# Découpage de texte libre (pages web / PDF)
TAILLE_CHUNK_TEXTE = 900      # caractères par passage
CHEVAUCHEMENT = 150           # caractères de recouvrement entre passages


def _decouper_texte(texte: str) -> List[str]:
    """
    Découpe un texte libre (article web, PDF) en passages avec chevauchement.
    On coupe de préférence sur une fin de phrase proche de la limite.
    """
    texte = " ".join((texte or "").split())
    if not texte:
        return []
    if len(texte) <= TAILLE_CHUNK_TEXTE:
        return [texte]

    chunks = []
    debut = 0
    n = len(texte)
    while debut < n:
        fin = min(debut + TAILLE_CHUNK_TEXTE, n)
        if fin < n:
            # cherche une fin de phrase entre fin-200 et fin
            fenetre = texte[max(debut, fin - 200):fin]
            coupe = max(
                fenetre.rfind(". "), fenetre.rfind("? "), fenetre.rfind("! ")
            )
            if coupe != -1:
                fin = max(debut, fin - 200) + coupe + 1
        chunks.append(texte[debut:fin].strip())
        if fin >= n:
            break
        debut = max(fin - CHEVAUCHEMENT, debut + 1)
    return [c for c in chunks if c]


# ═══════════════════════════════════════════════════════════════
# DÉCOUVERTE DES RESSOURCES VIA L'API CKAN
# ═══════════════════════════════════════════════════════════════

def _lister_ressources_finance() -> List[Dict]:
    """
    Interroge l'API CKAN de data.gov.ma pour lister les ressources
    téléchargeables du groupe 'finance'.
    """
    ressources = []
    try:
        url = f"{CKAN_BASE}/api/3/action/package_search"
        params = {"fq": "groups:finance", "rows": MAX_DATASETS}
        resp = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT, verify=False)
        resp.raise_for_status()
        data = resp.json()
        packages = data.get("result", {}).get("results", [])

        for pkg in packages:
            titre_dataset = pkg.get("title") or pkg.get("name", "")
            for res in pkg.get("resources", [])[:MAX_RESSOURCES_PAR_DATASET]:
                fmt = (res.get("format") or "").lower()
                if fmt in ("xlsx", "xls", "csv"):
                    ressources.append(
                        {
                            "titre": titre_dataset,
                            "resource_name": res.get("name") or titre_dataset,
                            "url": res.get("url"),
                            "format": fmt,
                        }
                    )
        logger.info(f"CKAN : {len(ressources)} ressource(s) finance trouvée(s)")
    except Exception as e:
        logger.warning(f"API CKAN indisponible ({e}) — fallback scraping HTML")
        ressources = _fallback_scraping_html()

    return ressources


def _fallback_scraping_html() -> List[Dict]:
    """Si l'API CKAN échoue, scrape la page groupe finance pour les liens fichiers."""
    from bs4 import BeautifulSoup
    from urllib.parse import urljoin

    url = SOURCES_CONFIG.get("data_gov_ma_finance", {}).get(
        "url", "https://data.gov.ma/data/fr/group/finance"
    )
    ressources = []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, verify=False)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"].lower()
            for fmt in ("xlsx", "xls", "csv"):
                if href.endswith(f".{fmt}"):
                    ressources.append(
                        {
                            "titre": a.get_text(strip=True) or "Dataset finance",
                            "resource_name": a.get_text(strip=True) or "ressource",
                            "url": urljoin(url, a["href"]),
                            "format": fmt,
                        }
                    )
    except Exception as e:
        logger.error(f"Fallback scraping échoué : {e}")
    return ressources[:MAX_DATASETS]


# ═══════════════════════════════════════════════════════════════
# TÉLÉCHARGEMENT + DÉCOUPAGE EN CHUNKS
# ═══════════════════════════════════════════════════════════════

def _telecharger(url: str) -> Optional[bytes]:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=60, verify=False)
        resp.raise_for_status()
        return resp.content
    except Exception as e:
        logger.warning(f"Téléchargement échoué {url}: {e}")
        return None


def _fichier_vers_chunks(contenu: bytes, fmt: str, titre: str) -> List[str]:
    """Transforme un fichier tabulaire en passages texte lisibles."""
    try:
        import pandas as pd
    except ImportError:
        logger.error("pandas requis : pip install pandas openpyxl")
        return []

    chunks: List[str] = []

    try:
        if fmt == "csv":
            feuilles = {"data": pd.read_csv(io.BytesIO(contenu), sep=None, engine="python")}
        else:
            xl = pd.ExcelFile(io.BytesIO(contenu))
            feuilles = {s: xl.parse(s) for s in xl.sheet_names}
    except Exception as e:
        logger.warning(f"Parsing '{titre}' échoué : {e}")
        return []

    for nom_feuille, df in feuilles.items():
        if df is None or df.empty:
            continue
        df = df.dropna(how="all").fillna("")
        colonnes = [str(c) for c in df.columns]
        entete = f"Dataset officiel : {titre} | Feuille : {nom_feuille} | Colonnes : {', '.join(colonnes)}"

        lignes_txt = []
        for _, row in df.iterrows():
            cellules = [
                f"{col}: {str(row[col]).strip()}"
                for col in df.columns
                if str(row[col]).strip()
            ]
            if cellules:
                lignes_txt.append(" | ".join(cellules))

        for i in range(0, len(lignes_txt), LIGNES_PAR_CHUNK):
            bloc = lignes_txt[i : i + LIGNES_PAR_CHUNK]
            chunks.append(entete + "\n" + "\n".join(bloc))

    return chunks


# ═══════════════════════════════════════════════════════════════
# API PUBLIQUE
# ═══════════════════════════════════════════════════════════════

def ingerer_datasets_finance(reset: bool = True) -> Dict:
    """
    Télécharge et indexe les datasets finance de data.gov.ma.
    reset=True purge l'index dataset existant avant ré-ingestion.
    """
    rag_store.init()
    if reset:
        rag_store.purge(doc_type="dataset")

    ressources = _lister_ressources_finance()
    stats = {"ressources": 0, "chunks": 0, "erreurs": 0}

    for res in ressources:
        if not res.get("url"):
            continue
        contenu = _telecharger(res["url"])
        if not contenu:
            stats["erreurs"] += 1
            continue

        chunks = _fichier_vers_chunks(contenu, res["format"], res["titre"])
        if not chunks:
            stats["erreurs"] += 1
            continue

        n = rag_store.ajouter_chunks(
            chunks=chunks,
            doc_type="dataset",
            source="data_gov_ma_finance",
            titre=res["titre"],
            url=res["url"],
        )
        stats["ressources"] += 1
        stats["chunks"] += n

    logger.info(f"Ingestion finance terminée : {stats}")
    return stats


def ingerer_projets(projets: List, reset: bool = True) -> Dict:
    """
    Indexe les projets détectés (titre, description, fiche) pour permettre
    au RAG de répondre à des questions projet + croisement données finance.
    """
    rag_store.init()
    if reset:
        rag_store.purge(doc_type="projet")

    total = 0
    for p in projets:
        d = p.model_dump() if hasattr(p, "model_dump") else dict(p)
        morceaux = [
            f"Projet : {d.get('titre', '')}",
            f"Secteur : {d.get('secteur', '')} / {d.get('sous_secteur', '') or 'N/A'}",
            f"Région : {d.get('region', '') or 'N/A'} - Ville : {d.get('ville', '') or 'N/A'}",
            f"Porteur : {d.get('porteur', '') or 'N/A'}",
            f"Montant : {d.get('montant_mad', '') or 'Non précisé'} MAD",
            f"Stade : {d.get('stade_avancement', '') or 'N/A'}",
            f"Description : {d.get('description', '') or ''}",
            f"Fiche : {d.get('fiche_synthetique', '') or ''}",
        ]
        contenu = "\n".join(m for m in morceaux if m.split(":", 1)[-1].strip())
        n = rag_store.ajouter_chunks(
            chunks=[contenu],
            doc_type="projet",
            source=d.get("source_principale", "projet"),
            titre=d.get("titre", ""),
            url=d.get("url_source", ""),
            ref_id=str(d.get("id", "")),
        )
        total += n

    logger.info(f"Ingestion projets terminée : {total} projet(s) indexé(s)")
    return {"projets_indexes": total}


def ingerer_source_scrapee(
    titre: str,
    contenu: str,
    url: str,
    source: str,
    projet_id: str = "",
) -> int:
    """
    Indexe le CONTENU BRUT d'une source scrapée (page web ou texte PDF).
    Si projet_id est fourni, les passages sont liés au projet : le RAG
    pourra retrouver exactement la source d'où l'info du projet provient.

    Idempotent par URL : re-scraper la même source remplace ses anciens chunks.
    """
    if not contenu or len(contenu.strip()) < 100:
        return 0

    rag_store.init()
    if url:
        rag_store.supprimer_par_url(url)

    chunks = _decouper_texte(contenu)
    if not chunks:
        return 0

    return rag_store.ajouter_chunks(
        chunks=chunks,
        doc_type="source",
        source=source,
        titre=titre or source,
        url=url,
        ref_id=str(projet_id or ""),
    )
