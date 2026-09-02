"""
Vercel Serverless Function Entry Point for FastAPI Backend
"""

import sys
from pathlib import Path

# Add root directory to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from src.api.app import app

# Expose handler alias for Vercel serverless function runners
handler = app
