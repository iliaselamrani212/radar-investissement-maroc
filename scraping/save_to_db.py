import psycopg2
import json
import os
from dotenv import load_dotenv
import glob

load_dotenv()

def save_all():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"), port=os.getenv("DB_PORT"),
        user=os.getenv("DB_USER"), password=os.getenv("DB_PASS"),
        dbname=os.getenv("DB_NAME")
    )
    cur = conn.cursor()
    
    total = 0
    for filepath in glob.glob("raw_data/*.json"):
        with open(filepath, "r", encoding="utf-8") as f:
            articles = json.load(f)
        
        for art in articles:
            try:
                cur.execute("""
                    INSERT INTO raw_articles 
                    (title, url, source, niveau_source, content)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (url) DO NOTHING
                """, (
                    art["title"], art["url"], art["source"],
                    art.get("niveau_source", 3), art.get("content", "")
                ))
                total += 1
            except Exception as e:
                print(f"Erreur: {e}")
    
    conn.commit()
    cur.close()
    conn.close()
    print(f"✅ {total} articles sauvegardés en DB")

if __name__ == "__main__":
    save_all()