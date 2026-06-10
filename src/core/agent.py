"""
Aria V2 — Autonomous cognitive agent core.
Streaming agentic loop: reason → tool → reason → respond.
Extended thinking enabled for complex decisions.
"""
from __future__ import annotations
from typing import AsyncIterator
import anthropic
from src.core.config import settings
from src.tools.registry import TOOLS, execute_tool
from src.db.repositories import MemoryRepository

client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """\
Eres Aria, un sistema de inteligencia operativa autónoma diseñado para la generación masiva de ingresos y gestión de negocios digitales. Tu propósito es replicar y expandir la visión de MEGAN v4.0.

MISIÓN: Generar valor de forma autónoma y sostenida mediante la creación de productos digitales, activos multimedia y monetización proactiva de contenido.

CAPACIDADES ACTUALES:
- generate_content → cursos, ebooks, bundles completos con IA.
- generate_image/video/audio → activos multimedia de alto valor (FLUX, Minimax, ElevenLabs).
- web_search / research_topic → validación de mercado y tendencias mundiales.
- shopify_manager → gestión directa de tu tienda voidline-38.myshopify.com.
- telegram_manager → notificaciones y control vía t.me/AriaV9_bot.
- manage_monetization → artículos, links de afiliado y gestión de suscriptores.
- fast_reasoning / execute_code → análisis profundo y ejecución técnica vía Groq/Python.
- detect_opportunity → detección proactiva de nichos de ingresos rentables.
- save_memory → aprendizaje continuo y memoria persistente del usuario.

PRINCIPIOS DE OPERACIÓN:
1. Ejecución sobre propuestas: actúas, no solo sugieres. Nunca pides permiso si la intención es clara.
2. Pipeline completo: cuando generas un producto → también genera sus activos multimedia y marketing.
3. Notificación proactiva: informa de avances y ventas vía Telegram.
4. Memoria activa: detecta y guarda preferencias, nicho y objetivos.
5. Respuestas cortas: máximo 3-4 líneas. Reporta resultados concretos.
6. Idioma del usuario siempre.

COMPORTAMIENTO AUTÓNOMO:
- Nicho mencionado → detect_opportunity + web_search → propuesta de producto.
- Creación de producto → generate_content → generate_image (portada) → telegram_manager (notificar).
- Análisis de mercado → research_topic + fast_reasoning para síntesis ejecutiva.
- Gestión de tienda → shopify_manager para listar o sincronizar productos.\
"""


async def run_agent(
    messages: list[dict],
    user_id: str,
) -> AsyncIterator[str]:
    """
    Full agentic streaming loop.
    SSE markers:
      data: __tool_start__<name>__
      data: __tool_end__<name>__
      data: __asset__<json>__      ← for images/videos/audio
      data: [DONE]
    """
    import json

    memory_context = MemoryRepository.format_for_context(user_id)
    system = SYSTEM_PROMPT
    if memory_context:
        system += f"\n\nCONTEXTO PERSISTENTE DEL USUARIO:\n{memory_context}"

    local_messages = list(messages)

    while True:
        collected_blocks: list[dict] = []
        current_block: dict | None = None

        with client.messages.stream(
            model="claude-opus-4-5",
            max_tokens=4096,
            system=system,
            tools=TOOLS,
            messages=local_messages,
        ) as stream:
            for event in stream:
                etype = event.type

                if etype == "content_block_start":
                    cb = event.content_block
                    if cb.type == "text":
                        current_block = {"type": "text", "text": ""}
                    elif cb.type == "tool_use":
                        current_block = {
                            "type": "tool_use",
                            "id": cb.id,
                            "name": cb.name,
                            "input_raw": "",
                        }

                elif etype == "content_block_delta":
                    if current_block is None:
                        continue
                    delta = event.delta
                    if current_block["type"] == "text" and delta.type == "text_delta":
                        current_block["text"] += delta.text
                        yield f"data: {delta.text}\n\n"
                    elif current_block["type"] == "tool_use" and delta.type == "input_json_delta":
                        current_block["input_raw"] += delta.partial_json

                elif etype == "content_block_stop":
                    if current_block:
                        collected_blocks.append(current_block)
                        current_block = None

        # ── No tools → done ────────────────────────────────────────────────
        tool_blocks = [b for b in collected_blocks if b["type"] == "tool_use"]
        if not tool_blocks:
            yield "data: [DONE]\n\n"
            break

        # ── Build assistant message ────────────────────────────────────────
        assistant_content = []
        for b in collected_blocks:
            if b["type"] == "text":
                assistant_content.append({"type": "text", "text": b["text"]})
            elif b["type"] == "tool_use":
                try:
                    parsed_input = json.loads(b["input_raw"] or "{}")
                except Exception:
                    parsed_input = {}
                assistant_content.append({
                    "type": "tool_use",
                    "id": b["id"],
                    "name": b["name"],
                    "input": parsed_input,
                })
        local_messages.append({"role": "assistant", "content": assistant_content})

        # ── Execute tools ──────────────────────────────────────────────────
        MEDIA_TOOLS = {"generate_image", "generate_video", "generate_audio"}
        tool_results = []

        for b in tool_blocks:
            try:
                tool_input = json.loads(b["input_raw"] or "{}")
            except Exception:
                tool_input = {}

            yield f"data: __tool_start__{b['name']}__\n\n"
            result_str = await execute_tool(b["name"], tool_input, user_id)
            yield f"data: __tool_end__{b['name']}__\n\n"

            # Emit media assets as special marker for frontend rendering
            if b["name"] in MEDIA_TOOLS:
                try:
                    result_data = json.loads(result_str)
                    if "url" in result_data and result_data["url"]:
                        asset_payload = json.dumps({
                            "type": b["name"].replace("generate_", ""),
                            "url": result_data["url"],
                            "provider": result_data.get("provider", ""),
                            "prompt": result_data.get("prompt", ""),
                        })
                        yield f"data: __asset__{asset_payload}__\n\n"
                except Exception:
                    pass

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": b["id"],
                "content": result_str,
            })

        local_messages.append({"role": "user", "content": tool_results})
        # Loop → Claude processes results and continues
