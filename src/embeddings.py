"""
Embeddings Module for Global News AI - Phase 4

Provides a singleton loader for the multilingual SentenceTransformers model
('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'), structured text
preparation, and single/batch vector embedding generation.
"""

from typing import Any, Dict, List, Optional
import json
import logging
logger = logging.getLogger(__name__)

# Model configuration constants
DEFAULT_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDING_DIMENSION = 384

# Module-level cached model instance (Singleton pattern)
_MODEL_INSTANCE: Optional[Any] = None
_CHECKED_TRANSFORMERS: bool = False
_HAS_SENTENCE_TRANSFORMERS: bool = False


def get_embedding_model(model_name: str = DEFAULT_MODEL_NAME) -> Any:
    """
    Loads and caches the SentenceTransformer model instance lazily on first use.
    Avoids heavy PyTorch import overhead on serverless startup.
    """
    global _MODEL_INSTANCE, _CHECKED_TRANSFORMERS, _HAS_SENTENCE_TRANSFORMERS
    import os
    if os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        # In serverless environments, avoid downloading 500MB weights on cold start
        return None

    if not _CHECKED_TRANSFORMERS:
        try:
            from sentence_transformers import SentenceTransformer
            _HAS_SENTENCE_TRANSFORMERS = True
        except Exception:
            _HAS_SENTENCE_TRANSFORMERS = False
        _CHECKED_TRANSFORMERS = True

    if not _HAS_SENTENCE_TRANSFORMERS:
        logger.debug("SentenceTransformers library not installed. Vector embeddings disabled.")
        return None

    if _MODEL_INSTANCE is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading SentenceTransformer embedding model: '{model_name}'...")
            _MODEL_INSTANCE = SentenceTransformer(model_name)
            logger.info(f"Embedding model loaded successfully (Dimension: {EMBEDDING_DIMENSION}).")
        except Exception as err:
            logger.warning(f"Could not load SentenceTransformer model: {err}")
            _MODEL_INSTANCE = None
    return _MODEL_INSTANCE



def prepare_embedding_text(article: Dict[str, Any]) -> str:
    """
    Constructs a rich, structured text representation of an article for vector embedding.
    Combines headline, summary, category taxonomy, country location, and keywords.
    """
    title = (article.get("title") or "").strip()
    summary = (article.get("summary") or "").strip()
    category = (article.get("category") or "World").strip()
    country = (article.get("country") or "Global").strip()

    # Parse keywords if stored as JSON string or list
    raw_keywords = article.get("keywords")
    if isinstance(raw_keywords, list):
        keywords_str = ", ".join(raw_keywords)
    elif isinstance(raw_keywords, str) and raw_keywords.startswith("["):
        try:
            kw_list = json.loads(raw_keywords)
            keywords_str = ", ".join(kw_list) if isinstance(kw_list, list) else raw_keywords
        except json.JSONDecodeError:
            keywords_str = raw_keywords
    else:
        keywords_str = str(raw_keywords or "")

    parts = [f"Title: {title}"]
    if summary:
        parts.append(f"Summary: {summary}")
    parts.append(f"Category: {category} | Country: {country}")
    if keywords_str:
        parts.append(f"Keywords: {keywords_str}")

    return "\n".join(parts)


def create_embedding(text: str) -> List[float]:
    """
    Generates a 384-dimensional vector embedding for a single text query or document.
    """
    if not text or not text.strip():
        return [0.0] * EMBEDDING_DIMENSION

    model = get_embedding_model()
    if not model:
        return [0.0] * EMBEDDING_DIMENSION

    embedding_vector = model.encode(text.strip(), convert_to_numpy=True).tolist()
    return embedding_vector


def create_embeddings_batch(texts: List[str], batch_size: int = 32) -> List[List[float]]:
    """
    Generates 384-dimensional vector embeddings for a list of text passages in batches.
    """
    if not texts:
        return []

    model = get_embedding_model()
    if not model:
        return [[0.0] * EMBEDDING_DIMENSION for _ in texts]

    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=False,
        convert_to_numpy=True,
    ).tolist()
    return embeddings

