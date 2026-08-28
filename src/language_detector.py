"""
Multilingual & Hinglish Language Detection Module for Global News AI - Phase 7

Provides fast, high-accuracy language detection distinguishing between:
- English
- Hindi (Devanagari script)
- Hinglish (Romanized Hindi grammar, stopwords, and mixed code-switching)

Supports explicit language overrides (e.g. "Explain in Hindi", "Hinglish mein batao").
"""

import re
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

# Devanagari Script Regex for Hindi
DEVANAGARI_REGEX = re.compile(r"[\u0900-\u097F]")

# Core Hinglish Keyword Lexicon
HINGLISH_KEYWORDS = {
    "aaj", "ab", "accha", "aur", "baare", "batao", "bataiye", "bhi", "chal",
    "chahiye", "duniya", "ek", "ghatna", "haalat", "hai", "hain", "ho", "hua",
    "hun", "iske", "isko", "isse", "jaana", "jante", "jiske", "kab", "kabhi",
    "kaafi", "kaun", "kaise", "karan", "karo", "karna", "ke", "ki", "ko", "kya",
    "kyun", "latest", "lekar", "log", "main", "matlab", "mein", "mera", "mujhe",
    "nahin", "nahi", "naya", "nayi", "par", "phir", "raha", "rahi", "rahe",
    "sab", "saath", "samjhao", "shuru", "sirf", "suraksha", "tarah", "taza",
    "tha", "thi", "the", "tum", "unka", "vistar", "vishaal", "woh", "yeh"
}

# Common Hinglish Multi-Word Phrase Patterns
HINGLISH_PHRASE_PATTERNS = [
    r"\b(kya\s+chal\s+raha)\b",
    r"\b(ke\s+baare\s+mein)\b",
    r"\b(ko\s+lekar)\b",
    r"\b(mein\s+kya)\b",
    r"\b(aaj\s+ki)\b",
    r"\b(batao|bataiye|samjhao)\b",
    r"\b(explain\s+karo)\b",
    r"\b(mein\s+explain)\b",
    r"\b(ab\s+batao)\b",
    r"\b(aur\s+kya)\b",
    r"\b(kya\s+ho\s+raha)\b",
    r"\b(kya\s+updates\s+hain)\b",
]

# Explicit Language Request Override Patterns
EXPLICIT_HINDI_PATTERNS = [
    r"\b(explain\s+(this\s+)?in\s+hindi)\b",
    r"\b(hindi\s+mein)\b",
    r"\b(hindi\s+me)\b",
    r"\b(in\s+hindi)\b",
    r"\b(हिंदी\s+में)\b",
]

EXPLICIT_HINGLISH_PATTERNS = [
    r"\b(explain\s+(this\s+)?in\s+hinglish)\b",
    r"\b(hinglish\s+mein)\b",
    r"\b(hinglish\s+me)\b",
    r"\b(in\s+hinglish)\b",
    r"\b(hinglish)\b",
]

EXPLICIT_ENGLISH_PATTERNS = [
    r"\b(explain\s+(this\s+)?in\s+english)\b",
    r"\b(english\s+mein)\b",
    r"\b(english\s+me)\b",
    r"\b(in\s+english)\b",
]


def check_explicit_language_override(query: str) -> Optional[str]:
    """
    Checks if the user explicitly requested a target response language
    (e.g., 'Explain in Hindi', 'Ab Hinglish mein batao', 'In English please').
    """
    q_lower = query.lower().strip()

    for pattern in EXPLICIT_HINDI_PATTERNS:
        if re.search(pattern, q_lower):
            return "Hindi"

    for pattern in EXPLICIT_HINGLISH_PATTERNS:
        if re.search(pattern, q_lower):
            return "Hinglish"

    for pattern in EXPLICIT_ENGLISH_PATTERNS:
        if re.search(pattern, q_lower):
            return "English"

    return None


def detect_language(query: str) -> Dict[str, Any]:
    """
    Master Language Detection Function.
    Returns dictionary with:
    - language: 'English', 'Hindi', 'Hinglish', or 'Other'
    - explicit_override: str or None
    - confidence: float score between 0.0 and 1.0
    - is_devanagari: bool
    """
    cleaned = (query or "").strip()
    if not cleaned:
        return {
            "language": "English",
            "explicit_override": None,
            "confidence": 1.0,
            "is_devanagari": False,
        }

    # Step 1: Check for explicit language instruction override
    override = check_explicit_language_override(cleaned)
    
    # Step 2: Check for Devanagari script (Hindi)
    devanagari_chars = DEVANAGARI_REGEX.findall(cleaned)
    if devanagari_chars and len(devanagari_chars) >= 2:
        return {
            "language": override or "Hindi",
            "explicit_override": override,
            "confidence": 0.98,
            "is_devanagari": True,
        }

    # Step 3: Check for Hinglish phrases and romanized vocabulary
    q_lower = cleaned.lower()
    words = set(re.findall(r"\b[a-z]+\b", q_lower))
    
    hinglish_matches = words.intersection(HINGLISH_KEYWORDS)
    phrase_matched = any(re.search(pat, q_lower) for pat in HINGLISH_PHRASE_PATTERNS)

    if len(hinglish_matches) >= 2 or phrase_matched:
        detected_lang = override or "Hinglish"
        return {
            "language": detected_lang,
            "explicit_override": override,
            "confidence": 0.92,
            "is_devanagari": False,
        }

    # Step 4: Single strong Hinglish trigger word check (e.g. "mein", "batao", "lekar")
    if len(hinglish_matches) == 1 and not (len(words) >= 6 and "india" in words):
        strong_triggers = {"mein", "batao", "samjhao", "lekar", "baare", "chakti", "phir", "aaj"}
        if hinglish_matches.intersection(strong_triggers):
            detected_lang = override or "Hinglish"
            return {
                "language": detected_lang,
                "explicit_override": override,
                "confidence": 0.85,
                "is_devanagari": False,
            }

    # Default to English
    return {
        "language": override or "English",
        "explicit_override": override,
        "confidence": 0.95,
        "is_devanagari": False,
    }


if __name__ == "__main__":
    import sys
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    test_queries = [
        "What is happening in India today?",
        "भारत में आज क्या हो रहा है?",
        "India mein aaj kya ho raha hai?",
        "AI ke field mein latest news kya hai?",
        "Climate change ko lekar kya updates hain?",
        "Isko Hindi mein explain karo.",
        "Ab Hinglish mein batao.",
        "Now explain in English please.",
        "China aur US ke beech kya chal raha hai?",
    ]

    print("\n--- MULTILINGUAL & HINGLISH LANGUAGE DETECTOR DEMO ---\n")
    for q in test_queries:
        res = detect_language(q)
        print(f"Query   : {q}")
        print(f"Detected: {res['language']} (Override: {res['explicit_override']}, Conf: {res['confidence']})\n")
