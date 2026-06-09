from src.db.repositories import ProductRepository, ConversationRepository

TOOLS = [
    {
        "name": "generate_content",
        "description": "Genera un producto digital completo (curso, ebook o bundle). Llama a esta tool cuando el usuario quiera crear contenido.",
        "input_schema": {
            "type": "object",
            "properties": {
                "type": {"type": "string", "enum": ["course", "ebook", "bundle"]},
                "topic": {"type": "string", "description": "Tema del contenido"},
                "target_audience": {"type": "string"},
                "price": {"type": "number"}
            },
            "required": ["type", "topic"]
        }
    },
    {
        "name": "manage_products",
        "description": "Lista, crea o actualiza productos en el catálogo",
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["list", "create", "update", "delete"]},
                "product_id": {"type": "string"},
                "data": {"type": "object"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "search_memory",
        "description": "Busca en el historial de conversaciones y preferencias del usuario",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer", "default": 5}
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_analytics",
        "description": "Obtiene métricas de ventas, conversiones y rendimiento de productos",
        "input_schema": {
            "type": "object",
            "properties": {
                "period": {"type": "string", "enum": ["today", "week", "month", "all"]},
                "metric": {"type": "string", "enum": ["revenue", "conversions", "top_products"]}
            }
        }
    }
]


async def execute_tool(name: str, inputs: dict, user_id: str) -> dict:
    if name == "generate_content":
        return await _generate_content(inputs, user_id)
    elif name == "manage_products":
        return await ProductRepository.handle(inputs, user_id)
    elif name == "search_memory":
        return await ConversationRepository.search(inputs["query"], user_id, inputs.get("limit", 5))
    elif name == "get_analytics":
        return await ProductRepository.analytics(inputs.get("period", "week"), user_id)
    return {"error": f"Tool desconocida: {name}"}


async def _generate_content(inputs: dict, user_id: str) -> dict:
    from src.core.agent import client

    content_type = inputs["type"]
    topic = inputs["topic"]

    prompt = f"""Crea un {content_type} completo y profesional sobre: {topic}

Para un curso: incluye título, descripción, 5-8 módulos con lecciones detalladas, precio sugerido.
Para un ebook: incluye título, descripción, índice con 8-12 capítulos, extracto del primer capítulo, precio.
Para un bundle: combina curso + ebook con precio especial y propuesta de valor.

Responde en JSON con la estructura del producto."""

    response = await client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    import json
    import re
    text = response.content[0].text
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    product_data = json.loads(json_match.group()) if json_match else {"content": text}

    product_data.update({
        "type": content_type,
        "topic": topic,
        "price": inputs.get("price") or {"course": 97, "ebook": 47, "bundle": 127}[content_type],
        "status": "draft"
    })

    saved = await ProductRepository.create(product_data, user_id)
    return {"success": True, "product": saved}
