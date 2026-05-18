"""
scraper.py - Collecteur HAUTE PERFORMANCE depuis les sources officielles.

Améliorations majeures :
  - Collecte PARALLÈLE des sources et des articles (ThreadPoolExecutor)
  - Rotation User-Agent + warming de session (contournement WAF / 403)
  - Découverte RSS/Atom + sitemap (plus fiable que le scraping HTML)
  - Pagination automatique (récupère les articles plus anciens)
  - Retry exponentiel + fallback SSL
  - Cache anti-doublon par URL+hash (n'appelle pas le LLM 2x sur le même contenu)
  - Pré-filtre par mots-clés d'investissement (économise massivement Ollama)
  - Extraction de contenu type "readability" (bloc le plus dense)
  - Indexation RAG du contenu brut, liée au projet détecté

API publique conservée :
    lancer_scraping(sources=None) -> dict
    collecter_source(source_id) -> list[dict]
"""
import hashlib
import logging
import random
import re
import sqlite3
import time
import urllib3
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .config import SOURCES_CONFIG
from .database import init_db, get_all_projets, save_projet, DB_PATH
from .pipeline import traiter_nouveau_document

logger = logging.getLogger(__name__)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ───────────────────────── Réglages ─────────────────────────
TIMEOUT = 25
MAX_ARTICLES_PAR_SOURCE = 15
MAX_PAGES_PAGINATION = 3
MIN_CONTENT_LENGTH = 180
PARALLEL_SOURCES = 6        # sources collectées en parallèle
PARALLEL_ARTICLES = 5       # articles téléchargés en parallèle par source

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
]

# Mots-clés d'investissement : pré-filtre AVANT l'appel LLM (gros gain de temps)
MOTS_CLES_INVEST = [
    "investissement", "investir", "milliard", "million", "convention",
    "usine", "projet", "construction", "inaugur", "chantier", "capacité",
    "emploi", "financement", "appel d'offres", "partenariat", "zone industrielle",
    "extension", "implantation", "dirham", "mad", "mw ", "gigawatt", "mégawatt",
    "infrastructure", "complexe", "plateforme", "terminal", "centrale",
    "dessalement", "hydrogène", "renouvelable", "data center", "raffinerie",
]
MONEY_RE = re.compile(
    r"\d[\d\s.,]*\s*(milliards?|millions?|mds?|m\s*mad|mad|dh|dirhams?|€|\$|usd|eur)",
    re.IGNORECASE,
)

COMMON_FEED_PATHS = [
    "/rss", "/feed", "/feed/", "/rss.xml", "/flux-rss", "/fr/rss",
    "/actualites/rss", "/feed/rss", "/index.rss", "/atom.xml",
]


# ═══════════════════════════════════════════════════════════════
# SESSION HTTP ROBUSTE
# ═══════════════════════════════════════════════════════════════

