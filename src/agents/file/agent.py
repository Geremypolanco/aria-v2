import logging
import os
import zipfile
import tempfile
from typing import Any, Dict, AsyncGenerator
from src.agents.base_v3 import BaseAgentV3

logger = logging.getLogger(__name__)

class FileAgent(BaseAgentV3):
    """
    FileAgent - Gestor real de archivos.
    Crea, lee, modifica, empaqueta archivos. Genera ZIPs listos para descarga.
    Diferenciador: entrega archivos reales, no solo texto.
    """

    def __init__(self):
        super().__init__(name="FileAgent", model="claude-sonnet-4-20250514")
        self.workspace = tempfile.mkdtemp(prefix="aria_files_")

    def create_file(self, filename: str, content: str, subfolder: str = "") -> dict:
        folder = os.path.join(self.workspace, subfolder) if subfolder else self.workspace
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return {"path": path, "size": os.path.getsize(path), "filename": filename}

    def read_file(self, filename: str) -> dict:
        path = os.path.join(self.workspace, filename)
        if not os.path.exists(path):
            return {"error": f"File not found: {filename}"}
        with open(path, "r", encoding="utf-8") as f:
            return {"content": f.read(), "size": os.path.getsize(path)}

    def create_zip(self, files: dict, zip_name: str) -> dict:
        zip_path = os.path.join(self.workspace, zip_name)
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for fname, content in files.items():
                zf.writestr(fname, content)
        return {"path": zip_path, "size": os.path.getsize(zip_path), "files": list(files.keys())}

    def list_workspace(self) -> list:
        result = []
        for root, dirs, filenames in os.walk(self.workspace):
            for fname in filenames:
                path = os.path.join(root, fname)
                rel = os.path.relpath(path, self.workspace)
                result.append({"name": fname, "path": rel, "size": os.path.getsize(path)})
        return result

    def generate_markdown_pdf_content(self, title: str, content: str) -> str:
        """Genera HTML listo para convertir a PDF via weasyprint o puppeteer."""
        return f"""<!DOCTYPE html>
<html lang='es'>
<head>
<meta charset='UTF-8'>
<style>
  body {{ font-family: Georgia, serif; max-width: 800px; margin: 0 auto; padding: 40px; color: #1a1a1a; line-height: 1.7; }}
  h1 {{ color: #1a1a2e; border-bottom: 2px solid #7c6aff; padding-bottom: 10px; }}
  h2 {{ color: #16213e; margin-top: 40px; }}
  h3 {{ color: #0f3460; }}
  code {{ background: #f4f4f8; padding: 2px 6px; border-radius: 3px; font-family: monospace; }}
  pre {{ background: #f4f4f8; padding: 16px; border-radius: 6px; overflow-x: auto; }}
  blockquote {{ border-left: 4px solid #7c6aff; padding-left: 16px; color: #555; margin: 20px 0; }}
</style>
</head>
<body>
<h1>{title}</h1>
{content}
</body>
</html>"""

    async def execute(self, task: str, context: Dict[str, Any] = None) -> AsyncGenerator[str, None]:
        context = context or {}
        action = context.get("action", "create")
        logger.info(f"{self.name} action={action}: {task[:60]}")

        yield f"data: [FileAgent] Ejecutando: {action}\n\n"

        try:
            if action == "create":
                result = self.create_file(
                    context.get("filename", "output.txt"),
                    context.get("content", ""),
                    context.get("subfolder", "")
                )
                yield f"data: [FileAgent] Archivo creado: {result['filename']} ({result['size']} bytes)\n\n"

            elif action == "zip":
                result = self.create_zip(context.get("files", {}), context.get("zip_name", "output.zip"))
                yield f"data: [FileAgent] ZIP creado con {len(result['files'])} archivos ({result['size']} bytes)\n\n"
                for f in result["files"]:
                    yield f"data:   - {f}\n\n"

            elif action == "read":
                result = self.read_file(context.get("filename", ""))
                if "error" in result:
                    yield f"data: [FileAgent] ERROR: {result['error']}\n\n"
                else:
                    yield f"data: [FileAgent] Archivo leido ({result['size']} bytes):\n{result['content'][:500]}...\n\n"

            elif action == "list":
                files = self.list_workspace()
                yield f"data: [FileAgent] {len(files)} archivos en workspace:\n\n"
                for f in files:
                    yield f"data:   {f['path']} ({f['size']} bytes)\n\n"

            elif action == "generate_pdf_html":
                html = self.generate_markdown_pdf_content(
                    context.get("title", task),
                    context.get("content", "")
                )
                result = self.create_file(context.get("filename", "document.html"), html)
                yield f"data: [FileAgent] HTML para PDF generado: {result['filename']}\n\n"

            else:
                yield f"data: [FileAgent] Accion desconocida: {action}\n\n"

        except Exception as e:
            logger.error(f"FileAgent error: {e}")
            yield f"data: [FileAgent] ERROR: {str(e)}\n\n"
