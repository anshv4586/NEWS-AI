# 🌍 Global News AI — Real-Time Multilingual Grounded RAG Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-gold.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React 19](https://img.shields.io/badge/React-19-61DAFB.svg?logo=react&logoColor=black)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-5.0%2B-646CFF.svg?logo=vite&logoColor=white)](https://vitejs.dev/)
[![Gemini 3.5 Flash](https://img.shields.io/badge/Google%20Gemini-3.5%20Flash-4285F4.svg?logo=google&logoColor=white)](https://ai.google.dev/)
[![Vercel Deployment](https://img.shields.io/badge/Vercel-Serverless%20Ready-000000.svg?logo=vercel&logoColor=white)](https://vercel.com/)

**Global News AI** is a high-performance, full-stack conversational intelligence platform and Retrieval-Augmented Generation (RAG) assistant. It provides **real-time breaking news updates, verified story breakdowns, and grounded question answering** across **English, Hindi (हिन्दी), and Hinglish**, with direct source citations (`[1]`, `[2]`).

Built for both **local development** and **serverless cloud deployment (Vercel)** with sub-second cold starts, dynamic database failover, and strict news quality validation.

---

## 🌟 Core Highlights & Capabilities

- ⚡ **Sub-Second Cold Starts & Zero Gateway Timeouts**
  - Lazy-loaded ML pipelines and parallelized RSS collectors ensure cold-start responses under **0.44s**.
  - Fully optimized for Vercel serverless functions with memory and execution budget management.

- 📰 **Verified Top Headlines (#1 to #10)**
  - Quality-gated ingestion stream: only articles with substantive, verified details (40+ characters of factual context) are featured.
  - **1-Click AI Analysis**: Click any headline from #1 to #10 to trigger an immediate, deep-dive grounded analysis.

- 🤖 **Grounded Conversational RAG with Strict Citations**
  - Powered by **Google Gemini 3.5 Flash** with automatic model failover (`gemini-3.5-flash-lite`, `gemini-3.5-flash`, `gemini-3.1-flash-lite`).
  - Strict grounding prevents hallucinations and preserves exact entity names, numbers, statistics, and dates.
  - Numerical citation tags (`[1]`, `[2]`) linked directly to verified publisher URLs (BBC, Al Jazeera, TechCrunch, Reuters, etc.).

- 🌐 **Multilingual & Dynamic Language Switching**
  - Native understanding and fluent generation in **English**, **Hindi (Devanagari)**, and **Hinglish** (Romanized Hindi).
  - Seamless in-flight language switching (*"Explain in Hindi"*, *"Ab Hinglish mein batao"*).

- 🔐 **Passwordless OTP Authentication & Session Security**
  - **Email & Phone Number Login**: Country-code selector (defaulting to **India +91**).
  - **6-Digit Auto-Focus OTP Input**: Auto-advance, backspace navigation, paste handling, and 60-second countdown.
  - **Salted SHA-256 Security**: OTPs are salted and hashed on the backend—never stored in plain text.
  - **HTTP-Only Session Cookies**: Session management using `HttpOnly`, `SameSite=Lax` cookies with rate limiting.

- 🗄️ **Dual Database Architecture (MySQL + SQLite Failover)**
  - Seamlessly connects to local/cloud MySQL databases.
  - Automatically fails over to an embedded, persistent SQLite engine when running serverless or in environments without MySQL.

---

## 🔄 System Architecture

```text
 ┌───────────────────────────────────────────────────────────────────────────┐
 │                       REACT 19 FRONTEND (Vite / Vercel)                  │
 │                                                                           │
 │  • Glassmorphic Responsive Interface & Fullscreen Mode                    │
 │  • Verified Top 10 World News Rankings (#1 to #10)                        │
 │  • Real-Time Conversational Chat with Grounded Source Cards               │
 │  • 6-Digit Auto-Advance OTP Authentication Modal                          │
 └────────────────────────────────────┬──────────────────────────────────────┘
                                      │ HTTP / CORS Proxy (/api/*)
 ┌────────────────────────────────────▼──────────────────────────────────────┐
 │                       FASTAPI SERVERLESS BACKEND                          │
 │                                                                           │
 │  • POST /api/chat           -> Conversational RAG Engine                  │
 │  • GET  /api/news/latest    -> Quality-Gated Live Headlines (#1 to #10)   │
 │  • POST /api/auth/send-otp  -> Salted Hash Generation & OTP Dispatch      │
 │  • POST /api/auth/verify-otp-> Rate-Limited Verification & Session Cookie │
 │  • GET  /api/auth/me        -> User Profile & Saved Bookmarks             │
 └───────────────────┬───────────────────────────────────┬───────────────────┘
                     │                                   │
 ┌───────────────────▼───────────────┐   ┌───────────────▼───────────────────┐
 │       HYBRID RETRIEVAL LAYER      │   │     DATABASE & STORAGE LAYER      │
 │                                   │   │                                   │
 │ • Exact/Fuzzy Headline Matcher    │   │ • Primary : MySQL 8.0+            │
 │ • ChromaDB Vector Semantic Search │   │ • Serverless Failover: SQLite     │
 │ • Recency Decay Reranker (w_rec)  │   │ • In-Memory Cooldown Cache        │
 └───────────────────┬───────────────┘   └───────────────────────────────────┘
                     │
 ┌───────────────────▼───────────────┐
 │       LLM GROUNDING ENGINE        │
 │                                   │
 │ • Google Gemini 3.5 Flash-Lite    │
 │ • OpenAI GPT-4o Fallback Support  │
 │ • Citation & Entity Verification  │
 └───────────────────────────────────┘
```

---

## 🚀 Quick Start (Local Development)

### 1. Prerequisites
- **Python 3.10+**
- **Node.js 18+** & **npm**
- *(Optional)* MySQL Server 8.0+ (SQLite fallback is enabled by default)

### 2. Clone and Setup
```bash
# Clone the repository
git clone https://github.com/anshv4586/NEWS-AI.git
cd NEWS-AI

# Create and activate Python virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install Python backend dependencies
pip install -r requirements.txt

# Install React frontend dependencies
cd frontend
npm install
cd ..
```

### 3. Configure Environment Variables (`.env`)
Create a `.env` file in the project root:
```ini
# Gemini API Key (Required for AI responses)
GEMINI_API_KEY=your_google_gemini_api_key_here
LLM_PROVIDER=gemini
LLM_MODEL=gemini-3.5-flash-lite

# Database Configuration (Optional - Defaults to SQLite if omitted)
DB_HOST=localhost
DB_PORT=3306
DB_NAME=global_news
DB_USER=root
DB_PASSWORD=your_mysql_password

# Session Security
SESSION_SECRET=your_super_secret_session_key_here
```

### 4. Launch Application
Start both the FastAPI backend and Vite frontend with a single command:
```bash
python run_app.py
```
- **Web UI**: [http://localhost:5173](http://localhost:5173)
- **FastAPI REST API**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Swagger Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## ☁️ Deploying to Vercel (Production)

This repository is pre-configured for zero-config deployment on **Vercel** via `vercel.json`.

### Steps to Deploy:
1. Push your code to GitHub.
2. Import your repository into [Vercel](https://vercel.com/).
3. In the Vercel Project Settings, navigate to **Settings** → **Environment Variables** and add:
   - `GEMINI_API_KEY`: *(Your Google Gemini API Key)*
   - `LLM_PROVIDER`: `gemini`
   - `SESSION_SECRET`: *(A random 32-character secret string)*
4. Click **Deploy**. Vercel will automatically build the React frontend and deploy the FastAPI serverless API routes.

---

## 📡 REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/chat` | Main conversational RAG endpoint (supports queries & follow-ups) |
| `GET` | `/api/news/latest` | Fetches the top verified breaking headlines (#1 to #10) |
| `GET` | `/api/news/category/{category}` | Retrieves filtered news by topic (World, Tech, Business, Sports, etc.) |
| `POST` | `/api/auth/send-otp` | Sends a 6-digit verification code to email or phone number |
| `POST` | `/api/auth/verify-otp` | Verifies OTP code, establishes session, and sets secure cookie |
| `GET` | `/api/auth/me` | Returns current user profile, authentication status, and saved bookmarks |
| `POST` | `/api/auth/logout` | Clears active authentication session and cookie |
| `GET` | `/api/health` | Healthcheck endpoint reporting DB driver status and uptime |

---

## 📁 Project Structure

```text
NEWS-AI/
├── api/
│   └── index.py            # Vercel Serverless Function entry point
├── config/
│   └── feeds.py            # RSS Feed Sources Configuration
├── database/
│   ├── schema.sql          # Core News Table Schema
│   └── auth_schema.sql     # Auth, Users, Sessions & Bookmarks Schema
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── AuthModal.jsx        # 6-Digit OTP Verification Modal
│   │   │   ├── Header.jsx           # Fullscreen Toggle & Brand Header
│   │   │   ├── HeroWelcome.jsx      # Welcome Banner Component
│   │   │   ├── TopHeadlineCard.jsx  # Top 10 World News Rankings
│   │   │   ├── CategoryPills.jsx    # News Category Filter Pills
│   │   │   ├── ChatSection.jsx      # Conversational Chat & Grounded Sources
│   │   │   ├── BottomNav.jsx        # Mobile & Desktop Navigation Bar
│   │   │   └── Modals.jsx           # History, Saved Bookmarks & Settings Modals
│   │   ├── services/
│   │   │   └── api.js               # REST Client with Smart Relative Proxying
│   │   ├── App.jsx                  # Main Application Component
│   │   ├── App.css                  # Design Tokens, Glassmorphism & Animations
│   │   └── index.css                # Global Theme Variables
│   ├── package.json                 # Frontend Dependencies & Build Scripts
│   └── vite.config.js               # Vite Proxy & Server Configuration
├── src/
│   ├── api/
│   │   ├── app.py          # FastAPI Application Setup & Middleware
│   │   ├── routes_chat.py  # Conversational REST Endpoints
│   │   ├── routes_news.py  # Top 10 & Category News Endpoints
│   │   ├── routes_auth.py  # OTP Auth & User Bookmarks Endpoints
│   │   └── routes_voice.py # Speech-to-Text & Voice Endpoints
│   ├── auth.py             # OTP Generation, Salting & Session Core
│   ├── auth_repository.py  # Database Persistence for Users & Sessions
│   ├── database.py         # MySQL & SQLite Failover Connection Manager
│   ├── news_repository.py  # Quality-Gated News Queries & Seed Seeder
│   ├── rag_pipeline.py     # Grounded Conversational RAG Pipeline
│   ├── retriever.py        # Hybrid Vector Retrieval & Fuzzy Matcher
│   ├── query_processor.py  # Intent Understanding & Query Rewriter
│   ├── context_builder.py  # Prompt Construction & Citation Builder
│   ├── embeddings.py       # Sentence Transformers Vector Generator
│   ├── vector_store.py     # ChromaDB Vector Store Client
│   ├── rss_collector.py    # Multi-Threaded RSS Ingestion Engine
│   ├── news_processor.py   # Article Validation, Quality Scoring & Tagging
│   ├── cleaner.py          # HTML Stripping & URL Normalization
│   └── llm.py              # Google Gemini & OpenAI Client Wrapper
├── run_app.py              # Full-System Concurrent Dev Server Launcher
├── vercel.json             # Vercel Serverless Routing & Deployment Config
├── requirements.txt        # Python Dependencies
└── README.md               # Project Documentation
```

---

## 🛡️ Security & Reliability

- **Salted SHA-256 OTPs**: Authentication codes are salted and hashed with secret keys; raw codes are never stored in databases.
- **Strict Grounding**: The AI answers strictly from authenticated news contexts and cites exact sources, preventing hallucinations.
- **Rate-Limiting**: Built-in throttling on OTP requests and session generation prevents brute-force attempts.
- **Automatic Driver Failover**: Seamlessly switches to SQLite if MySQL is unreachable, guaranteeing zero downtime.

---

## 📜 License

Distributed under the **MIT License**. See [LICENSE](LICENSE) for details.
