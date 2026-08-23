"""
RAG Pipeline Orchestrator Module for Global News AI - Phase 5

Coordinates Semantic Vector Retrieval -> Context Construction -> Anti-Hallucination Prompting ->
LLM Generation -> Verified Source Attribution.
"""

from typing import Any, Dict, List, Tuple
import logging
from src.retriever import retrieve_context_articles, DEFAULT_TOP_K, DEFAULT_SIMILARITY_THRESHOLD
from src.context_builder import (
    SYSTEM_INSTRUCTION_TEMPLATE,
    build_rag_context,
    build_user_prompt,
)
from src.llm import generate_grounded_answer

logger = logging.getLogger(__name__)

# Refusal Response for Unsupported Queries
REFUSAL_MESSAGE = (
    "I couldn't find sufficiently relevant recent news in my available sources to answer that reliably."
)


def format_sources_list(articles: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Constructs a verified list of authentic news sources with MySQL metadata and URLs.
    """
    sources = []
    for art in articles:
        rank = art.get("rank", 1)
        sources.append({
            "citation": f"[{rank}]",
            "source": art.get("source", "Unknown"),
            "title": art.get("title", ""),
            "url": art.get("url", ""),
            "published_at": art.get("published_at", ""),
            "country": art.get("country", "Global"),
        })
    return sources


def format_final_rag_response(
    answer: str,
    sources: List[Dict[str, str]],
) -> str:
    """
    Formats the combined answer and clickable news sources into clean markdown output.
    """
    formatted = [f"📰 **Answer**\n\n{answer}\n"]
    if sources:
        formatted.append("### 📚 **News Sources & References**")
        for s in sources:
            citation = s["citation"]
            source = s["source"]
            title = s["title"]
            url = s["url"]
            pub_date = s["published_at"]
            formatted.append(f"{citation} **[{source}]** {title}\n   • Date: {pub_date} | Link: {url}")
    return "\n\n".join(formatted)


def answer_news_question(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    min_score: float = DEFAULT_SIMILARITY_THRESHOLD,
) -> Dict[str, Any]:
    """
    Master RAG Function:
    1. Retrieves top K vector matches above min_score threshold.
    2. Builds clean context and anti-hallucination prompt.
    3. Invokes LLM.
    4. Attaches verified source citations.
    """
    cleaned_query = (query or "").strip()
    if not cleaned_query:
        return {
            "query": "",
            "answer": "Please enter a valid news question.",
            "sources": [],
            "status": "error",
        }

    logger.info(f"Processing RAG query: '{cleaned_query}'...")

    # Step 1: Semantic Vector Retrieval
    retrieved_articles = retrieve_context_articles(
        cleaned_query, top_k=top_k, min_score=min_score
    )

    if not retrieved_articles:
        logger.info(f"No relevant news context found above similarity threshold {min_score}.")
        return {
            "query": cleaned_query,
            "answer": REFUSAL_MESSAGE,
            "sources": [],
            "retrieved_articles": [],
            "formatted_response": f"📰 **Answer**\n\n{REFUSAL_MESSAGE}",
            "status": "insufficient_context",
        }

    # Step 2: Context & Prompt Construction
    context_str = build_rag_context(retrieved_articles)
    user_prompt = build_user_prompt(cleaned_query, context_str)
    sources = format_sources_list(retrieved_articles)

    # Step 3: LLM Generation
    try:
        raw_answer = generate_grounded_answer(
            prompt=user_prompt,
            system_instruction=SYSTEM_INSTRUCTION_TEMPLATE,
            temperature=0.2,
        )

        # Step 4: Check if LLM flagged insufficient context
        if "INSUFFICIENT_CONTEXT" in raw_answer.upper():
            logger.info("LLM flagged context as insufficient for query.")
            return {
                "query": cleaned_query,
                "answer": REFUSAL_MESSAGE,
                "sources": [],
                "retrieved_articles": retrieved_articles,
                "formatted_response": f"📰 **Answer**\n\n{REFUSAL_MESSAGE}",
                "status": "insufficient_context",
            }

        formatted_response = format_final_rag_response(raw_answer, sources)
        return {
            "query": cleaned_query,
            "answer": raw_answer,
            "sources": sources,
            "retrieved_articles": retrieved_articles,
            "formatted_response": formatted_response,
            "status": "success",
        }

    except Exception as e:
        logger.error(f"Error during RAG LLM generation: {e}")
        # Graceful error handling without dumping tracebacks
        error_msg = f"Sorry, I couldn't generate the answer because the LLM service is currently unavailable or API credentials are not configured. Details: {e}"
        return {
            "query": cleaned_query,
            "answer": error_msg,
            "sources": sources,
            "retrieved_articles": retrieved_articles,
            "formatted_response": f"📰 **Answer**\n\n{error_msg}",
            "status": "error",
        }
