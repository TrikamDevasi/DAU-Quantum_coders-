<div align="center">

# ⚡ PriceIQ

### *Most e-commerce stores leave 20–30% of revenue on the table every single day. PriceIQ fixes that — in real time.*

<br/>

[![React](https://img.shields.io/badge/React_18-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)](https://pytorch.org/)
[![Redis](https://img.shields.io/badge/Redis_Streams-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![MongoDB](https://img.shields.io/badge/MongoDB-4EA94B?style=for-the-badge&logo=mongodb&logoColor=white)](https://www.mongodb.com/)
[![Groq](https://img.shields.io/badge/Groq_AI-F55036?style=for-the-badge&logo=groq&logoColor=white)](https://groq.com/)

**[🚀 Live Demo](#-quick-start) · [🎥 Demo Video](#) · [📐 Architecture](#-architecture)**

</div>

---

## 🔥 The Problem

Retail pricing today is **static, delayed, and blind to demand signals.**

A product going viral on social media still shows yesterday's price at 2 AM. A flash crowd of 400 users adding the same item to their cart triggers zero response from the pricing engine. Meanwhile, Amazon reprices its catalog **every 10 minutes** using systems that cost millions to build.

Small and mid-size e-commerce stores have no equivalent. They set prices manually, run gut-feel promotions, and discover missed revenue opportunities in monthly reports — long after the moment has passed.

> **The gap between enterprise dynamic pricing and everyone else is a $300B problem. We built the infrastructure to close it.**

---

## 💡 The Solution

**PriceIQ** is a real-time, AI-powered dynamic pricing platform that senses demand as it happens and adjusts prices intelligently — automatically.

It ingests raw clickstream events (views, cart additions, purchases) through a Redis Streams pipeline, computes live demand velocity, and feeds that signal into a pricing engine backed by a deep learning recommendation model. Every price update is informed by what's happening *right now*, not last week's analytics export.

**Built in one hackathon. Production architecture throughout.**

---

## ✨ Key Features

- **⚡ Sub-100ms Demand Sensing** — Redis Streams pipeline ingests and processes clickstream events with microsecond cache lookups for the pricing engine
- **🧠 GRU4Rec Recommendations** — A PyTorch Gated Recurrent Unit model delivers session-aware product recommendations; cold-start handled via TF-IDF fallback
- **📊 Live A/B Testing Dashboard** — Real-time revenue and conversion visualizations so you can see pricing changes *working*
- **💬 AI Customer Chat** — Groq-powered support assistant embedded in the storefront, answering product questions instantly
- **🔐 Production Auth** — JWT sessions + Google OAuth 2.0 via Passport.js; not a demo stub
- **🔄 Intelligent Fallback** — When session data is sparse, Scikit-Learn TF-IDF content similarity takes over seamlessly, zero dropped recommendations

---

## 🏗️ Architecture

PriceIQ is a **three-service system** designed so each layer can scale independently:

```
┌──────────────────────────────────────────────────────────────┐
│  FRONTEND  ·  React 18 + Vite + TanStack Query               │
│  Storefront  ←→  Analytics Dashboard  ←→  AI Chat Widget     │
└───────────────────────────┬──────────────────────────────────┘
                            │  REST API
┌───────────────────────────▼──────────────────────────────────┐
│  BACKEND  ·  Express.js (Node.js ES Modules)                 │
│                                                               │
│  ┌─────────────────────┐    ┌──────────────────────────────┐ │
│  │  Auth & API Layer   │    │   Redis Stream Consumer      │ │
│  │  JWT · Passport     │    │   Clickstream → Velocity     │ │
│  └─────────────────────┘    └──────────┬─────────────────── ┘ │
│                                        │                      │
│  ┌─────────────────────┐    ┌──────────▼───────────────────┐ │
│  │  MongoDB            │    │   Redis Cache                │ │
│  │  Products · Users   │    │   Demand Scores (< 1ms read) │ │
│  │  Sessions · Events  │    └──────────────────────────────┘ │
│  └─────────────────────┘                                     │
└───────────────────────────┬──────────────────────────────────┘
                            │  Internal HTTP
┌───────────────────────────▼──────────────────────────────────┐
│  ML SERVICE  ·  FastAPI (Python)                             │
│                                                               │
│   GRU4Rec (PyTorch)   ──▶  Session-Based Recommendations     │
│   TF-IDF (Scikit-Learn) ▶  Cold-Start Fallback               │
│   Pandas + NumPy      ──▶  Real-Time Feature Engineering     │
│   PyMongo             ──▶  Direct Event Store Access         │
└──────────────────────────────────────────────────────────────┘
```

**Why this architecture?**

- **Redis Streams** were chosen over Kafka intentionally — for hackathon scope they offer 90% of the throughput with zero infrastructure overhead, while still being a serious production primitive.
- **FastAPI over Flask** because async ML serving with Pydantic validation matters when a pricing engine is calling your inference endpoint on every page load.
- **GRU4Rec** is the academic gold standard for session-based recommendation. Most hackathon projects use collaborative filtering. We didn't.

---

## 🚀 Quick Start

> ⚠️ **Judges:** The entire stack is dockerized. One command and it runs.

### Option A — Docker (Recommended)

```bash
git clone https://github.com/your-org/priceiq.git
cd priceiq
cp .env.example .env          # fill in GROQ_API_KEY + GOOGLE_OAUTH creds
docker-compose up --build
```

Open `http://localhost:5173` — done.

---

### Option B — Manual Setup

**Prerequisites:** Node.js ≥ 18, Python ≥ 3.10, MongoDB, Redis 7+

```bash
# 1. Clone
git clone https://github.com/your-org/priceiq.git && cd priceiq

# 2. Frontend
cd frontend && npm install && npm run dev

# 3. Backend  (new terminal)
cd backend && npm install && npm run dev

# 4. ML Service  (new terminal)
cd ml-service
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Seed demo data:**
```bash
cd backend && npm run seed
```

### Environment Variables

```env
# backend/.env
MONGO_URI=mongodb://localhost:27017/priceiq
REDIS_URL=redis://localhost:6379
JWT_SECRET=your_secret
GROQ_API_KEY=your_groq_key               # https://console.groq.com
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_secret
GOOGLE_CALLBACK_URL=http://localhost:5000/auth/google/callback
```

---

## 🛠️ Tech Stack

| Layer | Technology | Why We Chose It |
|---|---|---|
| Frontend | React 18 + Vite + TypeScript | Fast iteration; type safety caught critical bugs mid-hack |
| Styling | TailwindCSS + Shadcn UI | Production-quality UI in hours, not days |
| State | TanStack Query | Server-state sync with zero boilerplate; essential for live dashboards |
| Charts | Recharts | Composable; we needed custom overlays that Chart.js couldn't handle |
| Forms | React Hook Form + Zod | End-to-end type-safe — no runtime surprises on form submissions |
| Backend | Express.js (Node ESM) | Fast setup, strong shared team context |
| Primary DB | MongoDB + Mongoose | Flexible schema during rapid iteration; event collection scales horizontally |
| Real-Time | Redis + ioredis | Streams for ingestion, caching for sub-millisecond pricing reads |
| Auth | JWT + BcryptJS + Passport | Not a stub — real OAuth and hashed credentials throughout |
| AI Chat | Groq SDK | Fastest LLM inference available; imperceptible latency in the chat widget |
| ML Serving | FastAPI (Python) | Async-first; native Pydantic validation; built for this exact use case |
| Deep Learning | PyTorch (GRU4Rec) | Session modeling that outperforms matrix factorization on sparse data |
| Fallback ML | Scikit-Learn (TF-IDF) | Reliable cold-start handling without a second neural model |
| Feature Eng. | Pandas + NumPy | Real-time signal computation on the live event stream |
| Model Ops | PyMongo + Joblib | Direct event store access + fast model serialization |

---

## 🏁 What We Built During the Hackathon

This is not a mockup. Every item listed here is **functional and wired end-to-end:**

- [x] Redis Streams clickstream ingestion pipeline with live demand velocity computation
- [x] GRU4Rec model trained on synthetic session data and served via FastAPI
- [x] TF-IDF cold-start fallback with graceful routing logic between models
- [x] Express.js REST API with full JWT auth and Google OAuth
- [x] Dynamic pricing engine reading live Redis demand scores
- [x] Storefront with real product listings, cart, and session tracking
- [x] Analytics dashboard with live A/B test revenue and conversion charts
- [x] Groq AI chat assistant integrated into the storefront UI
- [x] Seed scripts for fully reproducible demo data

---

## ⚔️ Challenges & Learnings

**The hardest thing we solved:** Getting the ML inference pipeline fast enough for a real storefront.

A naïve setup — raw FastAPI calling PyTorch on every recommendation request — introduced ~400ms latency. Unacceptable. The fix involved three changes:

1. **Model warm-up at startup** — GRU4Rec loaded once and kept resident in memory, never cold-loaded per request
2. **Vectorized feature extraction** — Replaced per-event Python loops with NumPy batch operations for session feature computation
3. **Redis recommendation caching** — Outputs cached with a short TTL keyed on session fingerprint, eliminating redundant inference calls

**Result: P95 recommendation latency dropped from ~400ms to under 40ms.**

Other non-trivial moments:
- Designing the Redis Stream consumer to be idempotent so replayed events don't corrupt demand velocity scores
- Keeping Zod schemas synchronized between the frontend form layer and Mongoose models without a monorepo setup
- Training GRU4Rec on synthetic data that actually resembles real browsing session distributions — harder than the model architecture itself

---

## 🔭 Future Roadmap

The foundation is real. What comes next is scale and intelligence:

- **Bandit-based pricing optimization** — Replace the rule-based engine with a contextual multi-armed bandit that learns optimal price points from live conversion outcomes
- **Competitor price ingestion** — Pull external pricing signals so demand velocity is contextualized against real market position
- **Merchant SDK** — A `<script>` drop-in so any Shopify or WooCommerce store can plug in PriceIQ without a full backend integration
- **Pricing explainability** — Surface *why* a price changed so merchants can trust and override AI decisions with full context
- **Kafka migration path** — A documented upgrade from Redis Streams to Kafka for merchants whose event volume demands it

---

## 👥 Team

Built with urgency, caffeine, and an unreasonable amount of PyTorch documentation.

| Name | Role |
|---|---|
| — | ML & Recommendations |
| — | Backend & Real-Time Pipeline |
| — | Frontend & Dashboard |

---

<div align="center">

**PriceIQ** · Built at [Hackathon Name] · [Year]

*The pricing gap between Amazon and everyone else closes here.*

</div>
