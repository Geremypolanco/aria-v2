import logging
import os
import subprocess
import tempfile
from typing import Any, Dict, AsyncGenerator
import anthropic
from src.agents.base_v3 import BaseAgentV3

logger = logging.getLogger(__name__)

class CodeAgent(BaseAgentV3):
    """
    CodeAgent - Self-testing loop como Replit Agent 3.
    Ciclo: escribir -> ejecutar -> analizar output -> corregir -> re-ejecutar
    No para hasta que el codigo pasa o se agotan los intentos.
    """

    def __init__(self):
        super().__init__(name="CodeAgent", model="claude-sonnet-4-20250514")
        self.client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        self.max_iterations = 5
        self.workspace = tempfile.mkdtemp(prefix="aria_code_")

    def _execute_code(self, code: str, language: str = "python") -> dict:
        suffix = ".py" if language == "python" else ".js"
        cmd = ["python3"] if language == "python" else ["node"]
        with tempfile.NamedTemporaryFile(mode="w", suffix=suffix, dir=self.workspace, delete=False) as f:
            f.write(code)
            path = f.name
        try:
            result = subprocess.run(cmd + [path], capture_output=True, text=True, timeout=30)
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout[:5000],
                "stderr": result.stderr[:2000],
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "stdout": "", "stderr": "Timeout: 30s exceeded", "returncode": -1}
        except Exception as e:
            return {"success": False, "stdout": "", "stderr": str(e), "returncode": -1}
        finally:
            try:
                os.unlink(path)
            except Exception:
                pass

    async def execute(self, task: str, context: Dict[str, Any] = None) -> AsyncGenerator[str, None]:
        context = context or {}
        language = context.get("language", "python")
        logger.info(f"{self.name} starting self-testing loop for: {task[:80]}")

        yield f"data: [CodeAgent] Generando codigo para: {task[:60]}...\n\n"

        # Generate initial code
        gen_response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            system=f"Eres un experto en {language}. Genera codigo limpio y funcional. Responde SOLO con el codigo, sin markdown ni explicaciones.",
            messages=[{"role": "user", "content": task}]
        )
        code = gen_response.content[0].text
        yield f"data: [CodeAgent] Codigo generado ({len(code)} chars). Ejecutando...\n\n"

        for i in range(self.max_iterations):
            result = self._execute_code(code, language)
            if result["success"]:
                yield f"data: [CodeAgent] Exito en iteracion {i+1}\n\n"
                yield f"data: OUTPUT:\n{result['stdout']}\n\n"
                yield f"data: [CodeAgent] CODIGO FINAL:\n{code}\n\n"
                return

            yield f"data: [CodeAgent] Error en iter {i+1}: {result['stderr'][:200]}. Corrigiendo...\n\n"

            fix_response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                system="Eres un experto debugger. Corrige el error y devuelve SOLO el codigo corregido sin markdown.",
                messages=[{
                    "role": "user",
                    "content": f"Codigo:\n{code}\n\nError:\n{result['stderr']}\n\nCorrige el codigo."
                }]
            )
            code = fix_response.content[0].text

        yield f"data: [CodeAgent] Max iteraciones alcanzadas ({self.max_iterations}). Ultimo codigo:\n{code}\n\n"
