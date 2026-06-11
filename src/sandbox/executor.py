import subprocess
import logging

logger = logging.getLogger(__name__)

class SandboxExecutor:
    """
    Executes code in a controlled environment.
    """
    def execute_python(self, code: str):
        logger.info("Executing python code in sandbox")
        try:
            result = subprocess.run(
                ["python3", "-c", code],
                capture_output=True,
                text=True,
                timeout=30
            )
            return {"stdout": result.stdout, "stderr": result.stderr, "exit_code": result.returncode}
        except Exception as e:
            return {"error": str(e)}

sandbox = SandboxExecutor()
