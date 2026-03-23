# 🛍️ E-Commerce AI Assistant

<div align="center">

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=for-the-badge&logo=flask&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![Google Gemini](https://img.shields.io/badge/Gemini_2.5_Flash-4285F4?style=for-the-badge&logo=google&logoColor=white)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)

![FAISS](https://img.shields.io/badge/FAISS-Vector_Search-blue?style=for-the-badge)
![BM25](https://img.shields.io/badge/BM25-Keyword_Search-green?style=for-the-badge)
![SentenceTransformers](https://img.shields.io/badge/SentenceTransformers-all--MiniLM--L6--v2-orange?style=for-the-badge)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-013243?style=for-the-badge&logo=numpy&logoColor=white)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
![Status](https://img.shields.io/badge/Status-Active-success?style=for-the-badge)

</div>

---

<div align="center">
  <h3>An intelligent full-stack e-commerce platform powered by Hybrid Search (BM25 + FAISS) and Google Gemini AI with live streaming responses.</h3>
</div>

---

## 📌 Table of Contents

- [Overview](#-overview)
- [Live Demo](#-live-demo)
- [Tech Stack](#-tech-stack)
- [Features](#-features)
- [Project Structure](#-project-structure)
- [Database Schema](#-database-schema)
- [How It Works](#-how-it-works)


---

## 🔍 Overview

**E-Commerce AI Assistant** is a full-stack NLP project that transforms a raw Amazon product dataset into an intelligent shopping assistant. It combines:

- **BM25** for fast lexical keyword search
- **FAISS** with sentence embeddings for semantic vector search
- **Google Gemini 2.5 Flash** for AI-powered recommendations with **live streaming** (like ChatGPT)
- **Flask** backend with session-based authentication
- **Vanilla JS SPA** frontend with animated dark UI

> Originally built as an NLP Jupyter Notebook project, now evolved into a production-ready full-stack web application.

---

## 🚀 Live Demo

```
http://localhost:5000
```

Run locally following the [Installation](#-installation) steps below.

---

## 🛠️ Tech Stack

### Backend
| Technology | Purpose |
|---|---|
| ![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white) **Python 3.9+** | Core language |
| ![Flask](https://img.shields.io/badge/Flask-000000?logo=flask&logoColor=white) **Flask 3.0** | Web framework & REST API |
| ![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?logo=sqlalchemy&logoColor=white) **Flask-SQLAlchemy** | ORM & database management |
| ![SQLite](https://img.shields.io/badge/SQLite-003B57?logo=sqlite&logoColor=white) **SQLite** | Lightweight relational database |

### NLP / AI
| Technology | Purpose |
|---|---|
| 🤖 **Google Gemini 2.5 Flash** | LLM for recommendations + live SSE streaming |
| 🔢 **SentenceTransformers** (`all-MiniLM-L6-v2`) | Text embeddings for semantic search |
| ⚡ **FAISS** (Facebook AI) | Fast vector similarity search |
| 📝 **BM25Okapi** | Classical keyword-based ranking |
| 🐼 **Pandas + NumPy** | Data loading, cleaning & processing |

### Frontend
| Technology | Purpose |
|---|---|
| ![HTML5](https://img.shields.io/badge/HTML5-E34F26?logo=html5&logoColor=white) **HTML5** | Semantic markup, SPA structure |
| ![CSS3](https://img.shields.io/badge/CSS3-1572B6?logo=css3&logoColor=white) **CSS3** | Animated dark theme, responsive design |
| ![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?logo=javascript&logoColor=black) **Vanilla JS** | SPA routing, SSE streaming, API calls |
| 🔤 **Inter (Google Fonts)** | Typography |

---

## ✨ Features

### 🔐 Authentication
- Register with name, email, password (SHA-256 hashed)
- Session-based login with fixed secret key
- Protected routes for recommendations & history
- Auto-redirect on session expiry

### 📦 Products Page
- Browse **1,465+ real Amazon products** in a responsive grid
- **Sidebar filters** — Category, Price range, Minimum rating
- **Sorting** — Best rated, Price (low/high), Biggest discount
- Smart **pagination** with page range
- Product cards with **image, rating, price, discount badge**
- **Product modal** with full details + direct Buy on Amazon link
- **"Ask AI"** button on every card → pre-fills AI chat

### 🤖 AI Recommendations (Login Required)
- ChatGPT-style **live streaming** responses via Server-Sent Events (SSE)
- Hybrid retrieval: **BM25 + FAISS** to find top-5 relevant products
- Products appear instantly while AI streams its response
- Suggestion chips for quick queries
- Blinking cursor animation while streaming

### 📋 Chat History (Login Required)
- Every query, AI response & retrieved products saved to SQLite
- Collapsible conversation cards with product thumbnails
- Delete individual or clear all history
- Standalone `/chat-history` viewer page with stats & search
- Pagination for large history

### 🔍 Search
- Global search bar in navbar (press Enter)
- Hybrid BM25 + FAISS search across all 1,465 products

### 🎨 UI / UX
- Deep dark theme with animated gradient background
- Floating particle effects
- Animated navbar with gradient underline
- Page entrance animations
- Fully responsive (mobile, tablet, desktop)

---

## 🏗️ Project Structure

```
ecommerce-ai-assistant/
│
├── app.py                  ← Flask app, all API routes, SSE streaming
├── recommender.py          ← NLP engine: BM25 + FAISS + Gemini
├── database.py             ← SQLAlchemy models: User, ChatHistory
├── requirements.txt        ← Python dependencies
├── setup.sh                ← One-click setup script (Linux/Mac)
├── README.md               ← This file
│
├── templates/
│   ├── index.html          ← Main SPA (6 pages in one file)
│   └── chat_history.html   ← Standalone history viewer
│
└── static/
    ├── css/
    │   └── style.css       ← Full design system (dark theme + animations)
    └── js/
        └── main.js         ← SPA router, streaming, products, auth
```

## 🗃️ Database Schema

### `users` table
| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PK | Auto increment |
| `name` | VARCHAR(120) | Full name |
| `email` | VARCHAR(200) UNIQUE | Login email |
| `password_hash` | VARCHAR(256) | SHA-256 hashed |
| `created_at` | DATETIME | UTC timestamp |

### `chat_history` table
| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PK | Auto increment |
| `user_id` | INTEGER FK | References users.id |
| `query` | TEXT | User's question |
| `ai_response` | TEXT | Full Gemini response |
| `products_json` | TEXT | JSON array of retrieved products |
| `created_at` | DATETIME | UTC timestamp |

---

## 🧠 How It Works

```
User Query
    │
    ├─► BM25 Keyword Search  ──────────────────┐
    │   (rank_bm25 library)                    │
    │                                          ├──► Hybrid Score ──► Top 5 Products
    ├─► FAISS Vector Search ───────────────────┘
    │   (all-MiniLM-L6-v2 embeddings)
    │
    ├─► Products sent to frontend immediately  (SSE: event: products)
    │
    └─► Gemini 2.5 Flash streams response      (SSE: event: chunk × N)
            │
            └─► Saved to SQLite on completion  (SSE: event: done)
```

### Hybrid Scoring Formula
```python
final_score = 0.6 × faiss_similarity + 0.4 × bm25_normalized
```
---

## 👨‍💻 Author

<!-- Built with ❤️ as a full-stack NLP project — from Jupyter Notebook to production web app. -->
Rushindra K
---

<div align="center">

⭐ **Star this repo if you found it helpful!** ⭐

</div>
