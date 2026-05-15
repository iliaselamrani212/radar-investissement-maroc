CREATE TABLE IF NOT EXISTS raw_articles (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    url TEXT UNIQUE NOT NULL,
    source TEXT NOT NULL,
    niveau_source INT DEFAULT 3,
    content TEXT,
    scraped_at TIMESTAMP DEFAULT NOW(),
    processed BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_raw_processed ON raw_articles(processed);
CREATE INDEX idx_raw_source ON raw_articles(source);