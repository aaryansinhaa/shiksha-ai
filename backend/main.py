import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import engine, Base
from app.routers import chat, dashboard, log, protocol, survey

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ShikshaAI")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager creating database tables & seeding taxonomy on startup."""
    logger.info("Initializing Shiksha AI Database Tables & Taxons...")
    try:
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            await conn.run_sync(Base.metadata.create_all)
        
        from app.services.state_machine import seed_languages_and_contexts
        async with AsyncSession(engine) as session:
            await seed_languages_and_contexts(session)
    except Exception as e:
        logger.warning(f"Note on vector extension / table init: {e}")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    logger.info("Shiksha AI Server Startup Complete.")
    yield
    logger.info("Shiksha AI Server Shutdown.")

app = FastAPI(
    title="Shiksha AI - Conversational GenAI & RAG Assessment Platform",
    description="Dual-Language (English & Hindi) AI Platform for Self-Regulated Learning (SRL) Strategy Evaluation",
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(chat.router)
app.include_router(dashboard.router)
app.include_router(log.router)
app.include_router(protocol.router)
app.include_router(survey.router)

# Mount built React static files if frontend build exists
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)
