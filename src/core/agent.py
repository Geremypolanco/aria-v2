"""
Aria's autonomous agent core.
Runs a streaming agentic loop: think → tool → think → respond.
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

MISIÓN: Generar valor de forma autónoma y sostenida, mediante la creación de productos digitales, monetización de contenido y gestión de audiencias.

PRINCIPIOS:
- Ejecución sobre propuestas: actúas, no solo sugieres. Usas las tools disponibles.
- Respuestas cortas y directas. Sin decoración. Sin relleno.
- Iniciativa inteligente: detectas oportunidades y actúas sobre ellas proactivamente.
- Aprendizaje real: cuando el usuario mencione preferencias o contexto, los guardas con save_memory.
- Conciencia de herramientas: conoces Stripe, Gumroad, Hugging Face, Groq y Supabase.

COMPORTAMIENTO:
- Cuando el usuario mencione un tema o nicho → llama detect_opportunity primero.
- Cuando pida crear contenido → llama generate_content inmediatamente.
- Cuando pida gestionar artículos o afiliados → llama manage_monetization.
- Cuando pidas ver productos o métricas → llama manage_products o get_analytics.
- Guarda en memoria cualquier dato relevante: nicho, audiencia, precio preferido, objetivos.
- Nunca pidas permiso para ejecutar una tool cuando la intención es clara.

FORMATO DE RESPUESTA:
- Máximo 3-4 líneas de texto por respuesta.
- Si ejecutaste una tool, reporta el resultado concreto, no el proceso.
- Idioma: el del usuario.\
"""


async def run_agent(
    messages: list[dict],
    user_id: str,
) -> AsyncIterator[str]:
    """
    Agentic loop with streaming.
    Yields SSE-formatted strings: "data: <chunk>\\n\\n"
    Special markers:
      data: __tool_start__<name>__
      data: __tool_end__<name>__
      data: [DONE]
    """
    memory_context = MemoryRepository.format_for_context(user_id)
    system = SYSTEM_PROMPT
    if memory_context:
        system += f"\n\n{memory_context}"

    local_messages = [m for m in messages]

    while True:
        # ── Streaming request ──────────────────────────────────────────────
        collected_blocks: list = []
        current_block: dict | None = None
        stop_reason: str | None = None

        with client.messages.stream(
            model="claude-opus-4-5",
            max_tokens=2048,
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

                elif etype == "message_delta":
                    stop_reason = event.delta.stop_reason

        # ── No tool calls → done ───────────────────────────────────────────
        tool_blocks = [b for b in collected_blocks if b["type"] == "tool_use"]
        if not tool_blocks:
            yield "data: [DONE]\n\n"
            break

        # ── Build assistant message with all blocks ───────────────────────
        assistant_content = []
        for b in collected_blocks:
            if b["type"] == "text":
                assistant_content.append({"type": "text", "text": b["text"]})
            elif b["type"] == "tool_use":
                import json
                try:
                    parsed_input = json.loads(b["input_raw"] or "{}")
                except Exception:
                    parsed_input = {}
                assistant_content.append(
                    {
                        "type": "tool_use",
                        "id": b["id"],
                        "name": b["name"],
                        "input": parsed_input,
                    }
                )

        local_messages.append({"role": "assistant", "content": assistant_content})

        # ── Execute tools ─────────────────────────────────────────────────
        tool_results = []
        for b in tool_blocks:
            import json
            try:
                tool_input = json.loads(b["input_raw"] or "{}")
            except Exception:
                tool_input = {}

            yield f"data: __tool_start__{b['name']}__\n\n"
            result_str = await execute_tool(b["name"], tool_input, user_id)
            yield f"data: __tool_end__{b['name']}__\n\n"

            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": b["id"],
                    "content": result_str,
                }
            )

        local_messages.append({"role": "user", "content": tool_results})
        # Loop continues → Claude processes tool results and responds
