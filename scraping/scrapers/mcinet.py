from utils import scrape_listing_site


def scrape_mcinet():
    """
    Ministère de l’Industrie et du Commerce.

    Rôle :
    - stratégies industrielles
    - secteurs prioritaires
    - commerce
    - industrie
    - actualités institutionnelles
    """

    return scrape_listing_site(
        source_name="Ministère de l’Industrie et du Commerce",
        base_url="https://www.mcinet.gov.ma",
        urls=[
            "https://www.mcinet.gov.ma",
            "https://www.mcinet.gov.ma/fr/actualites",
            "https://www.mcinet.gov.ma/fr/content/industrie",
            "https://www.mcinet.gov.ma/fr/content/commerce",
            "https://www.mcinet.gov.ma/fr/content/strategies"
        ],
        niveau_source=1,
        type_source="ministere_industrie_strategies",
        output_filename="mcinet.json",
        max_articles_per_url=20
    )


if __name__ == "__main__":
    scrape_mcinet()