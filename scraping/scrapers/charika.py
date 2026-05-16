from utils import scrape_listing_site


def scrape_charika():
    return scrape_listing_site(
        source_name="Charika",
        base_url="https://www.charika.ma",
        urls=[
            "https://www.charika.ma",
            "https://www.charika.ma/actualites",
            "https://www.charika.ma/societe-{nom-entreprise}-{id}",
            "https://www.charika.ma/palmares-des-1000-plus-grandes-entreprises",
            "https://www.charika.ma/palmares-1000-pme",
            "https://en.charika.ma/palmares-societe-401-500",
            "https://www.charika-eco.ma/palmares-1000-plus-grandes-entreprises"
        ],
        niveau_source=2,
        type_source="base_information_entreprise",
        output_filename="charika.json",
        max_articles_per_url=15
    )


if __name__ == "__main__":
    scrape_charika()