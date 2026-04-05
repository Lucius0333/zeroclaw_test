"""Configuration loader for GitHub Activity Tracker."""

import os
from pathlib import Path
from typing import Optional


class GitHubConfig:
    """Load and manage GitHub API configuration."""

    def __init__(self, env_path: Optional[str] = None):
        """Initialize config from .env.github file or environment.

        Args:
            env_path: Path to .env.github file. If None, searches workspace root.
        """
        self.token: str = ""
        self.user: str = ""
        self.repo: str = ""
        self.base_url: str = "https://api.github.com"

        self._load(env_path)

    def _load(self, env_path: Optional[str]) -> None:
        """Parse .env.github file and populate config."""
        if env_path is None:
            workspace = Path("/zeroclaw-data/workspace")
            env_path_obj = workspace / ".env.github"
        else:
            env_path_obj = Path(env_path)

        if env_path_obj.exists():
            self._parse_env_file(env_path_obj)

        # Environment variables override file values
        self.token = os.environ.get("GITHUB_TOKEN", self.token)
        self.user = os.environ.get("GITHUB_USER", self.user)
        self.repo = os.environ.get("GITHUB_REPO", self.repo)

    def _parse_env_file(self, path: Path) -> None:
        """Parse key=value pairs from env file."""
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip()
                if key == "GITHUB_TOKEN":
                    self.token = value
                elif key == "GITHUB_USER":
                    self.user = value
                elif key == "GITHUB_REPO":
                    self.repo = value

    def is_valid(self) -> bool:
        """Check if required config is present."""
        return bool(self.token and self.user and self.repo)

    def repo_full_name(self) -> str:
        """Return owner/repo format."""
        return f"{self.user}/{self.repo}"
