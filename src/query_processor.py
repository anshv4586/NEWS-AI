"""
Query Processor & Intent Understanding Module for Global News AI - Phase 6

This module provides rule-assisted pattern matching and LLM-ready query parsing
to classify query types, detect metadata parameters (country, category, time range, language),
identify follow-up intents, and extract response length preferences.
"""

import re
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

# Standard Country & Region Mapping
COUNTRY_ALIASES: Dict[str, List[str]] = {
    "India": ["india", "bharat", "delhi", "mumbai", "indian", "भारत"],
    "USA": ["usa", "us", "united states", "america", "american", "washington", "biden", "trump"],
    "China": ["china", "chinese", "beijing"],
    "UK": ["uk", "united kingdom", "britain", "british", "london", "england"],
    "Russia": ["russia", "russian", "moscow"],
    "Ukraine": ["ukraine", "ukrainian", "kyiv", "kiev"],
    "Iran": ["iran", "iranian", "tehran"],
    "Germany": ["germany", "german", "berlin"],
    "France": ["france", "french", "paris"],
    "Japan": ["japan", "japanese", "tokyo"],
    "Europe": ["europe", "european", "eu"],
}

# Standard News Categories
CATEGORY_ALIASES: Dict[str, List[str]] = {
    "Technology": ["technology", "tech", "ai", "artificial intelligence", "software", "cyber", "robotics", "chips", "semiconductor"],
    "Politics": ["politics", "political", "election", "government", "parliament", "policy", "regulation", "diplomacy", "minister"],
    "Business": ["business", "economy", "economic", "market", "finance", "stocks", "trade", "tariffs", "inflation", "bank"],
    "Sports": ["sports", "sport", "cricket", "football", "soccer", "olympics", "tennis", "match"],
    "Science": ["science", "scientific", "space", "nasa", "isro", "research", "astronomy"],
    "Climate": ["climate", "environment", "global warming", "pollution", "carbon", "renewable", "weather"],
    "Health": ["health", "medical", "medicine", "virus", "vaccine", "hospital", "pharma", "pandemic"],
    "Entertainment": ["entertainment", "movie", "cinema", "bollywood", "hollywood", "music", "actor"],
    "World": ["world", "global", "international", "foreign"],
}

from src.language_detector import detect_language as detect_language_advanced


def detect_language(query: str) -> str:
    """
    Detects whether query is English, Hindi, or Hinglish using language_detector module.
    """
    res = detect_language_advanced(query)
    return res["language"]



def extract_countries(query: str) -> List[str]:
    """Extracts all countries/regions present in query text."""
    query_lower = query.lower()
    matched = []
    for country, aliases in COUNTRY_ALIASES.items():
        for alias in aliases:
            pattern = rf"\b{re.escape(alias)}\b"
            if re.search(pattern, query_lower):
                if country not in matched:
                    matched.append(country)
                break
    return matched


def extract_country(query: str) -> Optional[str]:
    """Extracts primary country/region from query text based on word boundaries."""
    countries = extract_countries(query)
    return countries[0] if countries else None


def extract_category(query: str) -> Optional[str]:
    """Extracts news category from query text."""
    query_lower = query.lower()
    for category, aliases in CATEGORY_ALIASES.items():
        for alias in aliases:
            pattern = rf"\b{re.escape(alias)}\b"
            if re.search(pattern, query_lower):
                return category
    return None


def extract_topic(query: str, country: Optional[str] = None, category: Optional[str] = None) -> Optional[str]:
    """
    Extracts the core topic terms from query text by stripping question phrases,
    country names, and category names.
    """
    q = query.lower()
    
    # Common preamble stop-phrases
    preambles = [
        "what is happening with", "what is happening in", "what is happening on",
        "what's happening with", "what's happening in", "what happened to",
        "what happened in", "what happened with", "tell me about",
        "give me the latest on", "give me latest on", "give me the latest developments in",
        "give me news about", "latest news on", "latest news about",
        "india mein", "bharat mein", "kya chal raha hai", "kya ho raha hai",
        "ke field mein", "field mein", "ke area mein", "area mein", "ko lekar",
        "ke baare mein", "ke regarding", "regarding", "concerning", "how are", "approaching",
        "batao", "bataiye", "samjhao"
    ]
    for p in preambles:
        q = q.replace(p, " ")
        
    # Remove matched country alias terms
    for aliases in COUNTRY_ALIASES.values():
        for alias in aliases:
            q = re.sub(rf"\b{re.escape(alias)}\b", " ", q, flags=re.IGNORECASE)
            
    # Remove punctuation & extra whitespace
    q = re.sub(r"[^\w\s]", " ", q)
    words = [w for w in q.split() if w not in ["what", "about", "is", "in", "the", "with", "and", "on", "for", "to", "of", "latest", "news", "today", "yesterday", "recent"]]
    
    topic_str = " ".join(words).strip()
    return topic_str if len(topic_str) >= 2 else None


