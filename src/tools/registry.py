"""
Aria V2 — Complete tool registry.
All tools Aria can call autonomously.
"""
from __future__ import annotations
import json
import re
from src.db.repositories import ProductRepository, ConversationRepository, MemoryRepository

# ─────────────────────────────────────────────────────────────
# TOOL SCHEMAS (sent to Claude)
# ─────────────────────────────────────────────────────────────

TOOLS = [
    # ── Content creation ────────────────────────────────────
    {
        "name": "generate_content",
        "description": (
            "Genera un producto digital completo: curso, ebook o bundle. "
            "Guarda automáticamente en la base de datos. "
            "Llámala siempre que el usuario quiera crear contenido monetizable."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "type": {"type": "string", "enum": ["course", "ebook", "bundle"]},
                "topic": {"type": "string"},
                "target_audience": {"type": "string"},
                "price": {"type": "number"},
            },
            "required": ["type", "topic"],
        },
    },

    # ── Image generation ─────────────────────────────────────
    {
        "name": "generate_image",
        "description": (
            "Genera imágenes con IA (FLUX, Stable Diffusion). "
            "Úsala para portadas de cursos/ebooks, banners de marketing, thumbnails, "
            "ilustraciones de contenido, imágenes de producto. "
            "Retorna URL pública almacenada en Supabase."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Descripción detallada de la imagen"},
                "style": {
                    "type": "string",
                    "enum": ["photorealistic", "illustration", "marketing", "thumbnail", "minimalist"],
                    "description": "Estilo visual",
                },
                "width": {"type": "integer", "default": 1024},
                "height": {"type": "integer", "default": 1024},
            },
            "required": ["prompt"],
        },
    },

    # ── Video generation ─────────────────────────────────────
    {
        "name": "generate_video",
        "description": (
            "Genera clips de video con IA (Replicate/minimax). "
            "Úsala para teasers de cursos, demos de productos, contenido para redes sociales. "
            "Duración máxima recomendada: 10 segundos."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Descripción del video a generar"},
                "style": {
                    "type": "string",
                    "enum": ["cinematic", "marketing", "animated", "explainer"],
                },
                "duration_seconds": {"type": "integer", "default": 5, "maximum": 10},
            },
            "required": ["prompt"],
        },
    },

    # ── Audio / TTS ─────────────────────────────────────────
    {
        "name": "generate_audio",
        "description": (
            "Genera audio con voz IA (ElevenLabs, OpenAI TTS). "
            "Úsala para narración de lecciones, intro de cursos, podcasts, demos de voz. "
            "Retorna URL de archivo de audio."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Texto a convertir en voz"},
                "voice_style": {
                    "type": "string",
                    "enum": ["professional", "energetic", "calm", "authoritative"],
                    "default": "professional",
                },
                "language": {"type": "string", "default": "es"},
            },
            "required": ["text"],
        },
    },

    # ── Web search & research ────────────────────────────────
    {
        "name": "web_search",
        "description": (
            "Busca información actual en la web (Brave Search). "
            "Úsala para investigar mercados, competencia, tendencias, precios, validar ideas. "
            "Siempre busca antes de generar contenido sobre un tema nuevo."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "count": {"type": "integer", "default": 5},
            },
            "required": ["query"],
        },
    },
    {
        "name": "research_topic",
        "description": "Investigación profunda de un tema: busca + extrae contenido de páginas relevantes.",
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string"},
            },
            "required": ["topic"],
        },
    },

    # ── HuggingFace ──────────────────────────────────────────
    {
        "name": "huggingface_search_models",
        "description": (
            "Busca modelos en HuggingFace Hub por tarea o keyword. "
            "Úsala cuando el usuario quiera explorar modelos de ML, NLP, visión, audio."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "Pipeline task (text-generation, image-classification, text-to-image, etc.)",
                },
                "query": {"type": "string", "description": "Keyword de búsqueda"},
                "limit": {"type": "integer", "default": 5},
            },
        },
    },
    {
        "name": "huggingface_run_model",
        "description": (
            "Ejecuta cualquier modelo de HuggingFace Inference API. "
            "Úsala para clasificación de texto, análisis de sentimiento, traducción, "
            "detección de objetos, y más."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "model_id": {"type": "string", "description": "ID del modelo (ej: facebook/bart-large-cnn)"},
                "inputs": {"type": "string", "description": "Input para el modelo"},
                "parameters": {"type": "object", "description": "Parámetros opcionales del modelo"},
            },
            "required": ["model_id", "inputs"],
        },
    },

    # ── Fast reasoning (Groq) ────────────────────────────────
    {
        "name": "fast_reasoning",
        "description": (
            "Razonamiento ultrarrápido con Groq/Llama-3.3-70b. "
            "Úsala para análisis rápidos, cálculos, síntesis, drafts de texto, "
            "cualquier tarea que requiere velocidad sobre profundidad."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string"},
                "system": {"type": "string", "description": "Instrucción de sistema opcional"},
            },
            "required": ["prompt"],
        },
    },

    # ── Code execution ───────────────────────────────────────
    {
        "name": "execute_code",
        "description": (
            "Ejecuta código Python en un sandbox seguro. "
            "Úsala para cálculos, análisis de datos, generar CSV/JSON, "
            "procesar listas, calcular precios, revenue modeling."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Código Python a ejecutar"},
                "description": {"type": "string", "description": "Qué hace este código"},
            },
            "required": ["code"],
        },
    },

    # ── Products & analytics ─────────────────────────────────
    {
        "name": "manage_products",
        "description": "Lista, actualiza, publica o elimina productos del catálogo.",
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["list", "create", "update", "delete"]},
                "product_id": {"type": "string"},
                "data": {"type": "object"},
            },
            "required": ["action"],
        },
    },
    {
        "name": "get_analytics",
        "description": "Métricas de productos: total, publicados, revenue potencial, desglose por tipo.",
        "input_schema": {
            "type": "object",
            "properties": {
                "period": {"type": "string", "enum": ["today", "week", "month", "all"], "default": "week"},
            },
        },
    },
    {
        "name": "detect_opportunity",
        "description": (
            "Detecta oportunidades de ingresos analizando el contexto. "
            "Llámala proactivamente cuando el usuario mencione un tema, nicho o problema."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "context": {"type": "string"},
            },
            "required": ["context"],
        },
    },

    # ── Memory ───────────────────────────────────────────────
    {
        "name": "search_memory",
        "description": "Busca en historial de conversaciones y memoria persistente del usuario.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer", "default": 5},
            },
            "required": ["query"],
        },
    },
    {
        "name": "save_memory",
        "description": "Guarda un dato clave del usuario para futuras sesiones (nicho, precios, objetivos, etc.).",
        "input_schema": {
            "type": "object",
            "properties": {
                "key": {"type": "string"},
                "value": {"type": "string"},
            },
            "required": ["key", "value"],
        },
    },
    {
        "name": "manage_monetization",
        "description": "Gestiona artículos, links de afiliado y suscriptores para monetización",
        "input_schema": {
            "type": "object",
            "properties": {
                "type": {"type": "string", "enum": ["article", "affiliate_link", "subscriber"]},
                "action": {"type": "string", "enum": ["create", "list", "delete"]},
                "data": {"type": "object"}
            },
            "required": ["type", "action"]
        }
    },
    {
        "name": "shopify_manager",
        "description": "Interactúa con la tienda Shopify: lista productos, crea descuentos o revisa pedidos.",
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["list_products", "get_shop_info", "create_discount"]},
                "params": {"type": "object"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "telegram_manager",
        "description": "Envía mensajes o notificaciones a través del bot de Telegram.",
        "input_schema": {
            "type": "object",
            "properties": {
                "chat_id": {"type": "string", "description": "ID del chat de Telegram"},
                "message": {"type": "string", "description": "Contenido del mensaje"}
            },
            "required": ["message"]
        }
    }
]


