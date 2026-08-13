import json
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.database import get_async_db
from app.models import Protocol
from app.schemas.protocol import ProtocolCreate, ProtocolUpdate, ProtocolResponse

router = APIRouter(prefix="/protocols", tags=["Protocols"])

DEFAULT_PROTOCOL = {
    "name": "interview_default",
    "title": "Shiksha AI Standard SRL Protocol",
    "languages": ["en", "hi"],
    "steps": [
        {"id": "intro", "type": "scenario", "question_en": "What subject are you studying?", "question_hi": "आप किस विषय की पढ़ाई कर रहे हैं?"},
        {"id": "strategy", "type": "open_question", "question_en": "How do you prepare for a difficult exam?", "question_hi": "आप किसी कठिन परीक्षा की तैयारी कैसे करते हैं?"},
        {"id": "frequency", "type": "likert_rating", "min": 1, "max": 5},
        {"id": "complete", "type": "feedback_summary"}
    ]
}

async def _ensure_default_protocol(db: AsyncSession):
    res = await db.execute(select(Protocol).where(Protocol.name == "interview_default"))
    existing = res.scalar_one_or_none()
    if not existing:
        proto = Protocol(
            name=DEFAULT_PROTOCOL["name"],
            title=DEFAULT_PROTOCOL["title"],
            languages=DEFAULT_PROTOCOL["languages"],
            steps=DEFAULT_PROTOCOL["steps"]
        )
        db.add(proto)
        await db.commit()

@router.get("", response_model=List[ProtocolResponse])
async def list_protocols(db: AsyncSession = Depends(get_async_db)):
    await _ensure_default_protocol(db)
    res = await db.execute(select(Protocol).order_by(Protocol.id))
    protos = res.scalars().all()
    out = []
    for p in protos:
        out.append(ProtocolResponse(
            name=p.name,
            title=p.title,
            languages=p.languages if isinstance(p.languages, list) else ["en", "hi"],
            steps=p.steps
        ))
    return out

@router.get("/{name}", response_model=ProtocolResponse)
async def get_protocol(name: str, db: AsyncSession = Depends(get_async_db)):
    await _ensure_default_protocol(db)
    res = await db.execute(select(Protocol).where(Protocol.name == name))
    proto = res.scalar_one_or_none()
    if not proto:
        raise HTTPException(status_code=404, detail=f"Protocol '{name}' not found")
    return ProtocolResponse(
        name=proto.name,
        title=proto.title,
        languages=proto.languages if isinstance(proto.languages, list) else ["en", "hi"],
        steps=proto.steps
    )

@router.post("", response_model=ProtocolResponse, status_code=status.HTTP_201_CREATED)
async def create_protocol(payload: ProtocolCreate, db: AsyncSession = Depends(get_async_db)):
    res = await db.execute(select(Protocol).where(Protocol.name == payload.name))
    if res.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"Protocol '{payload.name}' already exists")
    
    proto = Protocol(
        name=payload.name,
        title=payload.title,
        languages=payload.languages,
        steps=payload.steps
    )
    db.add(proto)
    await db.commit()
    return ProtocolResponse(
        name=proto.name,
        title=proto.title,
        languages=proto.languages,
        steps=proto.steps
    )

@router.put("/{name}", response_model=ProtocolResponse)
async def update_protocol(name: str, payload: ProtocolUpdate, db: AsyncSession = Depends(get_async_db)):
    res = await db.execute(select(Protocol).where(Protocol.name == name))
    proto = res.scalar_one_or_none()
    if not proto:
        raise HTTPException(status_code=404, detail=f"Protocol '{name}' not found")
    
    if payload.title is not None:
        proto.title = payload.title
    if payload.languages is not None:
        proto.languages = payload.languages
    if payload.steps is not None:
        proto.steps = payload.steps
    
    await db.commit()
    return ProtocolResponse(
        name=proto.name,
        title=proto.title,
        languages=proto.languages,
        steps=proto.steps
    )

@router.delete("/{name}")
async def delete_protocol(name: str, db: AsyncSession = Depends(get_async_db)):
    res = await db.execute(select(Protocol).where(Protocol.name == name))
    proto = res.scalar_one_or_none()
    if not proto:
        raise HTTPException(status_code=404, detail=f"Protocol '{name}' not found")
    
    await db.delete(proto)
    await db.commit()
    return {"status": "deleted", "name": name}

@router.get("/{name}/export")
async def export_protocol(name: str, db: AsyncSession = Depends(get_async_db)):
    res = await db.execute(select(Protocol).where(Protocol.name == name))
    proto = res.scalar_one_or_none()
    if not proto:
        raise HTTPException(status_code=404, detail=f"Protocol '{name}' not found")
    
    data = {
        "name": proto.name,
        "title": proto.title,
        "languages": proto.languages,
        "steps": proto.steps
    }
    content = json.dumps(data, indent=2)
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{name}_protocol.json"'}
    )

@router.post("/import")
async def import_protocol(
    request: Request,
    file: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_async_db)
):
    data = None
    if file:
        content = await file.read()
        try:
            data = json.loads(content.decode("utf-8"))
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON file format")
    else:
        try:
            data = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="Provide either a file upload or JSON body payload")
    
    if not data or not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="Invalid protocol JSON structure")

    name = data.get("name")
    title = data.get("title", f"Imported Protocol - {name}")
    languages = data.get("languages", ["en", "hi"])
    steps = data.get("steps", [])
    
    if not name:
        raise HTTPException(status_code=400, detail="Protocol JSON must specify a 'name' field")

    res = await db.execute(select(Protocol).where(Protocol.name == name))
    proto = res.scalar_one_or_none()
    if proto:
        proto.title = title
        proto.languages = languages
        proto.steps = steps
    else:
        proto = Protocol(name=name, title=title, languages=languages, steps=steps)
        db.add(proto)
    
    await db.commit()
    return {"status": "imported", "name": name, "title": title}
