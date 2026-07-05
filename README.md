# Shiksha AI

[![React](https://img.shields.io/badge/React-18.3-61DAFB?logo=react&logoColor=white)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16--pgvector-4169E1?logo=postgresql&logoColor=white)](https://github.com/pgvector/pgvector)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Shiksha AI is an open-source full-stack platform designed for evaluating Self-Regulated Learning (SRL) strategies using adaptive LLM interviews and vector similarity search. The application maps student study behaviors against Zimmerman's 14-taxon psychological model using a hybrid pipeline of LLM inference, PostgreSQL `pgvector` embeddings, and real-time interaction telemetry.

---

## Architecture Overview

```mermaid
graph TD
    User([User Browser]) -->|HTTP :8080| Nginx[Nginx Reverse Proxy]
    Nginx -->|Static Assets| React[React 18 + Vite Frontend]
    Nginx -->|API Requests| FastAPI[FastAPI Backend :5000]

    subgraph Backend Core
        FastAPI --> StateMachine[State Machine Engine]
        StateMachine --> RAG[RAG Vector Matcher]
        StateMachine --> LLMClient[Gemini API Service]
    end

    subgraph Data Layer
        RAG -->|768-dim Vector Distance| DB[(PostgreSQL 16 + pgvector)]
        StateMachine -->|Persist Sessions & Transcripts| DB
    end

    LLMClient -->|HTTPS| Gemini[Google Gemini API]
```

---

## Features

- **Conversational Assessment**: Multi-turn adaptive interviews powered by Gemini Flash API with structured state machine control flow.
- **RAG Strategy Classification**: Semantic similarity search via PostgreSQL `pgvector` and 768-dimensional embeddings (`text-embedding-004`).
- **Dual Language Support**: Native English (`en`) and Hindi (`hi`) prompt templates, UI strings, and strategy taxonomies.
- **Quantitative SRL Scoring**: Computes Strategy Use (SU), Strategy Frequency (SF), Strategy Consistency (SC), and Relative Consistency (RC) metrics based on Zimmerman (1986).
- **Researcher & Telemetry Dashboard**: Roster view of saved student records, raw transcript modal inspector, and 100ms sampled mouse coordinate tracking streams.
- **Teacher Analytics**: Cohort-level metrics and strategy distribution visualization using Recharts.

---

## Tech Stack

| Component | Technology |
| :--- | :--- |
| **Frontend** | React 18, TypeScript, Vite, TailwindCSS, Zustand, Recharts, Lucide React |
| **Backend** | Python 3.11+, FastAPI, Async SQLAlchemy 2.0, Pydantic v2, Uvicorn, Asyncpg |
| **Database & Vector Search** | PostgreSQL 16 with `pgvector` (SQLite `aiosqlite` fallback for testing) |
| **LLM & Embeddings** | Google Gemini API (`gemini-flash-latest`), `text-embedding-004` |
| **Deployment** | Docker Compose, Nginx |

---

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Google Gemini API Key

### 1. Environment Configuration
Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-flash-latest
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres_secure_pass
POSTGRES_DB=shiksha_ai
DATABASE_URL=postgresql+asyncpg://postgres:postgres_secure_pass@postgres:5432/shiksha_ai
DISABLE_LLM=false
```

### 2. Run with Docker Compose

```bash
docker compose -f docker-compose.prod.yml up --build -d
```

- **Application Web UI**: `http://localhost:8080`
- **FastAPI OpenAPI Docs**: `http://localhost:5000/docs`

---

## Local Development Setup

To run the backend and frontend services separately in development mode:

### Backend
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

PYTHONPATH=backend uvicorn backend.main:app --reload --port 5000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## API Reference

| Method | Path | Description |
| :--- | :--- | :--- |
| `POST` | `/startConversation` | Start or reset an interview session for a user |
| `POST` | `/reply` | Process a user message through state machine and RAG matcher |
| `GET` | `/student/evaluations` | Retrieve quantitative SRL scores for a given user |
| `GET` | `/researcher/students` | Fetch saved student records and conversation transcripts |
| `GET` | `/researcher/telemetry` | Fetch mouse traces and activity log entries |
| `GET` | `/dashboard/stats` | Retrieve aggregate cohort metrics for teacher analytics |
| `GET` | `/dashboard/courses` | Retrieve course enrollment breakdowns |

---

## Testing

Run backend tests using pytest:

```bash
PYTHONPATH=backend DATABASE_URL="sqlite+aiosqlite:///:memory:" pytest backend/tests/ -v
```

Verify frontend type checks and production bundle build:

```bash
cd frontend
npm run build
```

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
