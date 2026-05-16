import json
import time
import requests
import urllib3
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

try:
    import trafilatura
except ImportError:
    trafilatura = None


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "raw_data"
RAW_DIR.mkdir(exist_ok=True)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def clean_text(text: str) -> str:
    if not text:
        return ""
    return " ".join(text.split())


def save_json(filename: str, articles: list) -> list:
    output_file = RAW_DIR / filename

    unique = {}
    for article in articles:
        key = article.get("url") or article.get("title")
        if key:
            unique[key] = article

    articles = list(unique.values())

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    print(f"✅ {len(articles)} éléments sauvegardés dans {output_file}")
    return articles


def fetch_html_requests(url: str) -> str:
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30,
        verify=False
    )
    response.raise_for_status()
    return response.text


def fetch_html_playwright(url: str) -> str:
    html = ""

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        page = browser.new_page(
            user_agent=HEADERS["User-Agent"],
            locale="fr-FR"
        )

        try:
            page.goto(
                url,
                timeout=60000,
                wait_until="domcontentloaded"
            )
            page.wait_for_timeout(3000)
            html = page.content()

        except PlaywrightTimeoutError:
            print(f"⚠️ Timeout Playwright : {url}")
            html = ""

        except Exception as e:
            print(f"❌ Erreur Playwright sur {url}: {e}")
            html = ""

        finally:
            browser.close()

    return html


def fetch_html(url: str) -> str:
    try:
        return fetch_html_requests(url)

    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response is not None else None

        if status == 403:
            print(f"⚠️ 403 détecté, fallback Playwright : {url}")
            return fetch_html_playwright(url)

        print(f"❌ HTTP error {status} sur {url}: {e}")
        return ""

    except requests.exceptions.SSLError:
        print(f"⚠️ Problème SSL, fallback Playwright : {url}")
        return fetch_html_playwright(url)

    except Exception as e:
        print(f"⚠️ Erreur requests sur {url}: {e}")
        print(f"⚠️ Fallback Playwright : {url}")
        return fetch_html_playwright(url)


def extract_main_text(html: str) -> str:
    if not html:
        return ""

    if trafilatura is not None:
        try:
            text = trafilatura.extract(
                html,
                include_comments=False,
                include_tables=True,
                favor_precision=False
            )
            if text and len(text.strip()) > 100:
                return clean_text(text)
        except Exception as e:
            print(f"⚠️ Trafilatura a échoué, fallback BeautifulSoup : {e}")

    soup = BeautifulSoup(html, "lxml")

    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
        tag.decompose()

    main_zone = soup.select_one(
        "article, main, .article-content, .entry-content, .post-content, "
        ".content, .main-content, .actualite-content, .news-content, "
        ".page-content, .elementor-widget-container, .body, .field--name-body"
    )

    if main_zone:
        return clean_text(main_zone.get_text(separator=" "))

    body = soup.select_one("body")
    if body:
        return clean_text(body.get_text(separator=" "))

    return ""


def extract_title(html: str, fallback_url: str) -> str:
    if not html:
        return fallback_url

    soup = BeautifulSoup(html, "lxml")

    h1 = soup.select_one("h1")
    if h1:
        title = clean_text(h1.get_text())
        if title:
            return title[:300]

    if soup.title:
        title = clean_text(soup.title.get_text())
        if title:
            return title[:300]

    return fallback_url


def extract_links_from_listing(html: str, base_url: str, max_links: int = 20) -> list:
    if not html:
        return []

    soup = BeautifulSoup(html, "lxml")

    selectors = [
        "article a",
        ".post a",
        ".entry a",
        ".card a",
        ".item a",
        ".news-item a",
        ".views-row a",
        ".actualite a",
        ".blog-post a",
        ".elementor-post a",
        ".communique a",
        ".publication a",
        "h1 a",
        "h2 a",
        "h3 a",
        "h4 a",
        "a"
    ]

    candidates = []
    for selector in selectors:
        candidates.extend(soup.select(selector))

    links = []

    skip_words = [
        "login",
        "connexion",
        "signup",
        "register",
        "contact",
        "facebook",
        "twitter",
        "linkedin",
        "instagram",
        "youtube",
        "mailto:",
        "tel:",
        "javascript:",
        "#",
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".svg",
        ".zip"
    ]

    for link in candidates:
        title = clean_text(link.get_text())
        href = link.get("href")

        if not href:
            continue

        if not title or len(title) < 8:
            continue

        full_url = urljoin(base_url, href)
        full_url_lower = full_url.lower()

        if any(skip in full_url_lower for skip in skip_words):
            continue

        if full_url in links:
            continue

        links.append(full_url)

        if len(links) >= max_links:
            break

    return links


def scrape_listing_site(
    source_name: str,
    base_url: str,
    urls: list,
    niveau_source: int,
    type_source: str,
    output_filename: str,
    max_articles_per_url: int = 20
) -> list:
    articles = []

    for listing_url in urls:
        print(f"\n🔎 Listing {source_name}: {listing_url}")

        listing_html = fetch_html(listing_url)

        if not listing_html:
            print(f"⚠️ Aucun HTML récupéré pour {listing_url}")
            continue

        links = extract_links_from_listing(
            html=listing_html,
            base_url=base_url,
            max_links=max_articles_per_url
        )

        print(f"🔗 {len(links)} liens trouvés pour {source_name}")

        for article_url in links:
            try:
                article_html = fetch_html(article_url)

                if not article_html:
                    continue

                content = extract_main_text(article_html)

                if len(content) < 100:
                    continue

                title = extract_title(article_html, article_url)

                article = {
                    "title": title,
                    "url": article_url,
                    "source": source_name,
                    "niveau_source": niveau_source,
                    "type_source": type_source,
                    "content": content,
                    "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S")
                }

                articles.append(article)
                print(f"✅ Page extraite: {title[:90]}")

                time.sleep(2)

            except Exception as e:
                print(f"❌ Erreur article {article_url}: {e}")

        time.sleep(2)

    return save_json(output_filename, articles)