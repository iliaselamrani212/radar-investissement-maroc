from utils import scrape_listing_site


def scrape_thepulse():
    return scrape_listing_site(
        source_name="The Pulse",
        base_url="https://www.thepulse.ma",
        urls=[
            "https://www.thepulse.ma",
            "https://www.thepulse.ma/startups",
            "https://www.thepulse.ma/funding-rounds",
            "https://www.thepulse.ma/investors",
            "https://www.thepulse.ma/calls-for-projects"
        ],
        niveau_source=2,
        type_source="startup_ecosystem_database",
        output_filename="thepulse.json",
        max_articles_per_url=30
    )


if __name__ == "__main__":
    scrape_thepulse()