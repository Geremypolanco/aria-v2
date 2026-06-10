"""
Video generation provider.
- Primary: Replicate (minimax)
- Fallback: FAL.ai (Luma Dream Machine / Kling)
- Fallback: HuggingFace
"""
from __future__ import annotations
import httpx
import time
import uuid
import asyncio
from src.core.config import settings
from src.db.client import get_supabase


async def generate_video(
    prompt: str,
    duration_seconds: int = 5,
    style: str = "cinematic",
    user_id: str = "",
) -> dict:
    """
    Returns: { url, provider, duration, prompt, asset_id }
    """
    style_suffix = {
        "cinematic": ", cinematic, 4k, professional videography, smooth motion",
        "marketing": ", marketing video, clean, professional, product showcase",
        "animated": ", smooth animation, fluid motion, vibrant colors",
        "explainer": ", explainer animation, clean motion graphics, professional",
    }.get(style, "")

    full_prompt = prompt + style_suffix

    # ── Try Replicate ─────────────────────────────────────────────────────
    if settings.REPLICATE_API_KEY:
        try:
            result = await _replicate_video(full_prompt, duration_seconds)
            url = await _save_video_to_supabase(result["url"], user_id)
            return {**result, "url": url, "provider": "replicate/minimax", "prompt": prompt, "style": style}
        except Exception as e:
            print(f"Replicate video failed: {e}")

    # ── Fallback: FAL.ai (Luma Dream Machine) ─────────────────────────────
    if settings.FAL_API_KEY:
        try:
            result = await _fal_video(full_prompt)
            url = await _save_video_to_supabase(result["url"], user_id)
            return {**result, "url": url, "provider": "fal-ai/luma", "prompt": prompt, "style": style}
        except Exception as e:
            print(f"FAL video failed: {e}")

    # ── Fallback: HuggingFace ──────────────────────────────────────────────
    if settings.HUGGINGFACE_API_KEY:
        try:
            result = await _hf_video(full_prompt)
            url = await _save_video_to_supabase(result["url"], user_id, is_bytes=True)
            return {**result, "url": url, "provider": "huggingface/text-to-video", "prompt": prompt}
        except Exception as e:
            print(f"HF video failed: {e}")

    raise RuntimeError("All video providers failed. Please check API keys.")


async def _replicate_video(prompt: str, duration: int) -> dict:
    headers = {
        "Authorization": f"Token {settings.REPLICATE_API_KEY}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=300) as client:
        res = await client.post(
            "https://api.replicate.com/v1/models/minimax/video-01/predictions",
            headers=headers,
            json={"input": {"prompt": prompt, "duration": duration}},
        )
        res.raise_for_status()
        prediction = res.json()
        pred_id = prediction["id"]

        for _ in range(48):
            await asyncio.sleep(5)
            poll = await client.get(
                f"https://api.replicate.com/v1/predictions/{pred_id}",
                headers=headers,
            )
            data = poll.json()
            if data["status"] == "succeeded":
                output = data["output"]
                url = output if isinstance(output, str) else output[0]
                return {"url": url, "duration": duration}
            elif data["status"] == "failed":
                raise RuntimeError(f"Replicate failed: {data.get('error')}")

    raise TimeoutError("Video generation timed out")


async def _fal_video(prompt: str) -> dict:
    """Fallback using FAL.ai Luma Dream Machine."""
    headers = {
        "Authorization": f"Key {settings.FAL_API_KEY}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=300) as client:
        # Submit to Luma
        res = await client.post(
            "https://queue.fal.run/fal-ai/luma-dream-machine",
            headers=headers,
            json={"prompt": prompt},
        )
        res.raise_for_status()
        request_id = res.json()["request_id"]

        # Poll
        for _ in range(60):
            await asyncio.sleep(5)
            poll = await client.get(
                f"https://queue.fal.run/fal-ai/luma-dream-machine/requests/{request_id}",
                headers=headers,
            )
            data = poll.json()
            if data["status"] == "COMPLETED":
                return {"url": data["video"]["url"], "duration": 5}
            elif data["status"] == "FAILED":
                raise RuntimeError("FAL generation failed")
    
    raise TimeoutError("FAL video generation timed out")


async def _hf_video(prompt: str) -> dict:
    model = "ali-vilab/text-to-video-ms-1.7b"
    async with httpx.AsyncClient(timeout=180) as client:
        res = await client.post(
            f"https://api-inference.huggingface.co/models/{model}",
            headers={"Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}"},
            json={"inputs": prompt},
        )
        res.raise_for_status()
        return {"url": res.content, "duration": 4, "is_bytes": True}


async def _save_video_to_supabase(url_or_bytes, user_id: str, is_bytes: bool = False) -> str:
    asset_id = str(uuid.uuid4())
    path = f"{user_id}/videos/{asset_id}.mp4"
    try:
        db = get_supabase()
        if is_bytes:
            video_bytes = url_or_bytes
        else:
            async with httpx.AsyncClient(timeout=60) as client:
                r = await client.get(url_or_bytes)
                video_bytes = r.content
        db.storage.from_("assets").upload(path, video_bytes, {"content-type": "video/mp4"})
        return db.storage.from_("assets").get_public_url(path)
    except Exception:
        return url_or_bytes if isinstance(url_or_bytes, str) else ""
