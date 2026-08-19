import os
import logging
import httpx
import numpy as np
from typing import List, Dict, Any, Optional
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import StrategyEmbedding

logger = logging.getLogger("ShikshaAI.rag")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

async def get_embedding(text_input: str) -> Optional[List[float]]:
    """Get 768-dim float vector embedding via Gemini text-embedding-004 API."""
    if not GEMINI_API_KEY or not text_input.strip():
        # Fallback to deterministic pseudo-embedding for testing/mocking
        return _generate_mock_embedding(text_input)

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={GEMINI_API_KEY}"
        payload = {
            "model": "models/text-embedding-004",
            "content": {
                "parts": [{"text": text_input}]
            }
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            embedding_vals = data.get("embedding", {}).get("values", [])
            if len(embedding_vals) == 768:
                return embedding_vals
            return _generate_mock_embedding(text_input)
    except Exception as e:
        logger.error(f"Failed to fetch Gemini embedding: {e}")
        return _generate_mock_embedding(text_input)

def _generate_mock_embedding(text_input: str) -> List[float]:
    """Generates normalized 768-dim mock vector derived from text hash for local RAG."""
    seed = sum(ord(c) for c in text_input)
    np.random.seed(seed % 2**32)
    vec = np.random.randn(768).astype(np.float32)
    norm = np.linalg.norm(vec)
    return (vec / norm).tolist()

async def match_strategy_rag(
    db: AsyncSession,
    user_text: str,
    top_k: int = 3
) -> List[Dict[str, Any]]:
    """Retrieve top-k matching strategy codes using pgvector distance."""
    query_vec = await get_embedding(user_text)
    if not query_vec:
        return []

    try:
        # Use pgvector Cosine distance operator (<=>)
        query_sql = text("""
            SELECT strategy_id, name, phase, category, content, (embedding <=> :vec) as distance
            FROM strategy_embedding
            ORDER BY embedding <=> :vec
            LIMIT :k
        """)
        result = await db.execute(query_sql, {"vec": str(query_vec), "k": top_k})
        rows = result.fetchall()
        
        matches = []
        for r in rows:
            matches.append({
                "strategy_id": r[0],
                "name": r[1],
                "phase": r[2],
                "category": r[3],
                "content": r[4]
            })
        return matches
    except Exception as e:
        logger.warning(f"pgvector query fallback: {e}")
        # Fallback to direct text matching against known strategies
        return _fallback_keyword_strategy_match(user_text)

def _fallback_keyword_strategy_match(text_input: str) -> List[Dict[str, Any]]:
    text_lower = text_input.lower()
    if any(k in text_lower for k in ["repeat", "flashcard", "doohra", "पुनरावृत्ति", "याद", "practice"]):
        return [{"strategy_id": "008-001", "name": "Rehearsing & Memorizing"}]
    elif any(k in text_lower for k in ["notes", "map", "mindmap", "नोट्स", "माइंड मैप", "outline", "summary", "summaries"]):
        return [{"strategy_id": "002-001", "name": "Organizing & Transforming"}]
    elif any(k in text_lower for k in ["timetable", "schedule", "goal", "लक्ष्य", "टाइमटेबल", "plan"]):
        return [{"strategy_id": "003-001", "name": "Goal Setting & Planning"}]
    elif any(k in text_lower for k in ["friend", "group", "peer", "मित्र", "दोस्त"]):
        return [{"strategy_id": "009-001", "name": "Seeking Social Assistance (Peers)"}]
    elif any(k in text_lower for k in ["quiet", "distraction", "शांत", "फोन"]):
        return [{"strategy_id": "006-001", "name": "Environmental Structuring"}]
    elif any(k in text_lower for k in ["paper", "test", "exam", "question", "quiz"]):
        return [{"strategy_id": "010-002", "name": "Reviewing Records (Tests)"}]
    return [{"strategy_id": "000-000", "name": "Other / Non-SRL"}]
