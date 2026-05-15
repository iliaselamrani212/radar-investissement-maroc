from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from pathlib import Path
import json
import time

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "raw_data"
RAW_DIR.mkdir(exist_ok=True)

def clean_text(text):
    return " ".join(text.split())

def scrape_charika_nouvelles_societes():
    articles = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)

            page = browser.new_page(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            )

            page.goto(
                "https://www.charika.ma",
                timeout=60000,
                wait_until="domcontentloaded"
            )

            page.wait_for_timeout(5000)

            links = page.query_selector_all("a")

            for link in links:
                try:
                    text = clean_text(link.inner_text())
                    href = link.get_attribute("href")

                    if not text or len(text) < 30:
                        continue

                    keywords = [
                        "investissement",
                        "entreprise",
                        "société",
                        "projet",
                        "capital",
                        "industrie",
                        "maroc",
                        "afrique",
                        "économie",
                        "exportations"
                    ]

                    if any(k.lower() in text.lower() for k in keywords):
                        if href and not href.startswith("http"):
                            href = "https://www.charika.ma" + href

                        articles.append({
                            "title": text[:250],
                            "url": href if href else "https://www.charika.ma",
                            "source": "Charika.ma",
                            "niveau_source": 1,
                            "content": text,
                            "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S")
                        })

                except Exception:
                    continue

            browser.close()

    except PlaywrightTimeoutError:
        print("Timeout Charika")
    except Exception as e:
        print(f"Erreur Charika : {e}")

    # Supprimer les doublons par title
    unique = {}
    for art in articles:
        unique[art["title"]] = art

    articles = list(unique.values())

    output_file = RAW_DIR / "charika.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    print(f"✅ {len(articles)} articles Charika sauvegardés dans {output_file}")

    return articles

if __name__ == "__main__":
    scrape_charika_nouvelles_societes()