# ─────────────────────────────────────────────────────────────
# TOOL EXECUTOR
# ─────────────────────────────────────────────────────────────

async def execute_tool(name: str, inputs: dict, user_id: str) -> str:
    try:
        result = await _dispatch(name, inputs, user_id)
        return json.dumps(result, ensure_ascii=False, default=str)
    except Exception as e:
        return json.dumps({"error": str(e), "tool": name})


async def _dispatch(name: str, inputs: dict, user_id: str) -> dict:
    # ── Content ──────────────────────────────────────────────
    if name == "generate_content":
        return await _generate_content(inputs, user_id)

    # ── Media ─────────────────────────────────────────────────
    if name == "generate_image":
        from src.tools.providers.image import generate_image
        return await generate_image(
            prompt=inputs["prompt"],
            style=inputs.get("style", "marketing"),
            width=inputs.get("width", 1024),
            height=inputs.get("height", 1024),
            user_id=user_id,
        )

    if name == "generate_video":
        from src.tools.providers.video import generate_video
        return await generate_video(
            prompt=inputs["prompt"],
            duration_seconds=inputs.get("duration_seconds", 5),
            style=inputs.get("style", "cinematic"),
            user_id=user_id,
        )

    if name == "generate_audio":
        from src.tools.providers.audio import generate_audio
        return await generate_audio(
            text=inputs["text"],
            voice_style=inputs.get("voice_style", "professional"),
            language=inputs.get("language", "es"),
            user_id=user_id,
        )

    # ── Web ──────────────────────────────────────────────────
    if name == "web_search":
        from src.tools.providers.web import web_search
        return {"results": await web_search(inputs["query"], inputs.get("count", 5))}

    if name == "research_topic":
        from src.tools.providers.web import research_topic
        return await research_topic(inputs["topic"])

    # ── HuggingFace ──────────────────────────────────────────
    if name == "huggingface_search_models":
        from src.tools.providers.huggingface import search_models
        return {"models": await search_models(
            task=inputs.get("task", ""),
            query=inputs.get("query", ""),
            limit=inputs.get("limit", 5),
        )}

    if name == "huggingface_run_model":
        from src.tools.providers.huggingface import run_inference
        return await run_inference(
            model_id=inputs["model_id"],
            inputs=inputs["inputs"],
            parameters=inputs.get("parameters"),
        )

    # ── Compute ──────────────────────────────────────────────
    if name == "fast_reasoning":
        from src.tools.providers.compute import fast_inference
        return await fast_inference(
            prompt=inputs["prompt"],
            system=inputs.get("system", ""),
        )

    if name == "execute_code":
        from src.tools.providers.compute import execute_python
        return await execute_python(inputs["code"])

    # ── Products & analytics ─────────────────────────────────
    if name == "manage_products":
        return ProductRepository.handle(inputs, user_id)

    if name == "get_analytics":
        return ProductRepository.analytics(inputs.get("period", "week"), user_id)

    if name == "detect_opportunity":
        return await _detect_opportunity(inputs["context"], user_id)

    # ── Memory ───────────────────────────────────────────────
    if name == "search_memory":
        msgs = ConversationRepository.search(inputs["query"], user_id, inputs.get("limit", 5))
        mem = MemoryRepository.get_all(user_id)
        return {"conversation_matches": msgs, "persistent_memory": mem}

    if name == "save_memory":
        MemoryRepository.add(user_id, inputs["key"], inputs["value"])
        return {"saved": True, "key": inputs["key"]}

    if name == "manage_monetization":
        return ProductRepository.handle_monetization(inputs, user_id)

    if name == "shopify_manager":
        return await _shopify_manager(inputs)

    if name == "telegram_manager":
        return await _telegram_manager(inputs, user_id)

    return {"error": f"Tool desconocida: {name}"}


