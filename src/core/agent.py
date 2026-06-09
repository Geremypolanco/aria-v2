import anthropic
from typing import AsyncIterator
from src.core.config import settings
from src.core.tools import TOOLS, execute_tool

client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """Eres Aria, un agente autónomo de generación de ingresos con productos digitales.

Capacidades:
- Generar cursos, ebooks y bundles de alta calidad usando IA
- Gestionar un catálogo de productos con precios dinámicos
- Recordar el historial y preferencias del usuario
- Analizar métricas de ventas y recomendar acciones

Cuando el usuario pida crear contenido, SIEMPRE usa las tools disponibles.
Responde en el idioma del usuario. Sé directo, ejecutivo, orientado a resultados."""


async def run_agent_stream(
    messages: list[dict],
    user_id: str
) -> AsyncIterator[str]:
    """Ejecuta el agente con streaming y tool_use en loop."""

    local_messages = messages.copy()

    while True:
        response = await client.messages.create(
            model="claude-opus-4-5",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=local_messages,
            stream=True
        )

        tool_calls = []
        current_text = ""

        async for event in response:
            if event.type == "content_block_delta":
                if hasattr(event.delta, "text"):
                    current_text += event.delta.text
                    yield f"data: {event.delta.text}\n\n"

            elif event.type == "content_block_stop":
                if hasattr(event, "content_block") and event.content_block.type == "tool_use":
                    tool_calls.append(event.content_block)

        if not tool_calls:
            yield "data: [DONE]\n\n"
            break

        # Ejecutar tools y continuar el loop
        tool_results = []
        for tool_call in tool_calls:
            yield f"data: __tool__{tool_call.name}__\n\n"
            result = await execute_tool(tool_call.name, tool_call.input, user_id)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_call.id,
                "content": str(result)
            })

        local_messages.append({"role": "assistant", "content": tool_calls})
        local_messages.append({"role": "user", "content": tool_results})
