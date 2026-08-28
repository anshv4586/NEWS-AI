"""
Interactive Terminal CLI Chat Interface for Global News AI - Phase 5 (RAG + LLM)

Executable with:
    python -m src.chat
"""

import sys
import logging
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Configure UTF-8 encoding for Windows terminal stdout/stderr
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from src.rag_pipeline import answer_conversational_news
from src.conversation_manager import ConversationState
from src.database import test_connection
from src.vector_store import count_vectors

# Configure logger format
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


def main():
    """
    Main interactive CLI loop for Global News AI Conversational Assistant (Phase 6).
    """
    print("\n" + "=" * 80)
    print(" 🌐 GLOBAL NEWS AI - CONVERSATIONAL GLOBAL NEWS ASSISTANT (PHASE 6)")
    print("=" * 80)

    # Health Check
    db_ok = test_connection()
    if not db_ok:
        print("[WARNING] MySQL Database connection failed. Search will operate with vector store data.")

    try:
        vector_count = count_vectors()
        print(f" Ready! Indexed Vector DB documents: {vector_count}")
    except Exception as e:
        print(f"[WARNING] Could not check Vector DB count: {e}")

    print(" Features: Recency Ranking | Country & Category Filters | Follow-up Understanding")
    print(" Languages: English | Hindi (हिंदी) | Hinglish")
    print(" Commands: 'clear' (reset context), 'exit' or 'quit' (exit application)")
    print("-" * 80 + "\n")

    state = ConversationState()

    while True:
        try:
            user_input = input("\nYou > ").strip()
            if not user_input:
                continue

            low_input = user_input.lower()
            if low_input in ("exit", "quit", "q", "bye"):
                print("\nThank you for using Global News AI Assistant. Goodbye! 🚀\n")
                break

            if low_input in ("clear", "reset"):
                state.reset()
                print("\n[INFO] Conversation context cleared successfully!")
                print("-" * 80)
                continue

            print(f"\n[INFO] Processing query: '{user_input}'...")
            res = answer_conversational_news(user_input, state=state)

            if res.get("search_query") and res["search_query"] != user_input:
                print(f"[INFO] Rewritten Search Query: '{res['search_query']}'")

            print("\nAssistant:")
            print(res["formatted_response"])
            print("-" * 80)

        except KeyboardInterrupt:
            print("\nExiting Global News AI Assistant. Goodbye! 🚀\n")
            break
        except Exception as e:
            logger.error(f"Unexpected CLI error: {e}")
            print(f"\n[ERROR] System Error: {e}. Please try again.\n")


if __name__ == "__main__":
    main()

