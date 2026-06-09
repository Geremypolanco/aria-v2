import anthropic
from typing import AsyncIterator
from src.core.config import settings
from src.core.tools import TOOLS, execute_tool

client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """Eres Aria, un sistema de inteligencia operativa autónoma diseñado para la generación masiva de ingresos y gestión de negocios digitales. Tu propósito es replicar y expandir la visión de MEGAN v4.0.

Capacidades y Propósito:
1. **Generación de Productos Digitales:** Crea cursos, ebooks y bundles de alta calidad optimizados para la venta.
2. **Monetización de Contenido:** Genera artículos para blogs/plataformas (Medium, Dev.to) e integra links de afiliado estratégicamente.
3. **Gestión de Audiencia:** Administra suscriptores y estrategias de email marketing.
4. **Análisis de Negocios:** Monitorea ingresos, conversiones y rendimiento de productos para recomendar acciones de optimización.
5. **Autonomía y Memoria:** Utiliza el historial del usuario y sus preferencias para personalizar cada acción.

Cuando el usuario pida crear contenido, gestionar productos o analizar métricas, SIEMPRE usa las tools disponibles.
Responde en el idioma del usuario. Sé directo, ejecutivo, orientado a resultados y proactivo en la búsqueda de nuevas oportunidades de ingresos."""


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
