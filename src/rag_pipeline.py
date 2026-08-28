import sys
import re
from typing import Any, Dict, List, Optional
import logging

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from src.query_processor import process_query
from src.language_detector import check_explicit_language_override
from src.conversation_manager import ConversationState, rewrite_follow_up_query
from src.retriever import retrieve_context_articles, DEFAULT_TOP_K, DEFAULT_SIMILARITY_THRESHOLD
from src.context_builder import (
    apply_broad_news_diversity,
    build_system_instruction,
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


def extract_article_index_reference(query: str) -> Optional[int]:
    """
    Extracts numerical index (1-based) from queries like 'tell me about story 2' or 'first article'.
    """
    q = query.lower().strip()
    match = re.search(r"\b(article|story|item|number)\s*(\d+)\b", q)
    if match:
        return int(match.group(2))

    words_to_num = {"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5, "1st": 1, "2nd": 2, "3rd": 3}
    for w, val in words_to_num.items():
        if w in q:
            return val
    return None


def answer_conversational_news(
    query: str,
    state: Optional[ConversationState] = None,
    top_k: int = DEFAULT_TOP_K,
    min_score: float = DEFAULT_SIMILARITY_THRESHOLD,
) -> Dict[str, Any]:
    """
    Master Conversational RAG Pipeline (Phase 7 Multilingual):
    1. Manages ConversationState across chat turns.
    2. Analyzes intent, language, country, category, time requirements.
    3. Handles explicit language switching turns ('Explain in Hindi', 'Ab Hinglish mein').
    4. Rewrites ambiguous follow-up queries into standalone search queries.
    5. Applies hybrid vector + metadata filters + recency decay ranking.
    6. Formats dynamic system instructions matching requested language & style.
    7. Generates grounded answer with real source citations.
    """
    cleaned_query = (query or "").strip()
    if not cleaned_query:
        return {
            "query": "",
            "answer": "Please enter a valid news question.",
            "sources": [],
            "status": "error",
        }

    if state is None:
        state = ConversationState()

    # Reset command handling
    if cleaned_query.lower() in ("clear", "reset"):
        state.reset()
        msg = "Conversation history cleared! Ask me anything about global news."
        return {
            "query": cleaned_query,
            "answer": msg,
            "sources": [],
            "retrieved_articles": [],
            "formatted_response": f"📰 **Answer**\n\n{msg}",
            "status": "success",
        }

    logger.info(f"[Conversational RAG] Received user query: '{cleaned_query}'...")

    # Step 1: Query Analysis & Language Detection
    parsed = process_query(cleaned_query)
    q_type = parsed.get("query_type")
    resp_mode = parsed.get("response_mode", "default")

    # Language Resolution Priority: Explicit Override > Turn Language > Session State Language
    explicit_lang = check_explicit_language_override(cleaned_query)
    target_lang = explicit_lang or parsed.get("language") or state.current_language
    state.current_language = target_lang

    # Step 2: Handle Source-Related Queries ("Show me the sources")
    if q_type == "source_request":
        last_arts = state.last_retrieved_articles
        if not last_arts:
            answer_text = "No news articles have been retrieved in this conversation yet."
            return {
                "query": cleaned_query,
                "answer": answer_text,
                "sources": [],
                "formatted_response": f"📰 **Answer**\n\n{answer_text}",
                "status": "no_previous_sources",
            }
        sources = format_sources_list(last_arts)
        answer_text = f"Here are the authentic sources used for the previous response ({len(sources)} sources):"
        formatted_response = format_final_rag_response(answer_text, sources)
        return {
            "query": cleaned_query,
            "answer": answer_text,
            "sources": sources,
            "retrieved_articles": last_arts,
            "formatted_response": formatted_response,
            "status": "success",
        }

    # Step 3: Handle Pure Language Switching Turns ("Explain in Hindi", "Ab Hinglish mein")
    if explicit_lang and state.last_retrieved_articles and not (parsed.get("country") and parsed.get("country") != state.current_country):
        logger.info(f"[Conversational RAG] Explicit language switch turn to '{explicit_lang}'. Reusing previous article context ({len(state.last_retrieved_articles)} articles).")
        retrieved_articles = state.last_retrieved_articles
        search_query = cleaned_query
    elif q_type == "article_reference":
        idx = extract_article_index_reference(cleaned_query)
        target_art = state.get_article_by_index(idx) if idx else None
        if target_art:
            retrieved_articles = [target_art]
        else:
            retrieved_articles = state.last_retrieved_articles[:1]

        if not retrieved_articles:
            return {
                "query": cleaned_query,
                "answer": REFUSAL_MESSAGE,
                "sources": [],
                "formatted_response": f"📰 **Answer**\n\n{REFUSAL_MESSAGE}",
                "status": "insufficient_context",
            }
        search_query = cleaned_query
    else:
        # Step 4: Standalone Query Rewriting
        search_query = rewrite_follow_up_query(cleaned_query, parsed, state)
        state.update_from_query(parsed)

        country_filter = parsed.get("country")
        category_filter = parsed.get("category")
        time_range = parsed.get("time_range", "all")

        # Step 5: Multilingual Hybrid Retrieval + Metadata Filtering + Recency Ranking
        retrieved_articles = retrieve_context_articles(
            query=search_query,
            top_k=top_k,
            min_score=min_score,
            country=country_filter,
            category=category_filter,
            time_range=time_range,
        )

        # Step 6: Broad News Diversity Filter for General Queries
        if q_type in ("general_news", "latest_news"):
            retrieved_articles = apply_broad_news_diversity(retrieved_articles)

    if not retrieved_articles:
        logger.info(f"No relevant news context found for query: '{search_query}'.")
        return {
            "query": cleaned_query,
            "answer": REFUSAL_MESSAGE,
            "sources": [],
            "retrieved_articles": [],
            "formatted_response": f"📰 **Answer**\n\n{REFUSAL_MESSAGE}",
            "status": "insufficient_context",
        }

    # Store articles in conversation state memory
    state.set_retrieved_articles(retrieved_articles)
    sources = format_sources_list(retrieved_articles)

    # Step 7: Context & Dynamic Prompt Construction
    context_str = build_rag_context(retrieved_articles)
    system_instruction = build_system_instruction(response_mode=resp_mode, language=target_lang)
    user_prompt = build_user_prompt(search_query, context_str)

    # Step 8: LLM Generation
    try:
        raw_answer = generate_grounded_answer(
            prompt=user_prompt,
            system_instruction=system_instruction,
            temperature=0.2,
        )

        if "INSUFFICIENT_CONTEXT" in raw_answer.upper():
            logger.info("LLM flagged context as insufficient.")
            return {
                "query": cleaned_query,
                "answer": REFUSAL_MESSAGE,
                "sources": [],
                "retrieved_articles": retrieved_articles,
                "formatted_response": f"📰 **Answer**\n\n{REFUSAL_MESSAGE}",
                "status": "insufficient_context",
            }

        state.add_turn(user_query=cleaned_query, answer=raw_answer, articles=retrieved_articles)
        formatted_response = format_final_rag_response(raw_answer, sources)

        return {
            "query": cleaned_query,
            "search_query": search_query,
            "answer": raw_answer,
            "sources": sources,
            "retrieved_articles": retrieved_articles,
            "formatted_response": formatted_response,
            "status": "success",
        }

    except Exception as e:
        logger.error(f"Error during Conversational LLM generation: {e}")
        error_msg = f"Sorry, I couldn't generate the answer because the LLM service is currently unavailable. Details: {e}"
        return {
            "query": cleaned_query,
            "answer": error_msg,
            "sources": sources,
            "retrieved_articles": retrieved_articles,
            "formatted_response": f"📰 **Answer**\n\n{error_msg}",
            "status": "error",
        }


def answer_news_question(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    min_score: float = DEFAULT_SIMILARITY_THRESHOLD,
) -> Dict[str, Any]:
    """
    Backward-compatible wrapper for single-turn queries.
    """
    return answer_conversational_news(query=query, top_k=top_k, min_score=min_score)

