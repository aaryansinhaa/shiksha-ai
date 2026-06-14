import os
import json
import logging
import httpx
from typing import Optional, List, Dict, Any

logger = logging.getLogger("ShikshaAI.llm")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
MODEL_NAME = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
DISABLE_LLM = os.environ.get("DISABLE_LLM", "false").lower() in ("true", "1", "yes")

async def get_llm_response(
    prompt: str,
    prev_conversation: Optional[List[Dict[str, str]]] = None,
    temperature: float = 0.2,
    max_tokens: int = 1024
) -> str:
    """Generate LLM response using Google Gemini 2.0 Flash API with mock mode fallback."""
    if DISABLE_LLM or not GEMINI_API_KEY:
        logger.info("LLM call running in mock mode (DISABLE_LLM=true or no GEMINI_API_KEY)")
        return _get_mock_response(prompt)

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={GEMINI_API_KEY}"
        
        contents = []
        if prev_conversation:
            for msg in prev_conversation:
                role = "user" if msg.get("role") == "user" else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg.get("content", "")}]
                })
        
        contents.append({
            "role": "user",
            "parts": [{"text": prompt}]
        })

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens
            }
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "").strip()
            
            return _get_mock_response(prompt)

    except Exception as e:
        logger.error(f"Error calling Gemini API: {e}. Falling back to mock response.")
        return _get_mock_response(prompt)


def _get_mock_response(prompt: str) -> str:
    prompt_lower = prompt.lower()
    if "subject" in prompt_lower or "विषय" in prompt_lower or "intro" in prompt_lower:
        return "नमस्ते! शिक्षा AI में आपका स्वागत है। आप किस विषय की पढ़ाई कर रहे हैं और परीक्षा की तैयारी कैसे करते हैं?"
    elif "frequency" in prompt_lower or "आवृति" in prompt_lower or "likert" in prompt_lower:
        return "आप इस तकनीक (जैसे फ्लैशकार्ड या नोट्स बनाना) का उपयोग कितनी बार करते हैं? (1 = बहुत कम, 5 = हमेशा)"
    elif "summary" in prompt_lower or "zusammenfassung" in prompt_lower or "complete" in prompt_lower:
        return "आपकी अध्ययन रणनीति साक्षात्कार पूर्ण हो गया है! आप लक्ष्य निर्धारण और पुनरावृत्ति रणनीतियों का उत्कृष्ट उपयोग करते हैं।"
    else:
        return "धन्यवाद! क्या आप मुझे बता सकते हैं कि जब कोई पाठ कठिन होता है तो आप उसे कैसे समझते हैं?"
