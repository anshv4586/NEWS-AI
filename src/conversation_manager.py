"""
Conversation Manager & Query Rewriting Module for Global News AI - Phase 6

Maintains lightweight, in-memory short-term conversation state across chat turns,
stores active context (topic, country, category, time range, retrieved articles),
and rewrites ambiguous follow-up queries into complete standalone search queries.
"""

import logging
from typing import Any, Dict, List, Optional
from src.query_processor import process_query

logger = logging.getLogger(__name__)


class ConversationState:
    """
    Lightweight in-memory conversation state for single-session context.
    Resets cleanly when user clears context or starts a new session.
    """

    def __init__(self):
        self.reset()

    def reset(self):
        """Resets all conversation memory parameters."""
        self.current_topic: Optional[str] = None
        self.current_country: Optional[str] = None
        self.current_category: Optional[str] = None
        self.current_language: str = "English"
        self.current_time_range: str = "all"
        self.recent_queries: List[str] = []
        self.last_retrieved_articles: List[Dict[str, Any]] = []
        self.turns: List[Dict[str, Any]] = []
        logger.info("[ConversationState] Conversation state initialized/cleared.")

    def set_language(self, language: str):
        """Sets active target language for conversation state."""
        if language:
            self.current_language = language


    def update_from_query(self, parsed_query: Dict[str, Any]):
        """
        Updates topic, country, category, language, and time_range from parsed query metadata.
        """
        raw_q = parsed_query.get("raw_query", "")
        if raw_q:
            self.recent_queries.append(raw_q)

        # Update language memory if specified
        lang = parsed_query.get("language")
        if lang:
            self.current_language = lang

        # Update active topic only if explicit new topic found or not a follow-up turn
        new_topic = parsed_query.get("topic")
        if new_topic and not parsed_query.get("is_follow_up"):
            self.current_topic = new_topic

        # Update country if newly specified
        new_country = parsed_query.get("country")
        if new_country:
            self.current_country = new_country

        # Update category if newly specified
        new_category = parsed_query.get("category")
        if new_category:
            self.current_category = new_category

        # Update time range if specified
        time_req = parsed_query.get("time_range")
        if time_req and time_req != "all":
            self.current_time_range = time_req

    def set_retrieved_articles(self, articles: List[Dict[str, Any]]):
        """Stores articles retrieved in the current turn for follow-up references."""
        self.last_retrieved_articles = articles

    def get_article_by_index(self, index: int) -> Optional[Dict[str, Any]]:
        """
        Retrieves article from memory by 1-based index (e.g. 1 for article 1, 2 for article 2).
        """
        if 1 <= index <= len(self.last_retrieved_articles):
            return self.last_retrieved_articles[index - 1]
        return None

    def add_turn(self, user_query: str, answer: str, articles: List[Dict[str, Any]]):
        """Appends a turn tuple to turn history."""
        self.set_retrieved_articles(articles)
        self.turns.append({
            "user_query": user_query,
            "answer": answer,
            "articles_count": len(articles),
        })

    def get_context_summary(self) -> Dict[str, Any]:
        """Returns a snapshot dictionary of active context."""
        return {
            "current_topic": self.current_topic,
            "current_country": self.current_country,
            "current_category": self.current_category,
            "current_time_range": self.current_time_range,
            "recent_queries": self.recent_queries[-3:],
            "articles_in_memory": len(self.last_retrieved_articles),
            "turns_count": len(self.turns),
        }


