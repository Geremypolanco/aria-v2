import logging
import os
import json
from datetime import datetime
from typing import Any, Dict, List, AsyncGenerator
import anthropic
from src.agents.base_v3 import BaseAgentV3

logger = logging.getLogger(__name__)

class MemoryAgent(BaseAgentV3):
    """
    MemoryAgent - Memoria persistente de Aria.
    Corto plazo: contexto conversacion activa.
    Largo plazo: perfil usuario, proyectos, preferencias (pgvector via Supabase).
    Diferenciador: Aria te recuerda, aprende de ti, no empieza de cero.
    """

    def __init__(self, supabase_client=None):
        super().__init__(name="MemoryAgent", model="claude-sonnet-4-20250514")
        self.client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        self.supabase = supabase_client
        self.short_term: List[dict] = []
        self.user_profile: dict = {}
        self.session_summary: str = ""

    def add_message(self, role: str, content: str):
        """Agrega mensaje al contexto de corto plazo."""
        self.short_term.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        # Keep only last 50 messages in short-term
        if len(self.short_term) > 50:
            self.short_term = self.short_term[-50:]

    def get_context(self, max_messages: int = 20) -> List[dict]:
        """Retorna contexto formateado para la API de Claude."""
        return [
            {"role": m["role"], "content": m["content"]}
            for m in self.short_term[-max_messages:]
        ]

    def update_profile(self, data: dict):
        """Actualiza el perfil del usuario con nuevos datos aprendidos."""
        self.user_profile.update(data)
        if self.supabase:
            try:
                self.supabase.table("user_profiles").upsert({
                    **self.user_profile,
                    "updated_at": datetime.now().isoformat()
                }).execute()
            except Exception as e:
                logger.error(f"Error saving profile to Supabase: {e}")

    def extract_preferences(self) -> dict:
        """Extrae preferencias del usuario de la conversacion actual."""
        if len(self.short_term) < 4:
            return {}
        recent = self.short_term[-10:]
        response = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            system="""Analiza esta conversacion y extrae datos del usuario.
Devuelve JSON con: nombre, objetivos, nichos_interes, estilo_comunicacion, proyectos_mencionados.
Solo incluye campos que puedas inferir con confianza.""",
            messages=[{"role": "user", "content": f"Conversacion:\n{json.dumps(recent)}"}]
        )
        try:
            text = response.content[0].text
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(text[start:end])
        except Exception:
            pass
        return {}

    def recall(self, query: str) -> str:
        """Busca en memoria del usuario informacion relevante para la query."""
        if not self.user_profile and not self.session_summary:
            return "No tengo memoria previa de este usuario en esta sesion."
        response = self.client.messages.create(
            model=self.model,
            max_tokens=400,
            system="Eres la memoria de Aria. Resume que recuerdas relevante para la query del usuario.",
            messages=[{"role": "user", "content": f"Query: {query}\nPerfil: {json.dumps(self.user_profile)}\nResumen sesion: {self.session_summary}"}]
        )
        return response.content[0].text

    def summarize_session(self):
        """Genera un resumen de la sesion actual para memoria de largo plazo."""
        if len(self.short_term) < 2:
            return
        response = self.client.messages.create(
            model=self.model,
            max_tokens=300,
            system="Resume en 3-5 puntos clave lo que se discutio y logro en esta sesion.",
            messages=[{"role": "user", "content": f"Sesion:\n{json.dumps(self.short_term[-20:])}"}]
        )
        self.session_summary = response.content[0].text
        return self.session_summary

    async def execute(self, task: str, context: Dict[str, Any] = None) -> AsyncGenerator[str, None]:
        context = context or {}
        action = context.get("action", "recall")
        logger.info(f"{self.name} action={action}")

        if action == "recall":
            memory = self.recall(context.get("query", task))
            yield f"data: [MemoryAgent] Recuerdo relevante:\n{memory}\n\n"

        elif action == "update_profile":
            preferences = self.extract_preferences()
            if preferences:
                self.update_profile(preferences)
                yield f"data: [MemoryAgent] Perfil actualizado: {json.dumps(preferences)}\n\n"
            else:
                yield f"data: [MemoryAgent] No se detectaron nuevas preferencias.\n\n"

        elif action == "summarize":
            summary = self.summarize_session()
            yield f"data: [MemoryAgent] Resumen de sesion:\n{summary}\n\n"

        elif action == "get_profile":
            yield f"data: [MemoryAgent] Perfil actual:\n{json.dumps(self.user_profile, indent=2)}\n\n"

        else:
            yield f"data: [MemoryAgent] Accion desconocida: {action}\n\n"
