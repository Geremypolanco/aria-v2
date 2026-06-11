import logging
import os
from typing import Any, Dict, AsyncGenerator
import anthropic
from src.agents.base_v3 import BaseAgentV3

logger = logging.getLogger(__name__)

class ResearchAgent(BaseAgentV3):
    """
    ResearchAgent - Analisis profundo y research con Claude.
    Descompone preguntas complejas, sintetiza informacion, genera reportes.
    Playwright headless disponible en sandbox para scraping real.
    """

    def __init__(self):
        super().__init__(name="ResearchAgent", model="claude-sonnet-4-20250514")
        self.client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    async def execute(self, task: str, context: Dict[str, Any] = None) -> AsyncGenerator[str, None]:
        context = context or {}
        depth = context.get("depth", "medium")
        logger.info(f"{self.name} researching: {task[:80]}")

        yield f"data: [ResearchAgent] Iniciando research: {task[:60]}...\n\n"

        # Step 1: Generate sub-queries
        yield f"data: [ResearchAgent] Generando sub-queries...\n\n"
        queries_response = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            system="Genera 5 sub-preguntas especificas para investigar el tema. Una por linea, sin numeros.",
            messages=[{"role": "user", "content": f"Tema: {task}"}]
        )
        sub_queries = queries_response.content[0].text
        yield f"data: [ResearchAgent] Sub-queries generadas:\n{sub_queries}\n\n"

        # Step 2: Deep analysis
        yield f"data: [ResearchAgent] Analizando en profundidad (depth={depth})...\n\n"
        system_prompt = """Eres un analista de mercado y negocios digitales de nivel experto.
Genera analisis profundos con datos reales, tendencias 2025-2026, oportunidades y recomendaciones accionables.
Estructura: resumen ejecutivo, hallazgos clave, datos de mercado, oportunidades, riesgos, recomendaciones."""

        with self.client.messages.stream(
            model=self.model,
            max_tokens=3000,
            system=system_prompt,
            messages=[{
                "role": "user",
                "content": f"Investiga en profundidad: {task}\nSub-aspectos a cubrir:\n{sub_queries}"
            }]
        ) as stream:
            for text in stream.text_stream:
                yield f"data: {text}\n\n"

        yield f"data: [ResearchAgent] Research completado.\n\n"
