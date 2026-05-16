from utils import scrape_listing_site


def scrape_opendata_maroc():
    return scrape_listing_site(
        source_name="Portail Open Data Maroc",
        base_url="https://www.data.gov.ma",
        urls=[
            "https://www.data.gov.ma/data/fr/dataset",
            "https://www.data.gov.ma/data/fr/dataset/?q=entreprise",
            "https://www.data.gov.ma/data/fr/dataset/?q=investissement",
            "https://www.data.gov.ma/data/fr/dataset/?q=industrie",
            "https://www.data.gov.ma/data/fr/dataset/?q=emploi",
            "https://www.data.gov.ma/data/fr/dataset/?q=finance"
        ],
        niveau_source=1,
        type_source="open_data_officiel",
        output_filename="opendata_maroc.json",
        max_articles_per_url=20
    )


if __name__ == "__main__":
    scrape_opendata_maroc()