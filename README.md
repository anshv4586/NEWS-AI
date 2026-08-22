# 🌍 Global News AI

Global News AI is a multi-phase project designed to build an intelligent, conversational news assistant. Users can interact via **Text or Voice** in **English, Hindi, or Hinglish** to receive concise, accurate, and up-to-date news powered by reliable sources, Retrieval-Augmented Generation (RAG), and LLMs.

---

## 📌 Project Roadmap (10 Phases)

```text
PHASE 1: RSS News Collection [COMPLETED]
        ↓
PHASE 2: News Cleaning + Storage
        ↓
PHASE 3: News Processing + Metadata
        ↓
PHASE 4: Embeddings + Vector Database
        ↓
PHASE 5: Basic RAG
        ↓
PHASE 6: News-specific Retrieval
        ↓
PHASE 7: Multilingual Hindi/English/Hinglish
        ↓
PHASE 8: Conversational Chat Interface
        ↓
PHASE 9: Voice Input + Output
        ↓
PHASE 10: Production + Evaluation
```

---

## 🔄 System Architecture & Workflow

```text
                         🌍 NEWS AI
                             │
                    ┌────────┴────────┐
                    │                 │
                   TEXT              VOICE
                    │                 │
                    │          Speech-to-Text
                    │                 │
                    └────────┬────────┘
                             ↓
                      Query Understanding
                             ↓
                 ┌───────────┴───────────┐
                 │                       │
          Conversation              Language
             Context              Hindi/English/
                                   Hinglish
                 │                       │
                 └───────────┬───────────┘
                             ↓
                    News Retrieval Engine
                             ↓
             ┌───────────────┼───────────────┐
             ↓               ↓               ↓
        Vector Search   Keyword Search   Metadata
             │               │               │
             └───────────────┼───────────────┘
                             ↓
                         Reranking
                             ↓
                      Event Clustering
                             ↓
                    Relevant News Evidence
                             ↓
                            LLM
                             ↓
                ┌────────────┼────────────┐
                ↓            ↓            ↓
             Answer       Sources      Timestamp
                │
                ↓
          Text / Voice Output
```

---

## 📦 Phase 1: RSS News Collection Overview

Phase 1 provides an automated, fault-tolerant ingestion pipeline that downloads, cleans, deduplicates, and saves RSS news articles from global publishers.

### 🏗️ Project Architecture

```text
d:/news project/
├── config/
│   └── feeds.py           # RSS source URLs categorized by topic & publisher
├── src/
│   ├── __init__.py        # Package marker
│   ├── rss_collector.py   # RSS parser & raw dictionary extractor
│   ├── cleaner.py         # HTML tag stripper, date ISO normalizer & deduplicator
│   ├── storage.py         # Automatic CSV & JSON dataset generator
│   └── main.py            # Main pipeline coordinator
├── data/
│   ├── news.csv           # Tabular export dataset
│   └── news.json          # Formatted JSON array dataset
├── tests/
│   └── test_pipeline.py   # Unit test suite (6 passing tests)
├── requirements.txt       # Dependencies (feedparser, pandas, bs4, python-dateutil)
├── .gitignore             # Python & environment ignore file
└── README.md              # Project documentation
```

### ⚡ Quick Start (Phase 1)

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run News Ingestion Pipeline:**
   ```bash
   python -m src.main
   ```

3. **Run Unit Test Suite:**
   ```bash
   python -m unittest discover tests
   ```

---

## 🚀 Status Tracker

- [x] **Phase 1: RSS News Collection** *(Completed ✅)*
- [ ] **Phase 2: News Cleaning + Storage**
- [ ] **Phase 3: News Processing + Metadata**
- [ ] **Phase 4: Embeddings + Vector Database**
- [ ] **Phase 5: Basic RAG**
- [ ] **Phase 6: News-specific Retrieval**
- [ ] **Phase 7: Multilingual (Hindi / English / Hinglish)**
- [ ] **Phase 8: Conversational Chat Interface**
- [ ] **Phase 9: Voice Input + Output**
- [ ] **Phase 10: Production & Evaluation**
