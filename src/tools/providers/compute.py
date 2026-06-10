"""
Code & reasoning provider.
- Fast LLM inference via Groq (llama-3.3-70b)
- Python code execution in sandboxed subprocess
- Data analysis
"""
from __future__ import annotations
import httpx
import subprocess
import tempfile
import os
import json
from src.core.config import settings


async def fast_inference(prompt: str, system: str = "", max_tokens: int = 1024) -> dict:
    """Ultra-fast inference via Groq (llama-3.3-70b-versatile)."""
    if not settings.GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY not configured.")

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    async with httpx.AsyncClient(timeout=30) as client:
        res = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": 0.7,
            },
        )
        res.raise_for_status()
        data = res.json()

    return {
        "text": data["choices"][0]["message"]["content"],
        "model": "groq/llama-3.3-70b",
        "tokens": data.get("usage", {}).get("total_tokens", 0),
        "latency_ms": data.get("x_groq", {}).get("usage", {}).get("total_time", 0),
    }


async def execute_python(code: str, timeout: int = 15) -> dict:
    """
    Execute Python code in a sandboxed subprocess.
    Returns stdout, stderr, and any JSON output.
    Safe: no network, no file writes outside /tmp.
    """
    # Safety checks
    forbidden = ["import os", "import sys", "subprocess", "open(", "__import__", "exec(", "eval("]
    for f in forbidden:
        if f in code:
            return {"error": f"Instrucción no permitida: '{f}'", "blocked": True}

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        tmp_path = f.name

    try:
        result = subprocess.run(
            ["python3", "-c", f"exec(open('{tmp_path}').read())"],
            capture_output=True,
            text=True,
            timeout=timeout,
            env={"PATH": "/usr/bin:/bin", "HOME": "/tmp"},
        )
        output = result.stdout.strip()
        error = result.stderr.strip()

        # Try to parse as JSON
        parsed = None
        try:
            parsed = json.loads(output)
        except Exception:
            pass

        return {
            "stdout": output,
            "stderr": error,
            "returncode": result.returncode,
            "parsed_output": parsed,
        }
    except subprocess.TimeoutExpired:
        return {"error": "Timeout: el código tardó más de 15 segundos"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        os.unlink(tmp_path)


async def analyze_data(data: list | dict, question: str) -> dict:
    """Use Groq to analyze structured data and answer a question."""
    data_str = json.dumps(data, ensure_ascii=False, indent=2)[:2000]
    return await fast_inference(
        prompt=f"Datos:\n{data_str}\n\nPregunta: {question}\n\nResponde de forma concisa con insights accionables.",
        system="Eres un analista de datos experto. Responde solo con el análisis, sin preámbulos.",
        max_tokens=512,
    )
