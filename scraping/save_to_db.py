import json
import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "raw_data"

load_dotenv(BASE_DIR / ".env")


ALLOWED_FILES = [
    "ammc.json",
    "charika.json",
    "hcp.json",
    "mcinet.json",
    "opendata_maroc.json",
    "thepulse.json",
]


def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        user=os.getenv("DB_USER", "radar"),
        password=os.getenv("DB_PASS", "radar123"),
        dbname=os.getenv("DB_NAME", "radar_db"),
    )


def init_table():
    """
    Crée la table raw_articles si elle n'existe pas.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS raw_articles (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            url TEXT UNIQUE NOT NULL,
            source TEXT NOT NULL,
            niveau_source INT DEFAULT 1,
            content TEXT,
            scraped_at TIMESTAMP DEFAULT NOW(),
            processed BOOLEAN DEFAULT FALSE,
            metadata JSONB DEFAULT '{}'
        );
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_raw_processed
        ON raw_articles(processed);
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_raw_source
        ON raw_articles(source);
    """)

    conn.commit()
    cur.close()
    conn.close()

    print("✅ Table raw_articles prête")


def load_json_file(filepath: Path):
    """
    Lire un fichier JSON en sécurité.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            return data

        print(f"⚠️ Le fichier {filepath.name} ne contient pas une liste JSON")
        return []

    except FileNotFoundError:
        print(f"⚠️ Fichier introuvable : {filepath}")
        return []

    except json.JSONDecodeError as e:
        print(f"❌ JSON invalide dans {filepath.name}: {e}")
        return []

    except Exception as e:
        print(f"❌ Erreur lecture {filepath.name}: {e}")
        return []


def save_all():
    """
    Sauvegarde les fichiers JSON autorisés dans PostgreSQL.
    """
    init_table()

    conn = get_db_connection()
    cur = conn.cursor()

    total_inserted = 0
    total_seen = 0

    files = [
        RAW_DIR / filename
        for filename in ALLOWED_FILES
        if (RAW_DIR / filename).exists()
    ]

    if not files:
        print("⚠️ Aucun fichier JSON trouvé dans raw_data/")
        cur.close()
        conn.close()
        return

    for filepath in files:
        print(f"\n📄 Lecture : {filepath.name}")

        articles = load_json_file(filepath)
        print(f"🔎 {len(articles)} éléments trouvés")

        for art in articles:
            total_seen += 1

            title = art.get("title")
            url = art.get("url")
            source = art.get("source")
            niveau_source = art.get("niveau_source", 1)
            content = art.get("content", "")

            if not title or not url or not source:
                print("⚠️ Article ignoré : title/url/source manquant")
                continue

            metadata = {
                "type_source": art.get("type_source"),
                "scraped_at": art.get("scraped_at"),
                "raw_file": filepath.name,
            }

            try:
                cur.execute("""
                    INSERT INTO raw_articles
                    (
                        title,
                        url,
                        source,
                        niveau_source,
                        content,
                        metadata
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (url) DO NOTHING
                """, (
                    title,
                    url,
                    source,
                    niveau_source,
                    content,
                    json.dumps(metadata, ensure_ascii=False),
                ))

                if cur.rowcount > 0:
                    total_inserted += 1

            except Exception as e:
                print(f"❌ Erreur insertion article : {e}")
                conn.rollback()
                continue

    conn.commit()
    cur.close()
    conn.close()

    print("\n✅ Sauvegarde terminée")
    print(f"📦 Articles lus : {total_seen}")
    print(f"🆕 Nouveaux articles insérés : {total_inserted}")


if __name__ == "__main__":
    save_all()