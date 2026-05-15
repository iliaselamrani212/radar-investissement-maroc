import time
from scrapers import charika, amdie, medias24, leconomiste
from save_to_db import save_all

def run_one_cycle():
    print("🔄 Cycle de scraping démarré")
    charika.scrape_charika_nouvelles_societes()
    amdie.scrape_amdie()
    medias24.scrape_medias24()
    leconomiste.scrape_leconomiste()
    save_all()
    print("✅ Cycle terminé")

if __name__ == "__main__":
    # Pour la démo : lance en boucle toutes les 30 min
    while True:
        run_one_cycle()
        time.sleep(1800)  # 30 minutes