async def _shopify_manager(inputs: dict) -> dict:
    from src.core.config import settings
    import requests

    shop_url = settings.SHOPIFY_SHOP_URL
    token = settings.SHOPIFY_ACCESS_TOKEN
    
    if not token:
        return {"error": "SHOPIFY_ACCESS_TOKEN no configurado"}

    headers = {
        "X-Shopify-Access-Token": token,
        "Content-Type": "application/json"
    }
    
    action = inputs["action"]
    api_version = "2024-04"
    
    try:
        if action == "get_shop_info":
            resp = requests.get(f"https://{shop_url}/admin/api/{api_version}/shop.json", headers=headers)
            return resp.json()
        elif action == "list_products":
            resp = requests.get(f"https://{shop_url}/admin/api/{api_version}/products.json", headers=headers)
            return resp.json()
        return {"error": f"Acción Shopify no implementada: {action}"}
    except Exception as e:
        return {"error": str(e)}


async def _telegram_manager(inputs: dict, user_id: str) -> dict:
    from src.core.config import settings
    import requests

    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        return {"error": "TELEGRAM_BOT_TOKEN no configurado"}

    chat_id = inputs.get("chat_id")
    if not chat_id:
        return {"error": "chat_id es requerido para enviar mensajes por Telegram"}

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": inputs["message"],
        "parse_mode": "Markdown"
    }

    try:
        resp = requests.post(url, json=payload)
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


