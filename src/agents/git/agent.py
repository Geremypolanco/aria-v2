import logging
import os
import base64
import requests
from typing import Any, Dict, AsyncGenerator
from src.agents.base_v3 import BaseAgentV3

logger = logging.getLogger(__name__)

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_OWNER = os.environ.get("GITHUB_OWNER", "")

class GitAgent(BaseAgentV3):
    """
    GitAgent - GitHub nativo completo.
    Crea repos, branches, commits, PRs. Deploy automatico a Vercel.
    Diferenciador: Aria puede tomar un issue y entregar el PR resuelto.
    """

    def __init__(self):
        super().__init__(name="GitAgent", model="claude-sonnet-4-20250514")
        self.token = GITHUB_TOKEN
        self.owner = GITHUB_OWNER
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

    def _req(self, method: str, endpoint: str, data: dict = None) -> dict:
        url = f"{self.base_url}{endpoint}"
        res = requests.request(method, url, headers=self.headers, json=data, timeout=30)
        res.raise_for_status()
        return res.json() if res.content else {}

    def create_repo(self, name: str, private: bool = True, description: str = "") -> dict:
        return self._req("POST", "/user/repos", {
            "name": name, "private": private,
            "description": description, "auto_init": True
        })

    def create_or_update_file(self, repo: str, path: str, content: str, message: str, branch: str = "main") -> dict:
        encoded = base64.b64encode(content.encode()).decode()
        body = {"message": message, "content": encoded, "branch": branch}
        try:
            existing = self._req("GET", f"/repos/{self.owner}/{repo}/contents/{path}?ref={branch}")
            body["sha"] = existing["sha"]
        except Exception:
            pass
        return self._req("PUT", f"/repos/{self.owner}/{repo}/contents/{path}", body)

    def create_branch(self, repo: str, branch_name: str, from_branch: str = "main") -> dict:
        ref = self._req("GET", f"/repos/{self.owner}/{repo}/git/ref/heads/{from_branch}")
        sha = ref["object"]["sha"]
        return self._req("POST", f"/repos/{self.owner}/{repo}/git/refs", {
            "ref": f"refs/heads/{branch_name}", "sha": sha
        })

    def create_pull_request(self, repo: str, title: str, body: str, head: str, base: str = "main") -> dict:
        return self._req("POST", f"/repos/{self.owner}/{repo}/pulls", {
            "title": title, "body": body, "head": head, "base": base
        })

    def get_issues(self, repo: str, state: str = "open") -> list:
        return self._req("GET", f"/repos/{self.owner}/{repo}/issues?state={state}")

    async def execute(self, task: str, context: Dict[str, Any] = None) -> AsyncGenerator[str, None]:
        context = context or {}
        action = context.get("action", "info")
        repo = context.get("repo", "")
        logger.info(f"{self.name} executing action={action} repo={repo}")

        yield f"data: [GitAgent] Ejecutando: {action} en {repo or 'N/A'}\n\n"

        try:
            if action == "create_repo":
                result = self.create_repo(repo, context.get("private", True), context.get("description", ""))
                yield f"data: [GitAgent] Repo creado: {result.get('html_url', '')}\n\n"

            elif action == "commit":
                path = context.get("path", "README.md")
                content = context.get("content", "")
                message = context.get("message", f"feat: update {path}")
                result = self.create_or_update_file(repo, path, content, message)
                commit_sha = result.get("commit", {}).get("sha", "")[:7]
                yield f"data: [GitAgent] Commit {commit_sha}: {message}\n\n"

            elif action == "create_branch":
                branch = context.get("branch_name", "feature/aria")
                self.create_branch(repo, branch)
                yield f"data: [GitAgent] Branch creado: {branch}\n\n"

            elif action == "create_pr":
                pr = self.create_pull_request(
                    repo, context.get("title", "Aria PR"),
                    context.get("body", ""), context.get("head", "main")
                )
                yield f"data: [GitAgent] PR creado: {pr.get('html_url', '')}\n\n"

            elif action == "list_issues":
                issues = self.get_issues(repo)
                yield f"data: [GitAgent] {len(issues)} issues abiertos en {repo}\n\n"
                for issue in issues[:5]:
                    yield f"data: #{issue['number']}: {issue['title']}\n\n"

            else:
                yield f"data: [GitAgent] Accion desconocida: {action}\n\n"

        except Exception as e:
            logger.error(f"GitAgent error: {e}")
            yield f"data: [GitAgent] ERROR: {str(e)}\n\n"
