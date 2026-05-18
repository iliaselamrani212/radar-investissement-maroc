CREATE EXTENSION IF NOT EXISTS "pgcrypto";

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

CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    titre TEXT NOT NULL,
    resume_ai TEXT,
    montant_mad NUMERIC,
    secteur TEXT NOT NULL,
    region TEXT,
    porteur TEXT,
    stade TEXT DEFAULT 'annoncé',
    date_annonce DATE,
    sources JSONB DEFAULT '[]',
    nb_sources_confirmees INT DEFAULT 1,
    latitude NUMERIC,
    longitude NUMERIC,
    embedding JSONB,
    score_fiabilite NUMERIC,
    score_details JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS regions (
    nom TEXT PRIMARY KEY,
    latitude NUMERIC,
    longitude NUMERIC
);

CREATE TABLE IF NOT EXISTS scoring_config (
    id INT PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    poids_source NUMERIC NOT NULL DEFAULT 0.30,
    poids_triangulation NUMERIC NOT NULL DEFAULT 0.30,
    poids_precision NUMERIC NOT NULL DEFAULT 0.15,
    poids_fraicheur NUMERIC NOT NULL DEFAULT 0.15,
    poids_llm NUMERIC NOT NULL DEFAULT 0.10,
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_projects_secteur ON projects(secteur);
CREATE INDEX IF NOT EXISTS idx_projects_region ON projects(region);
CREATE INDEX IF NOT EXISTS idx_projects_score ON projects(score_fiabilite DESC);
CREATE INDEX IF NOT EXISTS idx_projects_montant ON projects(montant_mad);
CREATE INDEX IF NOT EXISTS idx_projects_date ON projects(date_annonce DESC);

INSERT INTO regions VALUES
('Casablanca-Settat', 33.5731, -7.5898),
('Rabat-Salé-Kénitra', 34.0209, -6.8416),
('Tanger-Tétouan-Al Hoceïma', 35.7595, -5.8340),
('Fès-Meknès', 34.0181, -5.0078),
('Marrakech-Safi', 31.6295, -7.9811),
('Oriental', 34.6814, -1.9086),
('Béni Mellal-Khénifra', 32.3373, -6.3498),
('Souss-Massa', 30.4278, -9.5981),
('Drâa-Tafilalet', 31.9314, -4.4339),
('Guelmim-Oued Noun', 28.9870, -10.0574),
('Laâyoune-Sakia El Hamra', 27.1536, -13.2033),
('Dakhla-Oued Ed-Dahab', 23.6848, -15.9579)
ON CONFLICT (nom) DO NOTHING;

INSERT INTO scoring_config (
    id, poids_source, poids_triangulation, poids_precision,
    poids_fraicheur, poids_llm
) VALUES (1, 0.30, 0.30, 0.15, 0.15, 0.10)
ON CONFLICT (id) DO NOTHING;