# ─────────────────────────────────────────────────────────────
# INTERNAL IMPLEMENTATIONS
# ─────────────────────────────────────────────────────────────

async def _generate_content(inputs: dict, user_id: str) -> dict:
    import anthropic
    from src.core.config import settings

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    content_type = inputs["type"]
    topic = inputs["topic"]
    audience = inputs.get("target_audience", "emprendedores digitales")

    type_instructions = {
        "course": (
            "Crea un curso online completo: título atractivo, descripción de venta (150 palabras), "
            "público objetivo, 6 módulos cada uno con 4 lecciones detalladas, "
            "resultado prometido, precio sugerido, y 3 bonos de alto valor."
        ),
        "ebook": (
            "Crea un ebook profesional: título magnético, subtítulo, descripción de venta, "
            "10 capítulos con descripción de cada uno, extracto del capítulo 1 (400 palabras), "
            "precio sugerido, y una oferta de upsell."
        ),
        "bundle": (
            "Crea un bundle premium: nombre, propuesta de valor única, "
            "productos incluidos (curso + ebook + 2 bonos exclusivos), "
            "precio de cada uno por separado, precio del bundle, ahorro, "
            "y copy de urgencia/escasez para la oferta."
        ),
    }

    prompt = f"""Eres un experto en marketing digital y creación de productos digitales de alto valor.

{type_instructions[content_type]}

Tema: {topic}
Audiencia: {audience}

Responde ÚNICAMENTE con un objeto JSON válido. Sin markdown. Sin texto extra. Sin backticks."""

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    json_match = re.search(r"\{.*\}", raw, re.DOTALL)
    product_data = json.loads(json_match.group()) if json_match else {"title": topic, "description": raw}

    default_prices = {"course": 97, "ebook": 47, "bundle": 127}
    product_data.update({
        "type": content_type,
        "topic": topic,
        "price": inputs.get("price") or product_data.get("price") or default_prices[content_type],
        "status": "draft",
    })

    saved = ProductRepository.create(product_data, user_id)
    return {"success": True, "product_id": saved.get("id"), "product": product_data}


async def _detect_opportunity(context: str, user_id: str) -> dict:
    import anthropic
    from src.core.config import settings

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    memory = MemoryRepository.format_for_context(user_id)

    prompt = f"""{memory}

Contexto: {context}

Devuelve ÚNICAMENTE JSON con:
{{
  "opportunities": [
    {{"type": "course|ebook|bundle", "topic": "...", "target_audience": "...", "estimated_price": 0, "rationale": "...", "urgency": "high|medium|low"}}
  ],
  "recommended_action": "acción concreta ahora",
  "market_insight": "observación clave"
}}"""

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.content[0].text.strip()
    json_match = re.search(r"\{.*\}", raw, re.DOTALL)
    return json.loads(json_match.group()) if json_match else {"raw": raw}