def extract_time_range(query: str) -> str:
    """Classifies time requirements (today, yesterday, 24h, this week, latest, recent, all)."""
    q = query.lower()
    if "today" in q or "आज" in q:
        return "today"
    elif "yesterday" in q:
        return "yesterday"
    elif "24 hours" in q or "24h" in q or "last 24" in q:
        return "24h"
    elif "this week" in q or "week" in q:
        return "this_week"
    elif "latest" in q or "recent" in q or "newest" in q or "current" in q or "nayi" in q or "taza" in q:
        return "latest"
    return "all"


def detect_response_mode(query: str) -> str:
    """Detects preferred response length mode (default, detailed, summary, expanded)."""
    q = query.lower()
    if "detail" in q or "explain" in q or "vistar" in q or "in-depth" in q:
        return "detailed"
    elif "summary" in q or "summarize" in q or "quick" in q or "brief" in q or "sankshep" in q:
        return "summary"
    elif "everything" in q or "all details" in q or "complete" in q:
        return "expanded"
    return "default"


from src.language_detector import check_explicit_language_override


def check_is_follow_up(query: str) -> bool:
    """
    Checks if a query is likely a follow-up query requiring conversation context.
    """
    q = query.lower().strip()

    # Explicit language switching requests are treated as follow-up turns
    if check_explicit_language_override(query):
        return True

    # Common follow-up patterns in English, Hindi, and Hinglish
    follow_up_triggers = [
        "what about", "how about", "what else", "tell me more",
        "and china", "and india", "what of", "give me the latest",
        "latest developments", "any updates", "more info", "what happened today",
        "kya chal raha", "aur batao", "phir kya hua", "india mein", "china mein",
        "aur china", "aur india", "aur us", "phir", "aur",
        "story 1", "story 2", "article 1", "article 2", "first article", "second article", "third article"
    ]

    # Short query checks (e.g., "What about India?", "India mein?", "China mein?", "And US?")
    if len(q.split()) <= 4:
        if any(q.startswith(trig) for trig in ["what about", "how about", "and ", "give me", "tell me", "aur ", "phir "]):
            return True
        if "mein" in q or "me" in q or "में" in q:
            return True
        if q in ["what happened today?", "what about china?", "give me latest", "latest developments", "what happened today"]:
            return True

    for trig in follow_up_triggers:
        if trig in q:
            return True

    return False



def classify_query_type(query: str, countries: List[str], is_follow_up: bool = False) -> str:
    """
    Classifies query into standard query types:
    - source_request: Asking for news sources/citations.
    - article_reference: Reference to specific article in prior turn ("story 2", "first article").
    - comparison: Comparing news across two or more entities/countries.
    - summary: Direct request for a summary.
    - general_news: Broad queries like "What is happening in the world?"
    - latest_news: Broad queries like "What are the latest global developments?"
    - follow_up: Follow-up query requiring context rewrite.
    - time_based: Time-specific queries like "What happened today?"
    - topic_country_news: Specific news search by topic, country, or category.
    """
    q = query.lower().strip()
    
    # 1. Source Requests
    if any(phrase in q for phrase in ["source", "where did", "citation", "reported this", "links"]):
        return "source_request"
        
    # 2. Article-specific references
    if re.search(r"\b(article|story|item|number)\s*(\d+|one|two|three|first|second|third)\b", q):
        return "article_reference"
        
    # 3. Comparison
    if len(countries) >= 2 or "compare" in q or "versus" in q or "vs" in q:
        return "comparison"
        
    # 4. Explicit Summary Request
    if any(w in q for w in ["summarize", "summary", "sankshep"]):
        return "summary"
        
    # 5. Broad / General world news
    general_patterns = [
        "what is happening in the world",
        "what's happening in the world",
        "global news",
        "top news",
        "main news",
        "world news",
        "duniya mein kya ho raha hai",
    ]
    if any(pattern in q for pattern in general_patterns):
        return "general_news"
        
    # 6. Latest Global Developments
    if "latest developments" in q or "latest global" in q:
        if not is_follow_up:
            return "latest_news"
            
    # 7. Time-based query without explicit topic
    if q in ["what happened today?", "what happened today", "what happened yesterday?", "what happened in the last 24 hours?"]:
        if not is_follow_up:
            return "time_based"

    # 8. Explicit follow-up
    if is_follow_up:
        return "follow_up"
        
    return "topic_country_news"


