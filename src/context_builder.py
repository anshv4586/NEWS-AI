"""
Context & Prompt Builder Module for Global News AI - Phase 5

Constructs structured news context blocks and system instructions
enforcing strict grounding, citation tagging [1], [2], refusal on insufficient data,
and multilingual answer matching (English, Hindi, Hinglish).
"""

from typing import Any, Dict, List, Tuple

# System Prompt Template enforcing strict anti-hallucination rules
SYSTEM_INSTRUCTION_TEMPLATE = """You are Global News AI, a professional, factual, grounded news assistant.

CRITICAL INSTRUCTIONS:
1. Answer the user's question using ONLY the provided NEWS CONTEXT blocks below.
2. Do NOT invent facts, assume unmentioned events occurred, or extrapolate beyond the provided text.
3. Every factual statement must cite its source article using numerical citation tags like [1], [2], or [3].
4. Do NOT fabricate URLs or web links. Source URLs will be attached automatically by the application.
5. IF THE PROVIDED NEWS CONTEXT DOES NOT CONTAIN ENOUGH RELEVANT INFORMATION to reliably answer the question, output EXACTLY the phrase:
   "INSUFFICIENT_CONTEXT"
6. Respond in the SAME LANGUAGE as the user's question (English, Hindi, or Hinglish).
7. Keep answers concise, factual, objective, and clearly structured.
"""


def build_rag_context(articles: List[Dict[str, Any]]) -> str:
    """
    Formats a list of retrieved articles into clean, numbered context blocks.
    """
    if not articles:
        return "NO RELEVANT NEWS CONTEXT AVAILABLE."

    context_blocks = []
    for art in articles:
        rank = art.get("rank", 1)
        title = art.get("title", "").strip()
        source = art.get("source", "Unknown").strip()
        pub_date = art.get("published_at") or "Date Unknown"
        country = art.get("country", "Global")
        summary = art.get("summary", "").strip()

        block = (
            f"--- ARTICLE [{rank}] ---\n"
            f"Title: {title}\n"
            f"Source: {source} | Country: {country} | Date: {pub_date}\n"
            f"Summary: {summary if summary else 'No summary content provided.'}\n"
        )
        context_blocks.append(block)

    return "\n".join(context_blocks)


def build_user_prompt(query: str, context_str: str) -> str:
    """
    Combines user query and formatted news context into final user prompt.
    """
    prompt = (
        f"NEWS CONTEXT:\n"
        f"{context_str}\n\n"
        f"USER QUESTION: {query.strip()}\n\n"
        f"Provide a clear, grounded answer using citation tags [1], [2] where applicable. "
        f"If the context above is not sufficient to answer, reply with 'INSUFFICIENT_CONTEXT'."
    )
    return prompt
