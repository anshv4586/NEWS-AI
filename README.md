# 🌍 Global News AI — Multilingual Grounded RAG Companion

![License](https://img.shields.io/badge/License-MIT-gold.svg)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-green.svg)
![React](https://img.shields.io/badge/React-18-cyan.svg)
![Vite](https://img.shields.io/badge/Vite-5.0-purple.svg)
![MySQL](https://img.shields.io/badge/MySQL-8.0-orange.svg)
![ChromaDB](https://img.shields.io/badge/ChromaDB-VectorStore-red.svg)

**Global News AI** is a state-of-the-art, full-stack conversational news platform and grounded Retrieval-Augmented Generation (RAG) assistant. Users can interact via **Text or Voice** in **English, Hindi, or Hinglish** to receive concise, factual, and up-to-date global news summaries backed by real source verification.

---

## 🌟 Key Features

- 🖥️ **Widescreen & Fullscreen Widescreen UI**
  - Modern ChatGPT/Claude-style glassmorphic UI built with **React 18**, **Vite**, and **Vanilla CSS**.
  - Features HTML5 Fullscreen toggle mode (`Maximize2` / `Minimize2`) and responsive desktop sidebar panel displaying chat history and saved bookmarks.
  - Seamless Light & Dark mode toggle.

- 🔥 **Interactive Top 10 World News Rankings (#1 to #10)**
  - Real-time ingestion feed featuring top ranked world headlines.
  - Interactive Top 10 World News Drawer with rank badges (`#1`, `#2`, `#3` highlighted in gold/bronze gradients).
  - **1-Click AI Analysis**: Click any headline from #1 to #10 to instantly prompt News AI for a detailed breakdown.

- 🔐 **Secure OTP-Based Authentication System**
  - **Email & Phone Number Login**: Flexible choice with country-code selector (defaults to **India +91**).
  - **6-Digit Auto-Focus OTP Input**: Individual digit boxes with auto-advance, backspace navigation, paste handling, and 60-second countdown timer.
  - **Salted SHA-256 Security**: OTPs are salted and hashed on the backend; plain OTPs are **never** stored or sent to the browser.
  - **HTTP-Only Session Cookies**: Session tokens stored securely in `HttpOnly` and `SameSite=Lax` cookies.
  - **Rate Limiting & Protection**: Max 3 OTP requests per 10-minute window and 5 verification attempts per OTP code.
  - **Development OTP Logger**: Built-in fallback logger for friction-free local development when SMTP/Twilio keys are omitted.

- 🎙️ **Multilingual Intelligence & Voice Interaction**
  - Dynamic language detection and support for **English**, **Hindi (हिन्दी)**, and **Hinglish**.
  - Integrated Speech-to-Text (STT) and Text-to-Speech (TTS) audio playback.

- ⚡ **Grounded RAG Engine & Continuous Ingestion Worker**
  - Background worker continuously monitors RSS feeds (BBC, Al Jazeera, Reuters) and updates MySQL & ChromaDB vector store.
  - Hybrid retrieval with recency decay reranking and Gemini-3.6-flash RAG answer generation.

---

## 🚀 Quick Start (All-in-One Launcher)

To launch the complete application (FastAPI Backend + React Web UI) with automatic browser launching in one single command:

```bash
python run_app.py
```

- **React Web UI**: `http://localhost:5173`
- **FastAPI REST API**: `http://127.0.0.1:8000`
- **Interactive Swagger Docs**: `http://127.0.0.1:8000/docs`

---

## 🔄 End-to-End System Architecture

```text
 ┌───────────────────────────────────────────────────────────────────────────┐
 │                       REACT FRONTEND (Port 5173)                          │
 │                                                                           │
 │  • Fullscreen / Responsive Grid Layout                                    │
 │  • Top 10 World News Selector (#1 to #10)                                 │
 │  • Settings -> Account (Email & Phone OTP Authentication Modal)          │
 │  • Multilingual & Voice Input Component                                  │
 └────────────────────────────────────┬──────────────────────────────────────┘
                                      │ HTTP / CORS (Credentials: include)
 ┌────────────────────────────────────▼──────────────────────────────────────┐
 │                       FASTAPI BACKEND (Port 8000)                         │
 │                                                                           │
 │  • POST /api/chat          -> Conversational RAG Engine                   │
 │  • GET  /api/news/latest   -> Filtered Real-Time Headlines (#1 to #10)    │
 │  • POST /api/auth/send-otp -> Validate, Rate-limit, Hash & Deliver OTP    │
 │  • POST /api/auth/verify-otp-> Verify Hash, Upsert User, Set HTTP Cookie  │
 │  • GET  /api/auth/me       -> Session Token Validation                    │
 │  • POST /api/voice/chat    -> Speech-to-Text & Text-to-Speech Pipeline    │
 └────────────────────────────────────┬──────────────────────────────────────┘
                                      │ Parameterized SQL & Vector Queries
 ┌────────────────────────────────────▼──────────────────────────────────────┐
 │                      DATABASE & VECTOR ENGINE LAYER                       │
 │                                                                           │
 │  • MySQL 8.0+ : global_news (news, users, otp_verifications, sessions)    │
 │  • ChromaDB   : Persistent vector store (sentence-transformers)           │
 └───────────────────────────────────────────────────────────────────────────┘
```

---

## ⚙️ Environment Variables Configuration (`.env`)

Copy `.env.example` to `.env` and fill in your database and API credentials:

```ini
# MySQL Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_NAME=global_news
DB_USER=root
DB_PASSWORD=your_mysql_password

# LLM & RAG Configuration
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key
LLM_MODEL=gemini-3.6-flash
RAG_TOP_K=5
SIMILARITY_THRESHOLD=0.35

# Session Security
SESSION_SECRET=your_super_secret_session_key

# (Optional) Email OTP Delivery - Leave empty for Dev Logger
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM_EMAIL=noreply@newsai.com

# (Optional) Phone SMS OTP Delivery - Leave empty for Dev Logger
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+1234567890
```

---

## 🗄️ Database Setup & Migrations

To set up the MySQL database schema and authentication tables:

```bash
# 1. Main News Database Schema
mysql -u root -p < database/schema.sql

# 2. Authentication & User Session Schema
python -c "from src.database import get_connection; conn = get_connection(); cursor = conn.cursor(); [cursor.execute(s) for s in open('database/auth_schema.sql').read().split(';') if s.strip()]; conn.commit(); conn.close()"
```

---

## 🧪 Testing

Run the automated test suite for authentication, RAG pipeline, and continuous ingestion:

```bash
# Run Authentication Unit & Integration Tests
python tests/test_auth.py

# Run Full Test Suite
python -m unittest discover tests
```

---

## 📁 Repository Structure

```text
NEWS-AI/
├── config/
│   └── feeds.py            # RSS Feed Sources Configuration
├── database/
│   ├── schema.sql          # Main News Table Schema
│   └── auth_schema.sql     # Auth, Users, Sessions & Bookmarks Schema
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── AuthModal.jsx        # 6-Digit OTP Verification Modal
│   │   │   ├── Header.jsx           # Fullscreen Toggle & Header
│   │   │   ├── HeroWelcome.jsx      # Welcome Banner Component
│   │   │   ├── TopHeadlineCard.jsx  # Top 10 World News Rankings
│   │   │   ├── CategoryPills.jsx    # News Category Pills
│   │   │   ├── ChatSection.jsx      # Chat & Source Cards
│   │   │   ├── BottomNav.jsx        # Navigation Bar
│   │   │   └── Modals.jsx           # History, Saved & Settings Modals
│   │   ├── services/
│   │   │   └── api.js               # REST Client with Cookie Credentials
│   │   ├── App.jsx                  # Main Application Component
│   │   ├── App.css                  # Design Tokens & Styles
│   │   └── index.css                # Global Theme Token Variables
│   └── vite.config.js               # Vite Development Server Config
├── src/
│   ├── api/
│   │   ├── app.py          # FastAPI Application Header & Middleware
│   │   ├── routes_chat.py  # Conversational REST Endpoints
│   │   ├── routes_news.py  # Top 10 & Category News Endpoints
│   │   ├── routes_auth.py  # OTP Auth & User Bookmarks Endpoints
│   │   └── routes_voice.py # Voice Chat API Endpoint
│   ├── auth.py             # OTP Generation, Hashing & Session Core
│   ├── database.py         # MySQL Database Connection & Query Runner
│   ├── news_repository.py  # MySQL News Queries
│   ├── rag_pipeline.py     # Grounded Conversational RAG Pipeline
│   ├── retriever.py        # Hybrid Vector Retrieval & Reranking
│   ├── embeddings.py       # Sentence Transformers Vector Generator
│   ├── scheduler.py        # Near-Real-Time Ingestion Scheduler
│   └── chat.py             # Terminal CLI Assistant
├── tests/
│   └── test_auth.py        # OTP Auth Test Suite
├── .env.example            # Environment Template
├── run_app.py              # Full-System Launcher Script
├── requirements.txt        # Python Dependencies
└── README.md               # Project Documentation
```

---

## 📌 Project Status Roadmap

- [x] **Phase 1: RSS News Collection** *(Completed ✅)*
- [x] **Phase 2: MySQL Database & Storage** *(Completed ✅)*
- [x] **Phase 3: News Processing & Enrichment** *(Completed ✅)*
- [x] **Phase 4: Embeddings & Vector Database** *(Completed ✅)*
- [x] **Phase 5: Grounded RAG + LLM Engine** *(Completed ✅)*
- [x] **Phase 6: Conversational Global News Assistant** *(Completed ✅)*
- [x] **Phase 7: Multilingual Intelligence (English / Hindi / Hinglish)** *(Completed ✅)*
- [x] **Phase 8: Voice Interaction (Speech-to-Text & Text-to-Speech)** *(Completed ✅)*
- [x] **Phase 9: Near-Real-Time Continuous Ingestion & Widescreen UI** *(Completed ✅)*
- [x] **Phase 10: Secure OTP Authentication & User Session Management** *(Completed ✅)*

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.