def normalize_query_for_retrieval(
    query: str,
    topic: Optional[str] = None,
    country: Optional[str] = None,
    category: Optional[str] = None,
    time_range: str = "all",
) -> str:
    """
    Constructs a clean, normalized standalone retrieval query string from extracted parameters
    while preserving the raw user query intact for prompt generation.
    """
    parts = []
    if time_range in ("today", "24h", "latest", "this_week"):
        parts.append("latest")

    if topic:
        parts.append(topic)
    elif category:
        parts.append(f"{category} news")

    if country:
        parts.append(f"in {country}")

    if parts:
        normalized = " ".join(parts).strip()
        logger.info(f"[Query Normalizer] User Query '{query}' -> Normalized Retrieval Query '{normalized}'")
        return normalized

    return query


def process_query(query: str) -> Dict[str, Any]:
    """
    Master Query Analysis Function.
    
    Parses a raw user query string and extracts key parameters:
    - raw_query
    - retrieval_query
    - topic
    - country (primary)
    - countries (list)
    - category
    - time_range
    - language
    - response_mode
    - is_follow_up
    - query_type
    - wants_summary
    - wants_comparison
    - wants_details
    """
    cleaned_query = (query or "").strip()
    
    language = detect_language(cleaned_query)
    countries = extract_countries(cleaned_query)
    country = countries[0] if countries else None
    category = extract_category(cleaned_query)
    topic = extract_topic(cleaned_query, country=country, category=category)
    time_range = extract_time_range(cleaned_query)
    response_mode = detect_response_mode(cleaned_query)
    is_follow_up = check_is_follow_up(cleaned_query)
    query_type = classify_query_type(cleaned_query, countries=countries, is_follow_up=is_follow_up)
    
    retrieval_query = normalize_query_for_retrieval(
        query=cleaned_query,
        topic=topic,
        country=country,
        category=category,
        time_range=time_range,
    )
    
    wants_summary = response_mode == "summary" or query_type == "summary"
    wants_comparison = query_type == "comparison"
    wants_details = response_mode in ("detailed", "expanded")
    
    processed = {
        "raw_query": cleaned_query,
        "retrieval_query": retrieval_query,
        "topic": topic,
        "country": country,
        "countries": countries,
        "category": category,
        "time_range": time_range,
        "language": language,
        "response_mode": response_mode,
        "is_follow_up": is_follow_up,
        "query_type": query_type,
        "wants_summary": wants_summary,
        "wants_comparison": wants_comparison,
        "wants_details": wants_details,
    }
    
    logger.info(
        f"[Query Processor] Analyzed query='{cleaned_query}' | Type={query_type} | Topic='{topic}' | "
        f"Country={country} | Cat={category} | Time={time_range} | Lang={language}"
    )
    
    return processed


if __name__ == "__main__":
    import sys
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    test_queries = [
        "What is happening with AI regulation in India?",
        "What about China?",
        "Give me the latest developments.",
        "How are the US and China approaching AI?",
        "Summarize the latest climate news.",
        "भारत में आज क्या हो रहा है?",
        "India mein technology news batao",
        "What is happening in the world?",
        "Which source reported this story?",
        "Tell me more about article 2 in detail",
    ]
    print("\n--- QUERY PROCESSOR DEMO ---")
    for tq in test_queries:
        res = process_query(tq)
        print(f"Query: {tq}\nParsed: {res}\n")


