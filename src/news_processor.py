"""
News Processor & Enrichment Module for Global News AI

Handles text cleaning, NFKC Unicode normalization, article validation,
automatic language detection, category taxonomy mapping, country detection,
lightweight NLP keyword extraction, and quality scoring.
"""

from typing import Any, Dict, List, Optional, Tuple
import html
import json
import logging
import re
import unicodedata
from datetime import datetime, timezone
import dateutil.parser
from bs4 import BeautifulSoup

try:
    from langdetect import detect, DetectorFactory
    DetectorFactory.seed = 0  # Enforce deterministic language detection
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False

logger = logging.getLogger(__name__)

# Standardized Category Taxonomy
CATEGORY_TAXONOMY = {
    "World",
    "Politics",
    "Business",
    "Technology",
    "Science",
    "Sports",
    "Health",
    "Climate",
    "Entertainment",
    "Other",
}

# Rule-Based Category Mapping Dictionary
CATEGORY_MAPPINGS = {
    "tech": "Technology",
    "technology": "Technology",
    "science & technology": "Technology",
    "it": "Technology",
    "ai": "Technology",
    "business": "Business",
    "economy": "Business",
    "finance": "Business",
    "markets": "Business",
    "world": "World",
    "global": "World",
    "international": "World",
    "politics": "Politics",
    "government": "Politics",
    "election": "Politics",
    "policy": "Politics",
    "sport": "Sports",
    "sports": "Sports",
    "football": "Sports",
    "cricket": "Sports",
    "health": "Health",
    "medicine": "Health",
    "climate": "Climate",
    "environment": "Climate",
    "entertainment": "Entertainment",
    "culture": "Entertainment",
    "art": "Entertainment",
    "science": "Science",
}

# ISO-639-1 Language Code Mapping
LANGUAGE_CODE_MAP = {
    "en": "English",
    "hi": "Hindi",
    "fr": "French",
    "es": "Spanish",
    "de": "German",
    "zh-cn": "Chinese",
    "ar": "Arabic",
    "ru": "Russian",
    "pt": "Portuguese",
    "ja": "Japanese",
}

# Country Keyword Patterns Dictionary
COUNTRY_PATTERNS = {
    "India": r"\b(India|Indian|New Delhi|Mumbai|Modi)\b",
    "United States": r"\b(US|USA|United States|America|American|Washington|Trump|Biden)\b",
    "United Kingdom": r"\b(UK|Britain|British|London|Starmer)\b",
    "Saudi Arabia": r"\b(Saudi|Saudi Arabia|Riyadh|MBS)\b",
    "France": r"\b(France|French|Paris|Macron)\b",
    "Canada": r"\b(Canada|Canadian|Ottawa|Trudeau)\b",
    "Nigeria": r"\b(Nigeria|Nigerian|Abuja|Lagos)\b",
    "China": r"\b(China|Chinese|Beijing|Xi Jinping)\b",
    "Japan": r"\b(Japan|Japanese|Tokyo)\b",
    "Germany": r"\b(Germany|German|Berlin)\b",
    "Russia": r"\b(Russia|Russian|Moscow|Putin)\b",
    "Ukraine": r"\b(Ukraine|Ukrainian|Kyiv)\b",
    "Israel": r"\b(Israel|Israeli|Tel Aviv|Netanyahu)\b",
    "Palestine": r"\b(Palestine|Palestinian|Gaza)\b",
    "Iran": r"\b(Iran|Iranian|Tehran)\b",
}

# Common Stopwords for Keyword Extraction
STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can", "cannot", "could", "did", "do",
    "does", "doing", "down", "during", "each", "few", "for", "from", "further",
    "had", "has", "have", "having", "he", "her", "here", "him", "himself", "his",
    "how", "i", "if", "in", "into", "is", "it", "its", "itself", "just", "me",
    "more", "most", "my", "myself", "no", "nor", "not", "of", "off", "on", "once",
    "only", "or", "other", "our", "ours", "out", "over", "own", "same", "she",
    "should", "so", "some", "such", "than", "that", "the", "their", "theirs",
    "them", "themselves", "then", "there", "these", "they", "this", "those",
    "through", "to", "too", "under", "until", "up", "very", "was", "we", "were",
    "what", "when", "where", "which", "while", "who", "whom", "why", "will",
    "with", "would", "you", "your", "yours", "live", "news", "says", "new", "top"
}