def _new_session(referer: Optional[str] = None) -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,*/*;q=0.8",
        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    })
    if referer:
        s.headers["Referer"] = referer
    return s


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(min=1, max=8),
    retry=retry_if_exception_type((requests.exceptions.ConnectionError,
                                   requests.exceptions.Timeout)),
    reraise=True,
)
def _http_get(session: requests.Session, url: str, verify: bool = True) -> requests.Response:
    return session.get(url, timeout=TIMEOUT, verify=verify, allow_redirects=True)


def _fetch(url: str, session: Optional[requests.Session] = None) -> Optional[str]:
    """Télécharge une URL avec retry, fallback SSL et contournement 403."""
    sess = session or _new_session()
    try:
        resp = _http_get(sess, url, verify=True)
        if resp.status_code == 403:
            raise requests.exceptions.HTTPError(response=resp)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or "utf-8"
        return resp.text
    except requests.exceptions.SSLError:
        try:
            resp = _http_get(sess, url, verify=False)
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding or "utf-8"
            return resp.text
        except Exception as e:
            logger.debug(f"SSL+retry KO {url}: {e}")
            return None
    except requests.exceptions.HTTPError as e:
        code = getattr(e.response, "status_code", "?")
        if code == 403:
            # Tentative de contournement : nouvelle session, UA différent, referer
            try:
                base = f"{urlparse(url).scheme}://{urlparse(url).netloc}/"
                s2 = _new_session(referer=base)
                time.sleep(1.5)
                resp = _http_get(s2, url, verify=False)
                resp.raise_for_status()
                resp.encoding = resp.apparent_encoding or "utf-8"
                logger.info(f"403 contourné : {url}")
                return resp.text
            except Exception:
                logger.warning(f"403 persistant : {url}")
                return None
        logger.warning(f"HTTP {code} : {url}")
        return None
    except Exception as e:
        logger.debug(f"Fetch KO {url}: {e}")
        return None


# ═══════════════════════════════════════════════════════════════
# CACHE ANTI-DOUBLON (SQLite)
# ═══════════════════════════════════════════════════════════════

@contextmanager
def _cache_conn():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _init_cache():
    with _cache_conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS scraped_urls (
                url TEXT PRIMARY KEY,
                content_hash TEXT,
                last_seen TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)


def _hash(txt: str) -> str:
    return hashlib.md5(txt.encode("utf-8", "ignore")).hexdigest()


def _deja_traite(url: str, content: str) -> bool:
    h = _hash(content)
    with _cache_conn() as c:
        row = c.execute(
            "SELECT content_hash FROM scraped_urls WHERE url = ?", (url,)
        ).fetchone()
        if row and row[0] == h:
            return True
        c.execute(
            "INSERT OR REPLACE INTO scraped_urls (url, content_hash, last_seen) "
            "VALUES (?, ?, CURRENT_TIMESTAMP)",
            (url, h),
        )
    return False


# ═══════════════════════════════════════════════════════════════
# DÉCOUVERTE RSS / FLUX
# ═══════════════════════════════════════════════════════════════

def _trouver_flux(html: str, base_url: str) -> List[str]:
    """Détecte les flux RSS/Atom déclarés dans la page + chemins courants."""
    flux = []
    try:
        soup = BeautifulSoup(html, "html.parser")
        for link in soup.find_all("link", rel=lambda v: v and "alternate" in v):
            t = (link.get("type") or "").lower()
            if "rss" in t or "atom" in t or "xml" in t:
                href = link.get("href")
                if href:
                    flux.append(urljoin(base_url, href))
    except Exception:
        pass
    root = f"{urlparse(base_url).scheme}://{urlparse(base_url).netloc}"
    for p in COMMON_FEED_PATHS:
        flux.append(root + p)
    # unique en gardant l'ordre
    seen, out = set(), []
    for f in flux:
        if f not in seen:
            seen.add(f)
            out.append(f)
    return out[:6]


def _parser_flux(xml: str, source_id: str) -> List[Dict]:
    """Parse un flux RSS/Atom en liste d'items {title, url}."""
    items = []
    try:
        soup = BeautifulSoup(xml, "xml")
        entries = soup.find_all("item") or soup.find_all("entry")
        for e in entries[:MAX_ARTICLES_PAR_SOURCE]:
            title_tag = e.find("title")
            link_tag = e.find("link")
            title = title_tag.get_text(strip=True) if title_tag else ""
            if link_tag and link_tag.get("href"):
                url = link_tag.get("href")
            elif link_tag:
                url = link_tag.get_text(strip=True)
            else:
                url = ""
            if title and url:
                items.append({"title": title, "url": url, "source": source_id})
    except Exception as e:
        logger.debug(f"[{source_id}] Parse flux KO : {e}")
    return items


# ═══════════════════════════════════════════════════════════════
# EXTRACTION LIENS + PAGINATION
# ═══════════════════════════════════════════════════════════════

def _liens_articles(soup: BeautifulSoup, base_url: str, config: Dict) -> List[Tuple[str, str]]:
    selectors = config.get("selectors", {})
    article_sel = selectors.get("articles")
    base_domain = urlparse(base_url).netloc
    candidates = []

    if article_sel:
        for sel in [s.strip() for s in article_sel.split(",")]:
            candidates += soup.select(sel)
    if not candidates:
        candidates = soup.find_all("article")
    if not candidates:
        candidates = soup.find_all(
            ["div", "li"],
            class_=lambda c: c and any(
                k in str(c).lower()
                for k in ["article", "news", "item", "post", "actualite",
                          "communique", "card", "entry", "publication",
                          "release", "media"]
            ),
        )
    if not candidates:
        for li in soup.find_all("li"):
            a = li.find("a", href=True)
            if a and len(a.get_text(strip=True)) > 25:
                candidates.append(li)

    seen, liens = set(), []
    for el in candidates[:40]:
        a = el.find("a", href=True)
        if not a:
            continue
        title = (
            (el.find(["h1", "h2", "h3", "h4"]) or a).get_text(strip=True)
        )
        url = _abs(a["href"], base_url)
        if not url or url in seen or url == base_url:
            continue
        netloc = urlparse(url).netloc
        if netloc and netloc != base_domain:
            continue
        low = url.lower()
        if any(low.endswith(x) for x in [".jpg", ".png", ".gif", ".zip", ".doc", ".mp4"]):
            continue
        if title and len(title) > 12:
            seen.add(url)
            liens.append((title, url))
    return liens


def _urls_pagination(soup: BeautifulSoup, base_url: str) -> List[str]:
    """Trouve les pages suivantes (rel=next, ?page=N, /page/N, 'suivant')."""
    urls = []
    nxt = soup.find("a", rel=lambda v: v and "next" in v)
    if nxt and nxt.get("href"):
        urls.append(_abs(nxt["href"], base_url))
    for a in soup.find_all("a", href=True):
        txt = a.get_text(strip=True).lower()
        href = a["href"].lower()
        if (txt in ("suivant", "next", "›", "»", "→")
                or re.search(r"[?&]page=\d+", href)
                or re.search(r"/page/\d+", href)):
            u = _abs(a["href"], base_url)
            if u and u != base_url:
                urls.append(u)
    seen, out = set(), []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out[: MAX_PAGES_PAGINATION - 1]


# ═══════════════════════════════════════════════════════════════
# EXTRACTION CONTENU (readability-like)
# ═══════════════════════════════════════════════════════════════

def _extraire_contenu(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["nav", "header", "footer", "script", "style", "aside",
                     "iframe", "noscript", "form", "button", "svg"]):
        tag.decompose()

    art = soup.find("article")
    if art:
        t = art.get_text(separator=" ", strip=True)
        if len(t) > MIN_CONTENT_LENGTH:
            return t

    for kw in ["article-content", "article-body", "entry-content",
               "post-content", "content-body", "communique", "field-items",
               "node-body", "text-content", "main-content", "page-content",
               "actualite-detail", "single-content"]:
        el = soup.find(class_=lambda c: c and kw in str(c).lower())
        if el:
            t = el.get_text(separator=" ", strip=True)
            if len(t) > MIN_CONTENT_LENGTH:
                return t

    # Bloc le plus dense : div/section avec le plus de texte en <p>
    best, best_len = None, 0
    for blk in soup.find_all(["div", "section", "main"]):
        ps = blk.find_all("p", recursive=False) or blk.find_all("p")
        txt = " ".join(p.get_text(strip=True) for p in ps)
        if len(txt) > best_len:
            best, best_len = txt, len(txt)
    if best and best_len > MIN_CONTENT_LENGTH:
        return best

    paras = [p.get_text(strip=True) for p in soup.find_all("p")
             if len(p.get_text(strip=True)) > 40]
    if paras:
        return " ".join(paras)
    body = soup.find("body")
    return body.get_text(separator=" ", strip=True)[:9000] if body else ""


def _pertinent(titre: str, contenu: str) -> bool:
    """Pré-filtre rapide : l'article parle-t-il d'investissement ?"""
    blob = f"{titre} {contenu}".lower()
    hits = sum(1 for k in MOTS_CLES_INVEST if k in blob)
    return hits >= 2 or bool(MONEY_RE.search(blob))


# ═══════════════════════════════════════════════════════════════
# COLLECTE D'UNE SOURCE
# ═══════════════════════════════════════════════════════════════

def _fetch_html_source(source_id: str, config: Dict) -> List[Dict]:
    base_url = config["url"]
    session = _new_session(referer=f"{urlparse(base_url).scheme}://{urlparse(base_url).netloc}/")
    logger.info(f"[{source_id}] Listing : {base_url}")

    html = _fetch(base_url, session)
    if not html:
        return []

    # 1) Tentative RSS/flux (plus propre)
    liens: List[Tuple[str, str]] = []
    for flux_url in _trouver_flux(html, base_url):
        xml = _fetch(flux_url, session)
        if xml and ("<rss" in xml[:500].lower() or "<feed" in xml[:500].lower()
                    or "<?xml" in xml[:100].lower()):
            items = _parser_flux(xml, source_id)
            if items:
                logger.info(f"[{source_id}] Flux RSS trouvé : {len(items)} entrées ({flux_url})")
                liens = [(it["title"], it["url"]) for it in items]
                break

    # 2) Sinon scraping HTML + pagination
    if not liens:
        soup = BeautifulSoup(html, "html.parser")
        liens = _liens_articles(soup, base_url, config)
        for page_url in _urls_pagination(soup, base_url):
            ph = _fetch(page_url, session)
            if ph:
                liens += _liens_articles(BeautifulSoup(ph, "html.parser"), base_url, config)

    # Dédoublonnage
    seen, uniq = set(), []
    for t, u in liens:
        if u not in seen:
            seen.add(u)
            uniq.append((t, u))
    liens = uniq[:MAX_ARTICLES_PAR_SOURCE]

    if not liens:
        # Fallback : la page listing elle-même comme document
        contenu = _extraire_contenu(html)
        if len(contenu) > MIN_CONTENT_LENGTH and _pertinent(source_id, contenu):
            return [{"title": config["nom"], "content": contenu[:9000],
                     "url": base_url, "source": source_id}]
        return []

    # 3) Téléchargement PARALLÈLE des articles
    def _charger(item):
        titre, url = item
        h = _fetch(url, session)
        if not h:
            return None
        contenu = _extraire_contenu(h)
        if len(contenu) < MIN_CONTENT_LENGTH or not _pertinent(titre, contenu):
            return None
        return {"title": titre, "content": contenu[:9000], "url": url, "source": source_id}

    articles = []
    with ThreadPoolExecutor(max_workers=PARALLEL_ARTICLES) as ex:
        for res in ex.map(_charger, liens):
            if res:
                articles.append(res)

    logger.info(f"[{source_id}] {len(articles)} article(s) pertinent(s) retenus")
    return articles


def _fetch_pdf_source(source_id: str, config: Dict) -> List[Dict]:
    base_url = config["url"]
    session = _new_session()
    html = _fetch(base_url, session)
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    pdfs = [_abs(a["href"], base_url) for a in soup.find_all("a", href=True)
            if a["href"].lower().endswith(".pdf")][:6]
    if not pdfs:
        contenu = _extraire_contenu(html)
        if len(contenu) > MIN_CONTENT_LENGTH:
            return [{"title": config["nom"], "content": contenu[:9000],
                     "url": base_url, "source": source_id}]
        return []

    def _lire_pdf(pdf_url):
        try:
            r = session.get(pdf_url, timeout=40, verify=False)
            r.raise_for_status()
            tmp = Path("data") / f"tmp_{_hash(pdf_url)[:8]}.pdf"
            tmp.parent.mkdir(parents=True, exist_ok=True)
            tmp.write_bytes(r.content)
            from .lecture.pdf_reader import extraire_texte_pdf
            txt = extraire_texte_pdf(str(tmp))
            tmp.unlink(missing_ok=True)
            if txt and len(txt) > MIN_CONTENT_LENGTH and _pertinent("", txt):
                return {"title": Path(pdf_url).stem.replace("-", " ").replace("_", " "),
                        "content": txt[:9000], "url": pdf_url, "source": source_id}
        except Exception as e:
            logger.debug(f"[{source_id}] PDF KO {pdf_url}: {e}")
        return None

    articles = []
    with ThreadPoolExecutor(max_workers=3) as ex:
        for res in ex.map(_lire_pdf, pdfs):
            if res:
                articles.append(res)
    logger.info(f"[{source_id}] {len(articles)} PDF(s) pertinent(s)")
    return articles


def _fetch_datasets_source(source_id: str, config: Dict) -> List[Dict]:
    base_url = config["url"]
    session = _new_session()
    formats = config.get("formats", ["xlsx", "csv"])
    html = _fetch(base_url, session)
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    links = [_abs(a["href"], base_url) for a in soup.find_all("a", href=True)
             if any(a["href"].lower().endswith(f".{f}") for f in formats)][:4]
    articles = []
    for dl in links:
        try:
            ext = dl.rsplit(".", 1)[-1].lower()
            tmp = Path("data") / f"tmp_ds_{_hash(dl)[:8]}.{ext}"
            tmp.parent.mkdir(parents=True, exist_ok=True)
            r = session.get(dl, timeout=40, verify=False)
            r.raise_for_status()
            tmp.write_bytes(r.content)
            from .lecture.excel_reader import lire_excel_intelligemment
            rows = lire_excel_intelligemment(str(tmp))
            tmp.unlink(missing_ok=True)
            txt = str(rows)[:9000]
            if txt:
                articles.append({"title": Path(dl).stem.replace("-", " "),
                                 "content": txt, "url": dl, "source": source_id})
        except Exception as e:
            logger.debug(f"[{source_id}] dataset KO {dl}: {e}")
    return articles


def collecter_source(source_id: str) -> List[Dict]:
    config = SOURCES_CONFIG.get(source_id)
    if not config:
        logger.error(f"Source inconnue : {source_id}")
        return []
    t = config.get("type", "html")
    try:
        if t in ("html", "js_dynamic"):
            return _fetch_html_source(source_id, config)
        if t in ("pdf",):
            return _fetch_pdf_source(source_id, config)
        if t in ("datasets",):
            return _fetch_datasets_source(source_id, config)
        if t in ("html_pdf",):
            arts = _fetch_html_source(source_id, config)
            return arts or _fetch_pdf_source(source_id, config)
    except Exception as e:
        logger.warning(f"[{source_id}] Collecte KO : {e}")
    return []


# ═══════════════════════════════════════════════════════════════
# ORCHESTRATEUR
# ═══════════════════════════════════════════════════════════════

def lancer_scraping(sources: Optional[List[str]] = None) -> Dict:
    init_db()
    _init_cache()
    sources = sources or list(SOURCES_CONFIG.keys())
    projets_existants = get_all_projets(limit=1000)

    stats = {
        "sources_traitees": 0, "articles_collectes": 0,
        "projets_detectes": 0, "projets_rejetes": 0,
        "doublons_ignores": 0, "chunks_rag": 0, "erreurs": 0,
    }

    try:
        from .rag import ingerer_source_scrapee, rag_store
        rag_store.init()
        rag_actif = True
    except Exception as e:
        logger.warning(f"RAG désactivé : {e}")
        rag_actif = False

    logger.info(f"\n{'='*64}\nSCRAPING — {len(sources)} source(s) | collecte parallèle\n{'='*64}")

    # 1) COLLECTE PARALLÈLE de toutes les sources
    tous_articles: List[Dict] = []
    with ThreadPoolExecutor(max_workers=PARALLEL_SOURCES) as ex:
        futurs = {ex.submit(collecter_source, sid): sid for sid in sources}
        for fut in as_completed(futurs):
            sid = futurs[fut]
            try:
                arts = fut.result()
                stats["sources_traitees"] += 1
                stats["articles_collectes"] += len(arts)
                tous_articles += arts
                logger.info(f"[{sid}] ✓ {len(arts)} article(s)")
            except Exception as e:
                stats["erreurs"] += 1
                logger.error(f"[{sid}] ✗ {e}")

    logger.info(f"\n>>> {len(tous_articles)} article(s) collecté(s) → pipeline IA\n")

    # 2) PIPELINE séquentiel (Ollama = instance unique)
    for article in tous_articles:
        url = article.get("url", "")
        contenu = article.get("content", "")
        try:
            if url and _deja_traite(url, contenu):
                stats["doublons_ignores"] += 1
                continue

            projet = traiter_nouveau_document(
                document=article,
                source=article.get("source", ""),
                projets_existants=projets_existants,
            )
            projet_id = ""
            if projet:
                save_projet(projet)
                projets_existants.append(projet)
                projet_id = projet.id or ""
                stats["projets_detectes"] += 1
                logger.info(f"  ✅ {projet.titre[:60]}")
            else:
                stats["projets_rejetes"] += 1

            if rag_actif:
                try:
                    stats["chunks_rag"] += ingerer_source_scrapee(
                        titre=article.get("title", ""),
                        contenu=contenu,
                        url=url,
                        source=article.get("source", ""),
                        projet_id=projet_id,
                    )
                except Exception as e:
                    logger.debug(f"RAG KO : {e}")
        except Exception as e:
            stats["erreurs"] += 1
            logger.error(f"  Pipeline KO '{article.get('title','')[:40]}': {e}")

    logger.info(
        f"\n{'='*64}\nTERMINÉ\n"
        f"  Sources traitées   : {stats['sources_traitees']}\n"
        f"  Articles collectés : {stats['articles_collectes']}\n"
        f"  Projets détectés   : {stats['projets_detectes']}\n"
        f"  Rejets pipeline    : {stats['projets_rejetes']}\n"
        f"  Doublons ignorés   : {stats['doublons_ignores']}\n"
        f"  Chunks RAG indexés : {stats['chunks_rag']}\n"
        f"  Erreurs            : {stats['erreurs']}\n{'='*64}\n"
    )
    return stats


# ───────────────────────── Helpers ─────────────────────────

def _abs(href: str, base_url: str) -> str:
    if not href:
        return ""
    if href.startswith("http"):
        return href
    if href.startswith("//"):
        return f"{urlparse(base_url).scheme}:{href}"
    return urljoin(base_url, href)


# Compat rétro
_absolut_url = _abs
