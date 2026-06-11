import subprocess
import logging
import os
import uuid
import shutil
from typing import Dict, Any

logger = logging.getLogger(__name__)

class SandboxExecutor:
    """
    ARIA v3 Sandbox Executor
    Isolated environment for Python, Node, and Bash execution.
    """
    def __init__(self, base_workspace="/tmp/aria_workspace"):
        self.base_workspace = base_workspace
        if not os.path.exists(self.base_workspace):
            os.makedirs(self.base_workspace)

    def _get_session_dir(self):
        session_id = str(uuid.uuid4())
        session_dir = os.path.join(self.base_workspace, session_id)
        os.makedirs(session_dir)
        return session_dir

    def run(self, command: list, cwd: str, timeout: int = 30) -> Dict[str, Any]:
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd,
                env={"PATH": os.environ.get("PATH", "")} # Basic isolation
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
                "success": result.returncode == 0
            }
        except subprocess.TimeoutExpired:
            return {"error": "Execution timed out (30s limit)", "success": False}
        except Exception as e:
            return {"error": str(e), "success": False}

    def execute_python(self, code: str):
        session_dir = self._get_session_dir()
        file_path = os.path.join(session_dir, "script.py")
        with open(file_path, "w") as f:
            f.write(code)
        
        result = self.run(["python3", "script.py"], cwd=session_dir)
        shutil.rmtree(session_dir)
        return result

    def execute_node(self, code: str):
        session_dir = self._get_session_dir()
        file_path = os.path.join(session_dir, "index.js")
        with open(file_path, "w") as f:
            f.write(code)
        
        result = self.run(["node", "index.js"], cwd=session_dir)
        shutil.rmtree(session_dir)
        return result

    def execute_bash(self, script: str):
        session_dir = self._get_session_dir()
        file_path = os.path.join(session_dir, "run.sh")
        with open(file_path, "w") as f:
            f.write(script)
        
        os.chmod(file_path, 0o755)
        result = self.run(["bash", "run.sh"], cwd=session_dir)
        shutil.rmtree(session_dir)
        return result

sandbox = SandboxExecutor()
