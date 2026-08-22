"""
Storage Module for Global News AI

Handles saving cleaned news articles into CSV and JSON files inside the data/ directory.
Automatically creates the data/ folder if it does not exist.
"""

from typing import Any, Dict, List
from pathlib import Path
import json
import hashlib
import pandas as pd


def ensure_data_dir(data_dir: str = "data") -> Path:
    """
    Ensures the target data directory exists on disk.
    Creates directory recursively if it does not exist.
    """
    path = Path(data_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def generate_article_id(url: str, index: int) -> str:
    """
    Generates a deterministic unique ID for an article using SHA-256 hash of its URL.
    """
    if url:
        hash_digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:8]
        return f"news_{hash_digest}"
    return f"news_{index:04d}"


def prepare_articles_for_storage(
    articles: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Attaches unique 'id' column and ensures exact field order for export.
    """
    ordered_articles = []
    field_order = [
        "id",
        "title",
        "summary",
        "url",
        "source",
        "published_at",
        "author",
        "category",
        "language",
    ]

    for idx, art in enumerate(articles, start=1):
        art_id = generate_article_id(art.get("url", ""), idx)
        entry = {"id": art_id}
        for field in field_order:
            if field != "id":
                entry[field] = art.get(field, "")
        ordered_articles.append(entry)

    return ordered_articles


def save_to_csv(
    articles: List[Dict[str, Any]], filepath: Path
) -> str:
    """
    Saves articles to CSV format using pandas.
    """
    df = pd.DataFrame(articles)
    df.to_csv(filepath, index=False, encoding="utf-8-sig")
    return str(filepath)


def save_to_json(
    articles: List[Dict[str, Any]], filepath: Path
) -> str:
    """
    Saves articles to JSON format with formatting.
    """
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(articles, f, indent=2, ensure_ascii=False)
    return str(filepath)


def save_articles(
    articles: List[Dict[str, Any]], output_dir: str = "data"
) -> Dict[str, str]:
    """
    Prepares articles and saves them into both data/news.csv and data/news.json.
    Returns dictionary with output file paths.
    """
    target_dir = ensure_data_dir(output_dir)
    prepared_articles = prepare_articles_for_storage(articles)

    csv_path = target_dir / "news.csv"
    json_path = target_dir / "news.json"

    saved_csv = save_to_csv(prepared_articles, csv_path)
    saved_json = save_to_json(prepared_articles, json_path)

    return {
        "csv": saved_csv,
        "json": saved_json,
        "count": len(prepared_articles),
    }
