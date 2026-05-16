from utils import scrape_listing_site


def scrape_hcp():
    return scrape_listing_site(
        source_name="HCP",
        base_url="https://www.hcp.ma",
        urls=[
            "https://www.hcp.ma/Emploi_r433.html",
            "https://www.hcp.ma/search/pib/",
            "https://www.hcp.ma/search/emploi/",
            "https://www.hcp.ma/search/hcp/"
        ],
        niveau_source=1,
        type_source="statistiques_officielles",
        output_filename="hcp.json",
        max_articles_per_url=25
    )


if __name__ == "__main__":
    scrape_hcp()