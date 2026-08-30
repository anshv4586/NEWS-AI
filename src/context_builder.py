"""
Context & Prompt Builder Module for Global News AI - Phase 5

Constructs structured news context blocks and system instructions
enforcing strict grounding, citation tagging [1], [2], refusal on insufficient data,
and multilingual answer matching (English, Hindi, Hinglish).
"""

from typing import Any, Dict, List, Tuple

def apply_broad_news_diversity(
    articles: List[Dict[str, Any]],
    max_per_category: int = 2,
    max_per_source: int = 2,
) -> List[Dict[str, Any]]:
    """
    Filters retrieved articles for broad queries to ensure news diversity across
    different categories and publishers rather than returning multiple coverage items of 1 event.
    """
    if not articles:
        return []

    category_counts: Dict[str, int] = {}
    source_counts: Dict[str, int] = {}
    diverse_list = []

    for art in articles:
        cat = art.get("category", "World") or "World"
        src = art.get("source", "Unknown") or "Unknown"

        c_count = category_counts.get(cat, 0)
        s_count = source_counts.get(src, 0)

        if c_count < max_per_category and s_count < max_per_source:
            diverse_list.append(art)
            category_counts[cat] = c_count + 1
            source_counts[src] = s_count + 1

    # Fallback to original articles if filtering was too aggressive
    if len(diverse_list) < 2 and len(articles) >= 2:
        return articles

    # Re-rank assigned indices
    for rank, art in enumerate(diverse_list, start=1):
        art["rank"] = rank

    return diverse_list


def build_system_instruction(
    response_mode: str = "default",
    language: str = "English",
) -> str:
    """
    Constructs dynamic system instructions tailoring output length, tone, language,
    and preserving entities, dates, and technical terms.
    """
    length_instruction = {
        "default": "Keep answers concise, direct, factual, and objective (2-4 bullet points or 1-2 short paragraphs).",
        "detailed": "Provide an in-depth, detailed explanation covering background, key facts, and implications.",
        "summary": "Provide a quick, high-level summary (1-2 sentences maximum).",
        "expanded": "Provide a comprehensive, exhaustive breakdown covering all available details in the context.",
    }.get(response_mode, "Keep answers concise, direct, factual, and objective.")

    lang_instruction = {
        "Hindi": "IMPORTANT: Respond in clear, natural Hindi (Devanagari script).",
        "Hinglish": (
            "IMPORTANT: Respond in natural, conversational Hinglish (Romanized Hindi mixed with English terms). "
            "Example Hinglish style: 'India mein AI regulation ko lekar key developments ho rahe hain...'"
        ),
        "English": "Respond in clear, natural English.",
    }.get(language, "Respond in clear, natural English.")

    instruction = f"""You are Global News AI, a professional, factual, grounded conversational global news assistant providing breaking, real-time news updates.

CRITICAL INSTRUCTIONS:
1. Answer the user's question directly using the provided NEWS CONTEXT blocks below.
2. Prioritize and emphasize the freshest breaking news and developments from the last 24 hours.
3. Every factual statement must cite its source article using numerical citation tags like [1], [2], or [3].
4. Summarize the event clearly based on the provided headline, summary details, source publisher, category, and publication date.
5. If the user asks for details or more information about a specific article in the context, provide all available reported facts, background, publisher attribution, and date.
6. Do NOT invent facts or extrapolate beyond the provided text.
7. ENTITY & TERM PRESERVATION:
   - Do NOT translate person names, country names, company names, or organization names (e.g. Donald Trump, India, BBC News, NASA, ISRO).
   - Do NOT translate common technical terms (e.g. AI, software, startups, regulation, climate change, internet).
   - Preserve exact numbers, dates, monetary values, and statistics.
8. ONLY IF the provided news context is completely empty or mentions ZERO relevant articles to the user's question, output EXACTLY:
   "INSUFFICIENT_CONTEXT"
9. {lang_instruction}
10. {length_instruction}
"""
    return instruction


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
        category = art.get("category", "World")
        summary = art.get("summary", "").strip()

        block = (
            f"--- ARTICLE [{rank}] ---\n"
            f"Headline: {title}\n"
            f"Publisher: {source} | Country: {country} | Category: {category} | Published: {pub_date}\n"
            f"Details & Summary: {summary if summary else title}\n"
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
        f"Provide an informative, factual answer summarizing the story and citing sources with [1], [2] where applicable. "
        f"Only if no relevant news context exists at all, output 'INSUFFICIENT_CONTEXT'."
    )
    return prompt