def clean_text(text: Optional[str]) -> str:
    """
    Normalizes text:
    1. Decodes HTML entities (&amp;, &quot;, &#39;, &nbsp;).
    2. Strips raw HTML markup.
    3. Normalizes Unicode characters via NFKC (fixing corrupt symbols).
    4. Collapses excessive whitespace while preserving punctuation.
    """
    if not text:
        return ""

    # Step 1: Decode HTML entities twice if double encoded
    decoded = html.unescape(text)
    decoded = html.unescape(decoded)

    # Step 2: Strip HTML tags cleanly
    soup = BeautifulSoup(decoded, "html.parser")
    text_only = soup.get_text(separator=" ")

    # Step 3: NFKC Unicode normalization
    normalized = unicodedata.normalize("NFKC", text_only)

    # Step 4: Collapse whitespace preserving sentence punctuation
    cleaned = re.sub(r"\s+", " ", normalized).strip()
    return cleaned


def validate_article(article: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validates minimum requirements for an article.
    Mandatory fields: title, url, source.
    Returns (is_valid, reason).
    """
    if not article:
        return False, "Article object is empty or None."

    title = clean_text(article.get("title"))
    url = (article.get("url") or "").strip()
    source = clean_text(article.get("source"))

    if not title:
        return False, "Missing mandatory field: title."
    if not url:
        return False, "Missing mandatory field: url."
    if not source or source.lower() == "unknown":
        return False, "Missing mandatory field: source."

    return True, "Valid"


def detect_language(text: str, fallback_lang: str = "English") -> str:
    """
    Detects language of a text snippet using langdetect with fallback logic.
    Short snippets (< 15 chars) fallback safely to the provided fallback language.
    """
    cleaned = clean_text(text)
    if not cleaned or len(cleaned) < 15 or not LANGDETECT_AVAILABLE:
        return fallback_lang

    try:
        lang_code = detect(cleaned)
        return LANGUAGE_CODE_MAP.get(lang_code.lower(), fallback_lang)
    except Exception as e:
        logger.debug(f"Language detection fallback for text '{cleaned[:20]}...': {e}")
        return fallback_lang


def normalize_category(raw_category: Optional[str]) -> str:
    """
    Normalizes raw source category strings into standard category taxonomy.
    """
    if not raw_category:
        return "World"

    cleaned = clean_text(raw_category).lower()
    for key, mapped_category in CATEGORY_MAPPINGS.items():
        if key in cleaned:
            return mapped_category

    # If capital case matches taxonomy directly
    title_case = cleaned.title()
    if title_case in CATEGORY_TAXONOMY:
        return title_case

    return "World"


def detect_country(title: str, summary: str = "", source: str = "") -> str:
    """
    Detects country associated with an article using metadata and keyword pattern matching.
    Picks the country whose keyword appears earliest in the title/summary text.
    """
    title_clean = clean_text(title)
    summary_clean = clean_text(summary)
    combined_text = f"{title_clean} {summary_clean} {source}"

    earliest_pos = float("inf")
    detected_country = "Global"

    for country, pattern in COUNTRY_PATTERNS.items():
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            pos = match.start()
            if pos < earliest_pos:
                earliest_pos = pos
                detected_country = country

    return detected_country



def extract_keywords(title: str, summary: str = "", top_n: int = 5) -> List[str]:
    """
    Extracts top N meaningful keywords using lightweight frequency analysis,
    filtering out common stopwords, digits, and short tokens.
    """
    combined_text = f"{title} {summary}"
    cleaned = clean_text(combined_text)

    # Tokenize words (preserving hyphenated or alphanumeric words)
    words = re.findall(r"\b[A-Za-z0-9\-]{3,}\b", cleaned)

    filtered_words = []
    for w in words:
        w_lower = w.lower()
        if w_lower not in STOPWORDS and not w.isdigit():
            # Retain original case if capitalized (proper noun), else lower
            filtered_words.append(w if w[0].isupper() else w_lower)

    # Frequency counting preserving order of occurrence
    frequency = {}
    for word in filtered_words:
        key = word.lower()
        if key not in frequency:
            frequency[key] = {"word": word, "count": 0}
        frequency[key]["count"] += 1

    sorted_keywords = sorted(frequency.values(), key=lambda x: x["count"], reverse=True)
    top_keywords = [item["word"] for item in sorted_keywords[:top_n]]

    return top_keywords


def calculate_quality(article: Dict[str, Any]) -> str:
    """
    Assigns quality rating: 'valid', 'needs_review', or 'invalid'.
    """
    is_valid, _ = validate_article(article)
    if not is_valid:
        return "invalid"

    title = clean_text(article.get("title"))
    summary = clean_text(article.get("summary"))

    # If title is suspiciously short or missing summary entirely
    if len(title) < 15 or not summary:
        return "needs_review"

    return "valid"


def parse_published_date(raw_date: Any) -> str:
    """
    Normalizes any raw RSS/article date format (RFC 2822, ISO 8601, struct_time)
    into standard ISO UTC datetime string 'YYYY-MM-DD HH:MM:SS'.
    Guarantees that every article has a valid timestamp for precise recency sorting.
    """
    if not raw_date:
        return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    if isinstance(raw_date, datetime):
        if raw_date.tzinfo is not None:
            raw_date = raw_date.astimezone(timezone.utc).replace(tzinfo=None)
        return raw_date.strftime("%Y-%m-%d %H:%M:%S")

    if isinstance(raw_date, (list, tuple)) and len(raw_date) >= 6:
        try:
            dt = datetime(*raw_date[:6])
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            pass

    date_str = str(raw_date).strip()
    if not date_str or date_str.lower() in ("recently", "none", "null"):
        return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    try:
        dt = dateutil.parser.parse(date_str)
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def process_article(article: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], str]:
    """
    Master news processing function.
    Validates, cleans, normalizes, detects language/category/country,
    extracts keywords, parses publication timestamps, and assigns quality status.
    
    Returns (processed_article_dict, status_message).
    """
    is_valid, reason = validate_article(article)
    if not is_valid:
        logger.warning(f"Article rejected: {reason}")
        return None, reason

    # Step 1: Text Cleaning
    cleaned_title = clean_text(article.get("title"))
    cleaned_summary = clean_text(article.get("summary"))
    cleaned_source = clean_text(article.get("source"))
    cleaned_author = clean_text(article.get("author")) or "Unknown"
    url = (article.get("url") or "").strip()

    # Step 2: Language Detection
    fallback_lang = article.get("language") or "English"
    detected_lang = detect_language(f"{cleaned_title} {cleaned_summary}", fallback_lang=fallback_lang)

    # Step 3: Category Normalization
    raw_cat = article.get("category")
    normalized_cat = normalize_category(raw_cat)

    # Step 4: Country Detection
    detected_cntry = detect_country(cleaned_title, cleaned_summary, cleaned_source)

    # Step 5: Keyword Extraction
    keywords = extract_keywords(cleaned_title, cleaned_summary, top_n=5)

    # Step 6: Publication Timestamp Normalization (YYYY-MM-DD HH:MM:SS)
    published_iso = parse_published_date(article.get("published_at") or article.get("published"))

    # Step 7: Quality Status Calculation
    quality = calculate_quality(article)

    processed = {
        "article_id": article.get("id") or article.get("article_id"),
        "title": cleaned_title,
        "summary": cleaned_summary,
        "url": url,
        "source": cleaned_source,
        "published_at": published_iso,
        "author": cleaned_author,
        "category": normalized_cat,
        "language": detected_lang,
        "country": detected_cntry,
        "keywords": json.dumps(keywords, ensure_ascii=False),
        "quality_status": quality,
    }

    return processed, "Successfully processed"
