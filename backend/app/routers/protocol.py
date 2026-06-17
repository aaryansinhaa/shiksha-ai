from fastapi import APIRouter
from typing import List, Dict, Any

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

@router.get("")
async def list_protocols():
    return [DEFAULT_PROTOCOL]

@router.get("/{name}")
async def get_protocol(name: str):
    return DEFAULT_PROTOCOL
