"""
Audio generation provider.
Primary:  ElevenLabs → voice cloning + TTS (best quality)
Fallback: OpenAI TTS → tts-1-hd
Fallback: HuggingFace → facebook/mms-tts
"""
from __future__ import annotations
import httpx
import uuid
from src.core.config import settings
from src.db.client import get_supabase


async def generate_audio(
    text: str,
    voice_style: str = "professional",
    language: str = "es",
    user_id: str = "",
) -> dict:
    """
    Returns: { url, provider, duration_estimate, text }
    """
    if settings.ELEVENLABS_API_KEY:
        try:
            result = await _elevenlabs_tts(text, voice_style, language)
            url = await _save_audio(result["audio_bytes"], user_id, "mp3")
            return {"url": url, "provider": "elevenlabs", "text": text[:100], "voice": voice_style}
        except Exception as e:
            print(f"ElevenLabs failed: {e}")

    if settings.OPENAI_API_KEY:
        try:
            result = await _openai_tts(text, voice_style)
            url = await _save_audio(result["audio_bytes"], user_id, "mp3")
            return {"url": url, "provider": "openai/tts", "text": text[:100]}
        except Exception as e:
            print(f"OpenAI TTS failed: {e}")

    if settings.HUGGINGFACE_API_KEY:
        try:
            result = await _hf_tts(text, language)
            url = await _save_audio(result["audio_bytes"], user_id, "wav")
            return {"url": url, "provider": "huggingface/mms", "text": text[:100]}
        except Exception as e:
            print(f"HF TTS failed: {e}")

    raise RuntimeError("No audio provider configured.")


async def transcribe_audio(audio_url: str, language: str = "es") -> dict:
    """Speech-to-text via Groq Whisper (fastest) or HuggingFace."""
    if settings.GROQ_API_KEY:
        try:
            return await _groq_transcribe(audio_url, language)
        except Exception as e:
            print(f"Groq transcribe failed: {e}")

    raise RuntimeError("No transcription provider configured. Add GROQ_API_KEY.")


# ── Provider implementations ─────────────────────────────────────────────

_ELEVENLABS_VOICES = {
    "professional": "21m00Tcm4TlvDq8ikWAM",   # Rachel
    "energetic": "AZnzlk1XvdvUeBnXmlld",       # Domi
    "calm": "EXAVITQu4vr4xnSDxMaL",            # Bella
    "authoritative": "VR6AewLTigWG4xSOukaG",    # Arnold
}

async def _elevenlabs_tts(text: str, voice_style: str, language: str) -> dict:
    voice_id = _ELEVENLABS_VOICES.get(voice_style, _ELEVENLABS_VOICES["professional"])
    async with httpx.AsyncClient(timeout=60) as client:
        res = await client.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers={"xi-api-key": settings.ELEVENLABS_API_KEY, "Content-Type": "application/json"},
            json={
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
            },
        )
        res.raise_for_status()
        return {"audio_bytes": res.content}


async def _openai_tts(text: str, voice_style: str) -> dict:
    voice_map = {"professional": "nova", "energetic": "shimmer", "calm": "alloy", "authoritative": "onyx"}
    async with httpx.AsyncClient(timeout=60) as client:
        res = await client.post(
            "https://api.openai.com/v1/audio/speech",
            headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
            json={"model": "tts-1-hd", "input": text, "voice": voice_map.get(voice_style, "nova")},
        )
        res.raise_for_status()
        return {"audio_bytes": res.content}


async def _hf_tts(text: str, language: str) -> dict:
    model = "facebook/mms-tts-spa" if language == "es" else "facebook/mms-tts-eng"
    async with httpx.AsyncClient(timeout=60) as client:
        res = await client.post(
            f"https://api-inference.huggingface.co/models/{model}",
            headers={"Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}"},
            json={"inputs": text},
        )
        res.raise_for_status()
        return {"audio_bytes": res.content}


async def _groq_transcribe(audio_url: str, language: str) -> dict:
    async with httpx.AsyncClient(timeout=60) as client:
        audio_res = await client.get(audio_url)
        audio_bytes = audio_res.content

    async with httpx.AsyncClient(timeout=60) as client:
        res = await client.post(
            "https://api.groq.com/openai/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
            files={"file": ("audio.mp3", audio_bytes, "audio/mpeg")},
            data={"model": "whisper-large-v3", "language": language},
        )
        res.raise_for_status()
        return {"text": res.json()["text"], "provider": "groq/whisper"}


async def _save_audio(audio_bytes: bytes, user_id: str, ext: str) -> str:
    asset_id = str(uuid.uuid4())
    path = f"{user_id}/audio/{asset_id}.{ext}"
    try:
        db = get_supabase()
        content_type = "audio/mpeg" if ext == "mp3" else "audio/wav"
        db.storage.from_("assets").upload(path, audio_bytes, {"content-type": content_type})
        return db.storage.from_("assets").get_public_url(path)
    except Exception:
        return ""
