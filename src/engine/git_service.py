import os
import subprocess
from pathlib import Path
from typing import Optional, List

from git import Repo, GitCommandError


class GitService:
    """
    High-level Git API wrapper built on top of GitPython.
    Designed for automation workflows (e.g., auto regression after commit).
    """

    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.repo: Optional[Repo] = None

        if self.repo_path.exists():
            try:
                self.repo = Repo(self.repo_path)
            except Exception:
                self.repo = None

    # ---------------------------
    # Core Git Operations
    # ---------------------------

    def clone(self, repo_url: str, branch: str = "main"):
        if self.repo_path.exists():
            raise FileExistsError(f"Path {self.repo_path} already exists.")

        self.repo = Repo.clone_from(repo_url, self.repo_path, branch=branch)
        return self.repo

    def pull(self):
        self._ensure_repo()
        origin = self.repo.remotes.origin
        return origin.pull()

    def checkout(self, branch: str):
        self._ensure_repo()
        return self.repo.git.checkout(branch)

    def reset(self, mode: str = "--hard", target: str = "HEAD"):
        """
        mode: --soft | --mixed | --hard
        """
        self._ensure_repo()
        return self.repo.git.reset(mode, target)

    def add_all(self):
        self._ensure_repo()
        self.repo.git.add(A=True)

    def commit(self, message: str):
        self._ensure_repo()
        return self.repo.index.commit(message)

    def push(self, branch: str = "main"):
        self._ensure_repo()
        origin = self.repo.remotes.origin
        return origin.push(branch)

    def current_commit(self) -> str:
        self._ensure_repo()
        return self.repo.head.commit.hexsha

    # ---------------------------
    # Test Execution
    # ---------------------------

    def run_python_test(self, test_file: str) -> subprocess.CompletedProcess:
        """
        Executes a python test file.
        """
        test_path = self.repo_path / test_file

        if not test_path.exists():
            raise FileNotFoundError(f"{test_file} not found")

        return subprocess.run(
            ["python", str(test_path)],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
        )

    def run_pytest(self, extra_args: Optional[List[str]] = None):
        """
        Runs pytest in the repo directory.
        """
        cmd = ["pytest"]
        if extra_args:
            cmd.extend(extra_args)

        return subprocess.run(cmd, cwd=self.repo_path, capture_output=True, text=True)

    # ---------------------------
    # Automation Flow
    # ---------------------------

    def clone_and_test(self, repo_url: str, branch: str = "main"):
        """
        Full automation flow:
        - Clone
        - Checkout branch
        - Run pytest
        """
        self.clone(repo_url, branch)
        result = self.run_pytest()

        return {
            "commit": self.current_commit(),
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

    # ---------------------------
    # Utilities
    # ---------------------------

    def _ensure_repo(self):
        if not self.repo:
            raise RuntimeError("Repository is not initialized.")


if __name__ == "__main__":
    path = Path(r"C:/abc_clone")
    git_service = GitService(str(path))
    git_service.reset()
    pass
