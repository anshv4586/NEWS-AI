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

from src.rag_pipeline import answer_news_question
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
    Main interactive CLI loop for Global News AI Assistant.
    """
    print("\n" + "=" * 80)
    print(" 🌐 GLOBAL NEWS AI - RAG + LLM ASSISTANT (PHASE 5)")
    print("=" * 80)

    # Health Check
    db_ok = test_connection()
    if not db_ok:
        print("[WARNING] MySQL Database connection failed. Search will operate with limited data.")

    vector_count = count_vectors()
    print(f" Ready! Indexed Vector DB documents: {vector_count}")
    print(" Ask news questions in English, Hindi, or Hinglish.")
    print(" Type 'exit' or 'quit' to close.\n" + "-" * 80 + "\n")

    while True:
        try:
            user_input = input("\nUser Query > ").strip()
            if not user_input:
                continue

            if user_input.lower() in ("exit", "quit", "q", "bye"):
                print("\nThank you for using Global News AI. Goodbye! 🚀\n")
                break

            print(f"\n[INFO] Retrieving news & generating answer for: '{user_input}'...")
            rag_res = answer_news_question(user_input)

            print("\n" + rag_res["formatted_response"])
            print("-" * 80)

        except KeyboardInterrupt:
            print("\nExiting Global News AI. Goodbye!")
            break
        except Exception as e:
            print(f"\n[ERROR] System Error: {e}\n")


if __name__ == "__main__":
    main()
