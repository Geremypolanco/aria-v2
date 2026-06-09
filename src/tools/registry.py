"""
Tool registry for Aria's autonomous agent.
Each tool maps to a real execution function.
"""
from __future__ import annotations
import json
import re
from src.db.repositories import ProductRepository, ConversationRepository, MemoryRepository

# ─────────────────────────────────────────────
# Tool schemas (sent to Claude)
# ─────────────────────────────────────────────

TOOLS = [
    {
        "name": "generate_content",
        "description": (
            "Genera un producto digital completo y de alta calidad: curso, ebook o bundle. "
            "Llama esta tool siempre que el usuario quiera crear contenido monetizable. "
            "El producto se guarda en la base de datos automáticamente."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "type": {
                    "type": "string",
                    "enum": ["course", "ebook", "bundle"],
                    "description": "Tipo de producto a generar",
                },
                "topic": {
                    "type": "string",
                    "description": "Tema principal del producto",
                },
                "target_audience": {
                    "type": "string",
                    "description": "Audiencia objetivo",
                },
                "price": {
                    "type": "number",
                    "description": "Precio en USD. Si no se especifica, Aria elige uno óptimo.",
                },
            },
            "required": ["type", "topic"],
        },
    },
    {
        "name": "manage_products",
        "description": "Lista, actualiza, publica o elimina productos del catálogo del usuario.",
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["list", "create", "update", "delete"],
                },
                "product_id": {"type": "string"},
                "data": {
                    "type": "object",
                    "description": "Datos a actualizar (para action=update)",
                },
            },
            "required": ["action"],
        },
    },
    {
        "name": "search_memory",
        "description": "Busca en el historial de conversaciones y memoria persistente del usuario.",
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
        "description": (
            "Guarda un dato importante sobre el usuario o su negocio en memoria persistente. "
            "Úsala cuando detectes preferencias, objetivos o contexto relevante para futuras sesiones."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "Identificador corto (ej: 'nicho_principal', 'precio_preferido')",
                },
                "value": {"type": "string", "description": "Valor a recordar"},
            },
            "required": ["key", "value"],
        },
    },
    {
        "name": "get_analytics",
        "description": "Obtiene métricas de productos: total creados, publicados, ingresos potenciales y desglose por tipo.",
        "input_schema": {
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "enum": ["today", "week", "month", "all"],
                    "default": "week",
                },
            },
        },
    },
    {
        "name": "detect_opportunity",
        "description": (
            "Analiza el contexto actual y detecta oportunidades de generación de ingresos. "
            "Llama esta tool proactivamente cuando el usuario mencione un tema, problema o audiencia."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "context": {
                    "type": "string",
                    "description": "Contexto o tema sobre el que detectar oportunidades",
                },
            },
            "required": ["context"],
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

# ─────────────────────────────────────────────
# Tool executor
# ─────────────────────────────────────────────

async def execute_tool(name: str, inputs: dict, user_id: str) -> str:
    try:
        if name == "generate_content":
            result = await _generate_content(inputs, user_id)
        elif name == "manage_products":
            result = ProductRepository.handle(inputs, user_id)
        elif name == "search_memory":
            msgs = ConversationRepository.search(inputs["query"], user_id, inputs.get("limit", 5))
            mem = MemoryRepository.get_all(user_id)
            result = {"conversation_matches": msgs, "persistent_memory": mem}
        elif name == "save_memory":
            MemoryRepository.add(user_id, inputs["key"], inputs["value"])
            result = {"saved": True, "key": inputs["key"]}
        elif name == "get_analytics":
            result = ProductRepository.analytics(inputs.get("period", "week"), user_id)
        elif name == "detect_opportunity":
            result = await _detect_opportunity(inputs["context"], user_id)
        elif name == "manage_monetization":
            result = ProductRepository.handle_monetization(inputs, user_id)
        elif name == "shopify_manager":
            result = await _shopify_manager(inputs)
        elif name == "telegram_manager":
            result = await _telegram_manager(inputs, user_id)
        else:
            result = {"error": f"Tool desconocida: {name}"}
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})


# ─────────────────────────────────────────────
# Internal implementations
# ─────────────────────────────────────────────

async def _generate_content(inputs: dict, user_id: str) -> dict:
    import anthropic
    from src.core.config import settings

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    content_type = inputs["type"]
    topic = inputs["topic"]
    audience = inputs.get("target_audience", "emprendedores digitales")

    type_instructions = {
        "course": (
            "Crea un curso online completo con: título atractivo, descripción de venta (150 palabras), "
            "público objetivo, módulos (5-8) cada uno con 3-5 lecciones detalladas, "
            "resultado prometido y precio sugerido."
        ),
        "ebook": (
            "Crea un ebook profesional con: título magnético, subtítulo, descripción de venta, "
            "índice detallado (8-12 capítulos), extracto del capítulo 1 (300 palabras) y precio sugerido."
        ),
        "bundle": (
            "Crea un bundle premium: nombre del bundle, propuesta de valor única, "
            "lista de productos incluidos (curso + ebook + bonus), precio individual de cada uno, "
            "precio del bundle con descuento y urgencia/escasez para la oferta."
        ),
    }

    prompt = f"""Eres un experto en marketing digital y creación de productos digitales de alto valor.

{type_instructions[content_type]}

Tema: {topic}
Audiencia: {audience}

Responde ÚNICAMENTE con un objeto JSON válido, sin markdown, sin texto extra.
El JSON debe tener esta estructura base:
{{
  "title": "...",
  "description": "...",
  "price": número,
  "target_audience": "...",
  "modules_or_chapters": [...],
  "value_proposition": "...",
  "expected_outcome": "..."
}}"""

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    json_match = re.search(r"\{.*\}", raw, re.DOTALL)
    if json_match:
        product_data = json.loads(json_match.group())
    else:
        product_data = {"title": topic, "description": raw}

    default_prices = {"course": 97, "ebook": 47, "bundle": 127}
    product_data.update(
        {
            "type": content_type,
            "topic": topic,
            "price": inputs.get("price") or product_data.get("price") or default_prices[content_type],
            "status": "draft",
        }
    )

    saved = ProductRepository.create(product_data, user_id)
    return {"success": True, "product_id": saved.get("id"), "product": product_data}


async def _detect_opportunity(context: str, user_id: str) -> dict:
    import anthropic
    from src.core.config import settings

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    memory = MemoryRepository.format_for_context(user_id)

    prompt = f"""Eres Aria, un agente autónomo de generación de ingresos con productos digitales.

{memory}

Contexto actual: {context}

Analiza y devuelve ÚNICAMENTE un JSON con:
{{
  "opportunities": [
    {{
      "type": "course|ebook|bundle",
      "topic": "...",
      "target_audience": "...",
      "estimated_price": número,
      "rationale": "por qué esto generaría ingresos",
      "urgency": "high|medium|low"
    }}
  ],
  "recommended_action": "acción concreta a tomar ahora",
  "market_insight": "observación clave sobre el mercado"
}}"""

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    json_match = re.search(r"\{.*\}", raw, re.DOTALL)
    return json.loads(json_match.group()) if json_match else {"raw": raw}


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

    # Si no hay chat_id, intentamos obtenerlo de la memoria del usuario o usamos un default
    chat_id = inputs.get("chat_id")
    if not chat_id:
        # Aquí se podría buscar en MemoryRepository por 'telegram_chat_id'
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
