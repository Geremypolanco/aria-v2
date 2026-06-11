import logging
import os
from typing import Any, Dict, AsyncGenerator
import anthropic
from src.agents.base_v3 import BaseAgentV3

logger = logging.getLogger(__name__)

class WriterAgent(BaseAgentV3):
    """
    WriterAgent - Creador de infoproductos completos.
    Ebooks, cursos, landing pages, emails, scripts de contenido.
    Output listo para produccion, no borradores.
    """

    def __init__(self):
        super().__init__(name="WriterAgent", model="claude-sonnet-4-20250514")
        self.client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    async def execute(self, task: str, context: Dict[str, Any] = None) -> AsyncGenerator[str, None]:
        context = context or {}
        content_type = context.get("type", "ebook")
        logger.info(f"{self.name} creating {content_type}: {task[:60]}")

        yield f"data: [WriterAgent] Creando {content_type}: {task[:50]}...\n\n"

        if content_type == "landing_page":
            async for chunk in self._generate_landing_page(task, context):
                yield chunk
        elif content_type == "email_sequence":
            async for chunk in self._generate_email_sequence(task, context):
                yield chunk
        elif content_type == "script":
            async for chunk in self._generate_script(task, context):
                yield chunk
        else:
            async for chunk in self._generate_ebook(task, context):
                yield chunk

    async def _generate_ebook(self, task: str, context: dict) -> AsyncGenerator[str, None]:
        audience = context.get("audience", "emprendedores digitales")
        yield f"data: [WriterAgent] Generando outline del ebook...\n\n"

        outline_response = self.client.messages.create(
            model=self.model, max_tokens=800,
            system="Eres experto en infoproductos. Crea outlines detallados con 7-10 capitulos. Formato markdown.",
            messages=[{"role": "user", "content": f"Outline para ebook: '{task}'. Audiencia: {audience}"}]
        )
        outline = outline_response.content[0].text
        yield f"data: [WriterAgent] Outline listo. Escribiendo contenido completo...\n\n"

        with self.client.messages.stream(
            model=self.model, max_tokens=4000,
            system="""Eres un escritor experto en negocios digitales y marketing.
Escribe contenido profundo, practico y bien estructurado en markdown.
Cada capitulo debe tener: introduccion, contenido principal, ejemplos reales, ejercicio practico y resumen.
El tono es directo, sin relleno, orientado a resultados.""",
            messages=[{"role": "user", "content": f"Escribe el ebook completo basado en este outline:\n{outline}\nAudiencia: {audience}"}]
        ) as stream:
            for text in stream.text_stream:
                yield f"data: {text}\n\n"

        yield f"data: [WriterAgent] Ebook completado.\n\n"

    async def _generate_landing_page(self, task: str, context: dict) -> AsyncGenerator[str, None]:
        price = context.get("price", "")
        yield f"data: [WriterAgent] Generando landing page HTML...\n\n"

        with self.client.messages.stream(
            model=self.model, max_tokens=4000,
            system="""Eres experto en copywriting y desarrollo web.
Genera landing pages en HTML/CSS/JS completas, responsivas y optimizadas para conversion.
Incluye: hero section con CTA, beneficios, testimonios, precio, FAQ, footer.
Dark mode elegante. Responde SOLO con el HTML completo.""",
            messages=[{"role": "user", "content": f"Landing page para: {task}. Precio: {price}"}]
        ) as stream:
            for text in stream.text_stream:
                yield f"data: {text}\n\n"

        yield f"data: [WriterAgent] Landing page completada.\n\n"

    async def _generate_email_sequence(self, task: str, context: dict) -> AsyncGenerator[str, None]:
        days = context.get("days", 5)
        yield f"data: [WriterAgent] Generando secuencia de {days} emails...\n\n"

        with self.client.messages.stream(
            model=self.model, max_tokens=3000,
            system="""Eres experto en email marketing de alta conversion.
Genera secuencias de emails que construyen relacion, demuestran valor y convierten.
Cada email incluye: asunto (con emoji), preview text, cuerpo en HTML con CTA claro.""",
            messages=[{"role": "user", "content": f"Secuencia de {days} emails para: {task}"}]
        ) as stream:
            for text in stream.text_stream:
                yield f"data: {text}\n\n"

        yield f"data: [WriterAgent] Secuencia de emails completada.\n\n"

    async def _generate_script(self, task: str, context: dict) -> AsyncGenerator[str, None]:
        platform = context.get("platform", "youtube")
        yield f"data: [WriterAgent] Generando script para {platform}...\n\n"

        with self.client.messages.stream(
            model=self.model, max_tokens=2000,
            system=f"""Eres experto en contenido para {platform}.
Genera scripts virales con hooks fuertes, estructura clara y CTAs efectivos.
Incluye: hook (primeros 3 segundos), desarrollo, CTA. Tono: directo y energico.""",
            messages=[{"role": "user", "content": f"Script {platform}: {task}"}]
        ) as stream:
            for text in stream.text_stream:
                yield f"data: {text}\n\n"

        yield f"data: [WriterAgent] Script completado.\n\n"
