"""
HuggingFace Hub provider.
- Run any model via Inference API
- Search trending / task-specific models
- Download datasets info
- Fine-tune triggers (future)
"""
from __future__ import annotations
import httpx
from src.core.config import settings

HF_BASE = "https://huggingface.co"
HF_API = "https://api-inference.huggingface.co"
HF_HUB = "https://huggingface.co/api"


async def search_models(task: str = "", query: str = "", limit: int = 5) -> list[dict]:
    """Search HuggingFace Hub for models by task or keyword."""
    params: dict = {"limit": limit, "sort": "downloads", "direction": -1}
    if task:
        params["pipeline_tag"] = task
    if query:
        params["search"] = query

    async with httpx.AsyncClient(timeout=30) as client:
        res = await client.get(
            f"{HF_HUB}/models",
            headers=_hf_headers(),
            params=params,
        )
        res.raise_for_status()
        models = res.json()

    return [
        {
            "id": m.get("id"),
            "task": m.get("pipeline_tag"),
            "downloads": m.get("downloads", 0),
            "likes": m.get("likes", 0),
            "tags": m.get("tags", [])[:5],
            "url": f"{HF_BASE}/{m.get('id')}",
        }
        for m in models
    ]


async def run_inference(model_id: str, inputs: str | dict, parameters: dict | None = None) -> dict:
    """Run any HuggingFace model via Inference API."""
    payload: dict = {"inputs": inputs}
    if parameters:
        payload["parameters"] = parameters

    async with httpx.AsyncClient(timeout=120) as client:
        res = await client.post(
            f"{HF_API}/models/{model_id}",
            headers=_hf_headers(),
            json=payload,
        )
        res.raise_for_status()
        content_type = res.headers.get("content-type", "")
        if "application/json" in content_type:
            return {"output": res.json(), "model": model_id}
        else:
            # Binary output (image, audio, etc.)
            import base64
            return {"output_base64": base64.b64encode(res.content).decode(), "model": model_id, "content_type": content_type}


async def get_trending_models(task: str = "text-generation", limit: int = 8) -> list[dict]:
    """Get trending models for a specific task."""
    return await search_models(task=task, limit=limit)


async def classify_text(text: str, labels: list[str]) -> dict:
    """Zero-shot text classification."""
    result = await run_inference(
        "facebook/bart-large-mnli",
        inputs=text,
        parameters={"candidate_labels": labels},
    )
    return result


async def sentiment_analysis(text: str) -> dict:
    """Quick sentiment analysis."""
    result = await run_inference("cardiffnlp/twitter-roberta-base-sentiment-latest", inputs=text)
    return result


async def summarize_text(text: str, max_length: int = 150) -> dict:
    """Summarize long text."""
    result = await run_inference(
        "facebook/bart-large-cnn",
        inputs=text,
        parameters={"max_length": max_length, "min_length": 40},
    )
    return result


async def translate_text(text: str, target_lang: str = "en") -> dict:
    """Translate text using Helsinki-NLP models."""
    model_map = {
        "en": "Helsinki-NLP/opus-mt-es-en",
        "es": "Helsinki-NLP/opus-mt-en-es",
        "fr": "Helsinki-NLP/opus-mt-es-fr",
        "de": "Helsinki-NLP/opus-mt-es-de",
    }
    model = model_map.get(target_lang, "Helsinki-NLP/opus-mt-es-en")
    return await run_inference(model, inputs=text)


async def object_detection(image_url: str) -> dict:
    """Detect objects in an image."""
    async with httpx.AsyncClient(timeout=30) as client:
        img_res = await client.get(image_url)
        img_bytes = img_res.content

    async with httpx.AsyncClient(timeout=60) as client:
        res = await client.post(
            f"{HF_API}/models/facebook/detr-resnet-50",
            headers=_hf_headers(),
            content=img_bytes,
        )
        res.raise_for_status()
        return {"detections": res.json()}


def _hf_headers() -> dict:
    headers = {"Content-Type": "application/json"}
    if settings.HUGGINGFACE_API_KEY:
        headers["Authorization"] = f"Bearer {settings.HUGGINGFACE_API_KEY}"
    return headers
