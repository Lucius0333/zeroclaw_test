"""GitHub API client for the Activity Tracker.

Uses urllib.request (stdlib) to avoid external dependencies.
"""

import json
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional


class GitHubAPIClient:
    """HTTP client for GitHub REST API v3."""

    API_VERSION = "2022-11-28"

    def __init__(self, token: str):
        """Initialize API client.

        Args:
            token: GitHub Personal Access Token.
        """
        self.token = token
        self.base_url = "https://api.github.com"

    def _request(
        self,
        endpoint: str,
        params: Optional[Dict[str, str]] = None,
    ) -> Any:
        """Make an authenticated GET request to GitHub API.

        Args:
            endpoint: API path (e.g. '/repos/owner/repo/commits').
            params: Optional query parameters.

        Returns:
            Parsed JSON response.

        Raises:
            GitHubAPIError: On HTTP error responses.
        """
        url = f"{self.base_url}{endpoint}"
        if params:
            query = "&".join(f"{k}={v}" for k, v in params.items())
            url = f"{url}?{query}"

        req = urllib.request.Request(url)
        req.add_header("Authorization", f"Bearer {self.token}")
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("X-GitHub-Api-Version", self.API_VERSION)
        req.add_header("User-Agent", "ZeroClaw-Activity-Tracker")

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = e.read().decode("utf-8")
            except Exception:
                pass
            raise GitHubAPIError(
                status=e.code,
                url=url,
                message=body,
            ) from e
        except urllib.error.URLError as e:
            raise GitHubAPIError(
                status=0,
                url=url,
                message=str(e.reason),
            ) from e

    # ---- Repository endpoints ----

    def get_repo(self, owner: str, repo: str) -> Dict:
        """Fetch repository metadata."""
        return self._request(f"/repos/{owner}/{repo}")

    def get_commits(
        self,
        owner: str,
        repo: str,
        per_page: int = 30,
        page: int = 1,
    ) -> List[Dict]:
        """List repository commits."""
        return self._request(
            f"/repos/{owner}/{repo}/commits",
            params={"per_page": str(per_page), "page": str(page)},
        )

    def get_commit(self, owner: str, repo: str, sha: str) -> Dict:
        """Get a single commit by SHA."""
        return self._request(f"/repos/{owner}/{repo}/commits/{sha}")

    # ---- Pull Request endpoints ----

    def list_pull_requests(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        per_page: int = 30,
    ) -> List[Dict]:
        """List pull requests."""
        return self._request(
            f"/repos/{owner}/{repo}/pulls",
            params={"state": state, "per_page": str(per_page)},
        )

    def get_pull_request(
        self, owner: str, repo: str, pr_number: int
    ) -> Dict:
        """Get a single pull request."""
        return self._request(f"/repos/{owner}/{repo}/pulls/{pr_number}")

    # ---- Issue endpoints ----

    def list_issues(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        per_page: int = 30,
    ) -> List[Dict]:
        """List issues (includes pull requests; filter as needed)."""
        return self._request(
            f"/repos/{owner}/{repo}/issues",
            params={"state": state, "per_page": str(per_page)},
        )

    # ---- Contributor / Stats endpoints ----

    def get_contributors(
        self, owner: str, repo: str, per_page: int = 30
    ) -> List[Dict]:
        """List repository contributors."""
        return self._request(
            f"/repos/{owner}/{repo}/contributors",
            params={"per_page": str(per_page)},
        )

    def get_commit_activity(
        self, owner: str, repo: str
    ) -> List[Dict]:
        """Get the last year of commit activity (weekly)."""
        return self._request(f"/repos/{owner}/{repo}/stats/commit_activity")

    # ---- Rate limit ----

    def get_rate_limit(self) -> Dict:
        """Check current API rate limit status."""
        return self._request("/rate_limit")


class GitHubAPIError(Exception):
    """Raised when the GitHub API returns an error."""

    def __init__(self, status: int, url: str, message: str):
        self.status = status
        self.url = url
        self.message = message
        super().__init__(
            f"GitHub API error {status} on {url}: {message}"
        )