def rewrite_follow_up_query(
    raw_query: str,
    parsed_query: Dict[str, Any],
    state: ConversationState,
) -> str:
    """
    Rewrites follow-up queries into a standalone retrieval query string
    by merging current turn metadata with active conversation state.
    """
    is_follow_up = parsed_query.get("is_follow_up") or parsed_query.get("query_type") == "follow_up"
    
    # If not a follow up turn or no previous context exists in session memory, use normalized retrieval query
    if not is_follow_up or (not state.turns and not state.recent_queries and not state.current_topic):
        return parsed_query.get("retrieval_query") or raw_query


    q_lower = raw_query.lower().strip()

    # Context variables
    active_topic = state.current_topic
    active_country = parsed_query.get("country") or state.current_country
    active_category = parsed_query.get("category") or state.current_category

    # Case A: "What about <Country>?" or "<Country> mein?" pattern (e.g., "What about India?", "India mein?", "China mein?")
    if any(phrase in q_lower for phrase in ["what about", "how about", "mein", "me", "में"]) or q_lower.startswith(("and ", "aur ", "phir ")):
        if active_country:
            if active_topic:
                rewritten = f"{active_topic} in {active_country}"
            elif active_category:
                rewritten = f"{active_category} news in {active_country}"
            else:
                rewritten = f"news developments in {active_country}"
            logger.info(f"[Query Rewriter] Rewrote follow-up '{raw_query}' -> '{rewritten}'")
            return rewritten

    # Case B: "Give me the latest developments" / "What happened today?" pattern
    if any(kw in q_lower for kw in ["latest", "recent", "updates", "today", "developments"]):
        prefix = "latest developments in" if "latest" in q_lower or "developments" in q_lower else "recent news on"
        if active_topic and active_country:
            rewritten = f"{prefix} {active_topic} in {active_country}"
        elif active_topic:
            rewritten = f"{prefix} {active_topic}"
        elif active_country:
            rewritten = f"{prefix} {active_country}"
        elif active_category:
            rewritten = f"{prefix} {active_category}"
        else:
            rewritten = "latest global news developments"
        logger.info(f"[Query Rewriter] Rewrote follow-up '{raw_query}' -> '{rewritten}'")
        return rewritten

    # Case C: Fallback reconstruction from active state
    parts = []
    if active_topic:
        parts.append(active_topic)
    if active_country:
        parts.append(f"in {active_country}")
    elif active_category:
        parts.append(f"in {active_category}")

    if parts:
        rewritten = " ".join(parts)
        logger.info(f"[Query Rewriter] Rewrote follow-up '{raw_query}' -> '{rewritten}'")
        return rewritten

    return raw_query


if __name__ == "__main__":
    import sys
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    state = ConversationState()

    print("\n--- CONVERSATION STATE & QUERY REWRITING DEMO ---\n")

    # Turn 1
    q1 = "What is happening with AI regulation?"
    p1 = process_query(q1)
    state.update_from_query(p1)
    print(f"Turn 1 Query   : {q1}")
    print(f"Active Context : {state.get_context_summary()}\n")

    # Turn 2: Follow-up
    q2 = "What about India?"
    p2 = process_query(q2)
    rewritten2 = rewrite_follow_up_query(q2, p2, state)
    state.update_from_query(p2)
    print(f"Turn 2 Follow-Up: {q2}")
    print(f"Rewritten Query : {rewritten2}")
    print(f"Active Context  : {state.get_context_summary()}\n")

    # Turn 3: Follow-up
    q3 = "What about China?"
    p3 = process_query(q3)
    rewritten3 = rewrite_follow_up_query(q3, p3, state)
    state.update_from_query(p3)
    print(f"Turn 3 Follow-Up: {q3}")
    print(f"Rewritten Query : {rewritten3}")
    print(f"Active Context  : {state.get_context_summary()}\n")

    # Turn 4: Follow-up
    q4 = "Give me the latest developments."
    p4 = process_query(q4)
    rewritten4 = rewrite_follow_up_query(q4, p4, state)
    state.update_from_query(p4)
    print(f"Turn 4 Follow-Up: {q4}")
    print(f"Rewritten Query : {rewritten4}")
    print(f"Active Context  : {state.get_context_summary()}\n")

    # Turn 5: Clear
    state.reset()
    print("Command         : clear")
    print(f"Active Context  : {state.get_context_summary()}\n")
