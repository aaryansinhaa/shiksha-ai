import json
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.database import get_async_db
from app.models import Protocol
from app.schemas.protocol import ProtocolCreate, ProtocolUpdate, ProtocolResponse

router = APIRouter(prefix="/protocols", tags=["Protocols"])

ELABORATE_SRL_PROTOCOL = {
    "name": "zimmerman_14_taxon_srl_protocol",
    "title": "Zimmerman 14-Taxon Comprehensive Self-Regulated Learning Protocol",
    "version": "2.5.0",
    "languages": ["en", "hi"],
    "description": "Comprehensive diagnostic protocol for evaluating 14 Self-Regulated Learning (SRL) strategies across 6 contextual study scenarios.",
    "taxonomy": [
        {"code": "001-001", "name": "Self-Evaluation", "phase": "Forethought / Reflection", "category": "Evaluation", "description": "Evaluating one's own progress, self-testing, checking work accuracy"},
        {"code": "002-001", "name": "Organizing & Transforming", "phase": "Performance", "category": "Task Strategy", "description": "Creating outlines, mind maps, concept diagrams, summarizing text"},
        {"code": "003-001", "name": "Goal Setting & Planning", "phase": "Forethought", "category": "Planning", "description": "Setting targets, scheduling study sessions, creating timetables"},
        {"code": "004-001", "name": "Seeking Information", "phase": "Performance", "category": "Information", "description": "Searching library, internet, academic journals, extra reference material"},
        {"code": "005-001", "name": "Keeping Records & Monitoring", "phase": "Performance", "category": "Monitoring", "description": "Tracking exam scores, maintaining study logs, recording mistakes"},
        {"code": "006-001", "name": "Environmental Structuring", "phase": "Performance", "category": "Environment", "description": "Selecting quiet study space, turning off phone, eliminating distractions"},
        {"code": "007-001", "name": "Self-Consequences", "phase": "Performance", "category": "Motivation", "description": "Self-rewarding after targets, self-punishment or incentive control"},
        {"code": "008-001", "name": "Rehearsing & Memorizing", "phase": "Performance", "category": "Memorization", "description": "Flashcards, repetition, active recall, practicing formulas"},
        {"code": "009-001", "name": "Seeking Social Assistance (Peers)", "phase": "Performance", "category": "Social Help", "description": "Studying in peer groups, asking classmates for clarification"},
        {"code": "009-002", "name": "Seeking Social Assistance (Teachers)", "phase": "Performance", "category": "Social Help", "description": "Asking professor, tutor, instructor, or TA for guidance"},
        {"code": "010-001", "name": "Reviewing Records (Notes)", "phase": "Reflection", "category": "Review", "description": "Re-reading lecture notes, reviewing class materials"},
        {"code": "010-002", "name": "Reviewing Records (Tests)", "phase": "Reflection", "category": "Review", "description": "Analyzing graded exams, practicing past question papers"},
        {"code": "010-003", "name": "Reviewing Records (Textbooks)", "phase": "Reflection", "category": "Review", "description": "Re-reading textbook chapters, reviewing annotated readings"},
        {"code": "000-000", "name": "Other / Non-SRL", "phase": "General", "category": "General", "description": "General non-strategic study comments or casual responses"}
    ],
    "scenarios": [
        {
            "id": 1,
            "title_en": "Classroom Exam & Test Preparation",
            "title_hi": "कक्षा परीक्षा एवं टेस्ट की तैयारी",
            "prompt_en": "When preparing for a classroom exam or major test, what specific study strategies, techniques, or tools do you use?",
            "prompt_hi": "जब आप कक्षा परीक्षा या मुख्य टेस्ट की तैयारी करते हैं, तो आप किन विशिष्ट अध्ययन रणनीतियों, तकनीकों या उपकरणों का उपयोग करते हैं?"
        },
        {
            "id": 2,
            "title_en": "Writing Essays & Term Papers",
            "title_hi": "निबंध एवं टर्म पेपर लिखना",
            "prompt_en": "When writing an essay, term paper, or research assignment, how do you plan, organize, and execute your writing process?",
            "prompt_hi": "जब आप निबंध, टर्म पेपर या शोध असाइनमेंट लिखते हैं, तो आप अपनी लेखन प्रक्रिया की योजना, संगठन और निष्पादित कैसे करते हैं?"
        },
        {
            "id": 3,
            "title_en": "Solving Mathematics & Science Problems",
            "title_hi": "गणित और विज्ञान के प्रश्नों को हल करना",
            "prompt_en": "When working through complex mathematics, physics, or problem-solving assignments, what methods do you use to overcome difficulties?",
            "prompt_hi": "जब आप जटिल गणित, भौतिकी या समस्या-समाधान असाइनमेंट पर काम करते हैं, तो कठिनाइयों को दूर करने के लिए आप किन तरीकों का उपयोग करते हैं?"
        },
        {
            "id": 4,
            "title_en": "Reading Difficult Textbooks & Chapters",
            "title_hi": "कठिन पाठ्यपुस्तकों एवं अध्यायों को पढ़ना",
            "prompt_en": "When reading dense, technical textbook chapters or academic literature, how do you ensure comprehension and retain key concepts?",
            "prompt_hi": "जब आप कठिन तकनीकी पाठ्यपुस्तक के अध्यायों या अकादमिक साहित्य को पढ़ते हैं, तो आप समझ और मुख्य अवधारणाओं को याद रखना कैसे सुनिश्चित करते हैं?"
        },
        {
            "id": 5,
            "title_en": "Completing Assignments Under Low Motivation",
            "title_hi": "कम प्रेरणा की स्थिति में असाइनमेंट पूरा करना",
            "prompt_en": "When you feel unmotivated, tired, or uninterested in a required study task, what strategies do you use to stay focused and complete it?",
            "prompt_hi": "जब आप किसी आवश्यक अध्ययन कार्य में कम प्रेरित या थका हुआ महसूस करते हैं, तो ध्यान केंद्रित रखने और इसे पूरा करने के लिए आप किन रणनीतियों का उपयोग करते हैं?"
        },
        {
            "id": 6,
            "title_en": "Studying at Home Under Distractions",
            "title_hi": "घर पर विकर्षणों के बीच पढ़ाई करना",
            "prompt_en": "When studying at home with noise, digital notifications, or family distractions present, how do you structure your environment to focus?",
            "prompt_hi": "जब आप घर पर शोर, डिजिटल नोटिफिकेशन या पारिवारिक विकर्षणों के बीच पढ़ाई करते हैं, तो ध्यान केंद्रित करने के लिए आप अपने वातावरण को कैसे व्यवस्थित करते हैं?"
        }
    ],
    "probing_rules": {
        "max_probe_attempts": 2,
        "trigger_conditions": ["RAG match is 000-000", "Ambiguous or short strategy description"],
        "prompt_en": "Could you elaborate a bit more on what specific study techniques, actions, or tools you use in this scenario?",
        "prompt_hi": "क्या आप थोड़ा और विस्तार से बता सकते हैं कि इस स्थिति में आप कौन-कौन सी विशिष्ट तकनीकों का उपयोग करते हैं?"
    },
    "rating_scale": {
        "min": 1,
        "max": 5,
        "labels": {
            "1": {"en": "Seldom / Rarely", "hi": "कभी-कभार"},
            "2": {"en": "Occasionally", "hi": "कभी-कभी"},
            "3": {"en": "Sometimes", "hi": "मध्यम / आधा समय"},
            "4": {"en": "Frequently", "hi": "अक्सर"},
            "5": {"en": "Always / Consistently", "hi": "हमेशा / लगातार"}
        }
    },
    "scoring_metrics": [
        {"metric": "SU", "name": "Strategy Use", "formula": "Binary indicator (1 if used, 0 if not)", "interpretation": "Breadth of active strategy deployment"},
        {"metric": "SF", "name": "Strategy Frequency", "formula": "Total scenario occurrences count", "interpretation": "Volume of strategy application across contexts"},
        {"metric": "SC", "name": "Strategy Consistency", "formula": "Sum of Likert ratings (1-5)", "interpretation": "Total intensity score for each strategy"},
        {"metric": "RC", "name": "Relative Consistency", "formula": "SC / SF", "interpretation": "Average reliance per deployed strategy (Scale 1.0 to 5.0)"}
    ]
}

DEFAULT_PROTOCOL = ELABORATE_SRL_PROTOCOL

async def _ensure_default_protocol(db: AsyncSession):
    res_elab = await db.execute(select(Protocol).where(Protocol.name == "zimmerman_14_taxon_srl_protocol"))
    if not res_elab.scalar_one_or_none():
        db.add(Protocol(
            name=ELABORATE_SRL_PROTOCOL["name"],
            title=ELABORATE_SRL_PROTOCOL["title"],
            languages=ELABORATE_SRL_PROTOCOL["languages"],
            steps=ELABORATE_SRL_PROTOCOL
        ))
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
