import requests
from bs4 import BeautifulSoup
from pathlib import Path
import json
import time
from urllib.parse import urljoin

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "raw_data"
RAW_DIR.mkdir(exist_ok=True)

BASE_URL = "https://www.amdie.gov.ma"

def clean_text(text):
    return " ".join(text.split())

def scrape_amdie():
    articles = []

    urls_to_try = [
        "https://www.amdie.gov.ma/fr/actualites",
        "https://www.amdie.gov.ma/fr/communiques",
        "https://www.amdie.gov.ma/fr/projets",
        "https://www.amdie.gov.ma"
    ]

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    keywords = [
        "investissement", "projet", "industrie", "maroc", "entreprise",
        "convention", "partenariat", "usine", "emploi", "export",
        "énergie", "tourisme", "infrastructure", "développement"
    ]

    for url in urls_to_try:
        try:
            print(f"Scraping AMDIE : {url}")

            r = requests.get(url, headers=headers, timeout=30)
            r.raise_for_status()

            soup = BeautifulSoup(r.text, "lxml")

            candidates = soup.select(
                "article, .news-item, .item, .post, .card, .actualite, .views-row"
            )

            if not candidates:
                candidates = soup.select("a")

            for item in candidates:
                try:
                    title_el = item.select_one("h1, h2, h3, h4, .title, .entry-title")
                    link_el = item.select_one("a") if item.name != "a" else item

                    title = ""

                    if title_el:
                        title = clean_text(title_el.get_text())
                    elif item.name == "a":
                        title = clean_text(item.get_text())

                    if not title or len(title) < 25:
                        continue

                    if not any(k.lower() in title.lower() for k in keywords):
                        continue

                    href = link_el.get("href") if link_el else url
                    full_url = urljoin(BASE_URL, href)

                    content = clean_text(item.get_text())[:2500]

                    articles.append({
                        "title": title[:250],
                        "url": full_url,
                        "source": "AMDIE",
                        "niveau_source": 1,
                        "content": content,
                        "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S")
                    })

                except Exception:
                    continue

        except Exception as e:
            print(f"Erreur AMDIE sur {url}: {e}")

    unique = {}
    for art in articles:
        unique[art["url"]] = art

    articles = list(unique.values())

    output_file = RAW_DIR / "amdie.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    print(f"✅ {len(articles)} articles AMDIE sauvegardés dans {output_file}")

    return articles

if __name__ == "__main__":
    scrape_amdie()