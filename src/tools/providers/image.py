"""
Image generation provider.
Primary:   fal.ai  → FLUX.1 [schnell] (fast, free tier available)
Fallback:  Hugging Face Inference API → FLUX or SDXL
Fallback2: Stability AI → SD3
"""
from __future__ import annotations
import httpx
import base64
import uuid
from src.core.config import settings
from src.db.client import get_supabase


async def generate_image(
    prompt: str,
    style: str = "photorealistic",
    width: int = 1024,
    height: int = 1024,
    user_id: str = "",
) -> dict:
    """
    Returns: { url, provider, width, height, prompt, asset_id }
    Image is saved to Supabase Storage bucket 'assets'.
    """
    style_suffix = {
        "photorealistic": ", photorealistic, 8k, professional photography",
        "illustration": ", digital illustration, vector art, clean lines, vibrant colors",
        "marketing": ", marketing material, clean background, professional, brand identity",
        "thumbnail": ", YouTube thumbnail style, bold text space, high contrast, eye-catching",
        "minimalist": ", minimalist design, white background, simple shapes, modern",
    }.get(style, "")

    full_prompt = prompt + style_suffix

    # ── Try fal.ai first (best quality/speed) ─────────────────────────────
    if settings.FAL_API_KEY:
        try:
            result = await _fal_generate(full_prompt, width, height)
            url = await _save_to_supabase(result["url"], user_id)
            return {**result, "url": url, "provider": "fal.ai/flux", "prompt": prompt, "style": style}
        except Exception as e:
            print(f"fal.ai failed: {e}")

    # ── Fallback: Hugging Face ─────────────────────────────────────────────
    if settings.HUGGINGFACE_API_KEY:
        try:
            result = await _hf_generate(full_prompt, width, height)
            url = await _save_to_supabase(result["url"], user_id, is_base64=result.get("is_base64"))
            return {**result, "url": url, "provider": "huggingface/flux", "prompt": prompt, "style": style}
        except Exception as e:
            print(f"HuggingFace failed: {e}")

    # ── Fallback: Stability AI ─────────────────────────────────────────────
    if settings.STABILITY_API_KEY:
        try:
            result = await _stability_generate(full_prompt, width, height)
            url = await _save_to_supabase(result["url"], user_id, is_base64=True)
            return {**result, "url": url, "provider": "stability/sd3", "prompt": prompt, "style": style}
        except Exception as e:
            print(f"Stability failed: {e}")

    raise RuntimeError("No image provider configured. Add FAL_API_KEY, HUGGINGFACE_API_KEY, or STABILITY_API_KEY.")


async def _fal_generate(prompt: str, width: int, height: int) -> dict:
    async with httpx.AsyncClient(timeout=60) as client:
        res = await client.post(
            "https://fal.run/fal-ai/flux/schnell",
            headers={"Authorization": f"Key {settings.FAL_API_KEY}"},
            json={"prompt": prompt, "image_size": {"width": width, "height": height}, "num_images": 1},
        )
        res.raise_for_status()
        data = res.json()
        return {"url": data["images"][0]["url"], "width": width, "height": height}


async def _hf_generate(prompt: str, width: int, height: int) -> dict:
    # Use FLUX.1-schnell via HF Inference API
    model = "black-forest-labs/FLUX.1-schnell"
    async with httpx.AsyncClient(timeout=120) as client:
        res = await client.post(
            f"https://api-inference.huggingface.co/models/{model}",
            headers={"Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}"},
            json={"inputs": prompt, "parameters": {"width": width, "height": height}},
        )
        res.raise_for_status()
        # HF returns raw bytes
        b64 = base64.b64encode(res.content).decode()
        return {"url": b64, "width": width, "height": height, "is_base64": True}


async def _stability_generate(prompt: str, width: int, height: int) -> dict:
    async with httpx.AsyncClient(timeout=60) as client:
        res = await client.post(
            "https://api.stability.ai/v2beta/stable-image/generate/sd3",
            headers={"Authorization": f"Bearer {settings.STABILITY_API_KEY}", "Accept": "application/json"},
            data={"prompt": prompt, "output_format": "png"},
            files={"none": ""},
        )
        res.raise_for_status()
        data = res.json()
        return {"url": data["image"], "width": width, "height": height, "is_base64": True}


async def _save_to_supabase(url_or_b64: str, user_id: str, is_base64: bool = False) -> str:
    """Upload image to Supabase Storage, return public URL."""
    asset_id = str(uuid.uuid4())
    path = f"{user_id}/{asset_id}.png"

    try:
        db = get_supabase()
        if is_base64:
            image_bytes = base64.b64decode(url_or_b64)
        else:
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.get(url_or_b64)
                image_bytes = r.content

        db.storage.from_("assets").upload(path, image_bytes, {"content-type": "image/png"})
        public_url = db.storage.from_("assets").get_public_url(path)
        return public_url
    except Exception:
        # If storage fails, return original URL or data URI
        if is_base64:
            return f"data:image/png;base64,{url_or_b64}"
        return url_or_b64
