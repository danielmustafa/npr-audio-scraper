-- Enable the pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Correspondents table
CREATE TABLE correspondents (
    id SERIAL PRIMARY KEY,
    fullname VARCHAR NOT NULL,
    gender VARCHAR,
    embedding vector(256) NOT NULL
);

-- Audio metadata table
CREATE TABLE audio (
    id SERIAL PRIMARY KEY,
    correspondent_id INT REFERENCES correspondents(id) ON DELETE CASCADE,
    url TEXT UNIQUE NOT NULL
);

-- Audio segments table
CREATE TABLE audio_segments (
    id SERIAL PRIMARY KEY,
    audio_id INT REFERENCES audio(id) ON DELETE CASCADE,
    start_time_sec DECIMAL(10, 3) NOT NULL,
    end_time_sec DECIMAL(10, 3) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    -- Optionally: segment_embedding vector(256)
);