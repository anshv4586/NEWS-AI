-- Global News AI - Database Schema Definition (MySQL 8.0+)
-- Database: global_news
-- Table: news (Phase 3 Enriched Schema)

CREATE DATABASE IF NOT EXISTS global_news;
USE global_news;

CREATE TABLE IF NOT EXISTS news (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    article_id VARCHAR(64) NOT NULL,
    title TEXT NOT NULL,
    summary TEXT,
    url VARCHAR(768) NOT NULL,
    source VARCHAR(100) NOT NULL,
    published_at DATETIME,
    author VARCHAR(255),
    category VARCHAR(50) DEFAULT 'General',
    language VARCHAR(20) DEFAULT 'English',
    country VARCHAR(100) DEFAULT 'Global',
    keywords TEXT,
    quality_status VARCHAR(20) DEFAULT 'valid',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_news_url (url)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Performance Indexes for fast filtering and sorting
CREATE INDEX idx_news_published_at ON news (published_at);
CREATE INDEX idx_news_category ON news (category);
CREATE INDEX idx_news_source ON news (source);
CREATE INDEX idx_news_language ON news (language);
CREATE INDEX idx_news_country ON news (country);
CREATE INDEX idx_news_quality ON news (quality_status);
