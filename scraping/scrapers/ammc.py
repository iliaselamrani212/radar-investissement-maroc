from utils import scrape_listing_site


def scrape_ammc():
    return scrape_listing_site(
        source_name="AMMC",
        base_url="https://www.ammc.ma",
        urls=[
            "https://www.ammc.ma/fr/espace-emetteurs/communiques-presse",
            "https://www.ammc.ma/fr/espace-emetteurs/communiques-de-presse-de-lemetteur",
            "https://www.ammc.ma/espace-emetteurs/liste-operations-financieres?page=1"
        ],
        niveau_source=1,
        type_source="autorite_marche_capitaux",
        output_filename="ammc.json",
        max_articles_per_url=25
    )


if __name__ == "__main__":
    scrape_ammc()