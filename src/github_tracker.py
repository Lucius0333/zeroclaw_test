"""Activity tracking modules for GitHub repositories."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.api_client import GitHubAPIClient, GitHubAPIError
from src.config import GitHubConfig


class CommitTracker:
    """Track and analyse repository commits."""

    def __init__(self, client: GitHubAPIClient, config: GitHubConfig):
        self.client = client
        self.config = config

    def recent_commits(self, per_page: int = 20) -> List[Dict[str, Any]]:
        """Fetch recent commits and return simplified records."""
        raw = self.client.get_commits(
            self.config.user, self.config.repo, per_page=per_page
        )
        return [
            {
                "sha": c["sha"][:7],
                "author": c["commit"]["author"].get("name", "Unknown"),
                "message": c["commit"]["message"].split("\n")[0],
                "date": c["commit"]["author"].get("date", ""),
            }
            for c in raw
        ]

    def commit_count_last_week(self) -> int:
        """Return total commits in the last 7 days from weekly stats."""
        try:
            weeks = self.client.get_commit_activity(
                self.config.user, self.config.repo
            )
            # GitHub returns last 52 weeks; last entry is most recent
            if weeks:
                return int(weeks[-1].get("total", 0))
        except GitHubAPIError:
            pass
        return 0


class PRTracker:
    """Monitor pull requests."""

    def __init__(self, client: GitHubAPIClient, config: GitHubConfig):
        self.client = client
        self.config = config

    def open_prs(self) -> List[Dict[str, Any]]:
        """List open pull requests."""
        raw = self.client.list_pull_requests(
            self.config.user, self.config.repo, state="open"
        )
        return [
            {
                "number": pr["number"],
                "title": pr["title"],
                "author": pr["user"]["login"],
                "created_at": pr["created_at"],
                "url": pr["html_url"],
            }
            for pr in raw
        ]

    def pr_summary(self) -> Dict[str, Any]:
        """Return a summary dict of PR activity."""
        open_prs = self.open_prs()
        return {
            "open_count": len(open_prs),
            "open_prs": open_prs,
        }


class IssueTracker:
    """Monitor repository issues."""

    def __init__(self, client: GitHubAPIClient, config: GitHubConfig):
        self.client = client
        self.config = config

    def open_issues(self) -> List[Dict[str, Any]]:
        """List open issues."""
        raw = self.client.list_issues(
            self.config.user, self.config.repo, state="open"
        )
        # Filter out PRs (GitHub issues endpoint includes them)
        issues = [i for i in raw if "pull_request" not in i]
        return [
            {
                "number": i["number"],
                "title": i["title"],
                "author": i["user"]["login"],
                "created_at": i["created_at"],
                "url": i["html_url"],
            }
            for i in issues
        ]


class ContributorStats:
    """Gather contributor statistics."""

    def __init__(self, client: GitHubAPIClient, config: GitHubConfig):
        self.client = client
        self.config = config

    def top_contributors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Return top contributors by commit count."""
        raw = self.client.get_contributors(
            self.config.user, self.config.repo, per_page=limit
        )
        return [
            {
                "login": c["login"],
                "contributions": c["contributions"],
                "url": c["html_url"],
            }
            for c in raw
        ]


class ActivityReport:
    """Generate comprehensive activity reports."""

    def __init__(self, config: GitHubConfig, client: GitHubAPIClient):
        self.config = config
        self.client = client
        self.commit_tracker = CommitTracker(client, config)
        self.pr_tracker = PRTracker(client, config)
        self.issue_tracker = IssueTracker(client, config)
        self.contributor_stats = ContributorStats(client, config)
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)

    def build(self) -> Dict[str, Any]:
        """Build a full activity report."""
        report: Dict[str, Any] = {
            "repository": self.config.repo_full_name(),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        # Commits
        try:
            report["recent_commits"] = self.commit_tracker.recent_commits()
            report["commits_last_week"] = (
                self.commit_tracker.commit_count_last_week()
            )
        except GitHubAPIError as e:
            report["commits_error"] = str(e)

        # Pull requests
        try:
            report["pull_requests"] = self.pr_tracker.pr_summary()
        except GitHubAPIError as e:
            report["pr_error"] = str(e)

        # Issues
        try:
            report["open_issues"] = self.issue_tracker.open_issues()
        except GitHubAPIError as e:
            report["issues_error"] = str(e)

        # Contributors
        try:
            report["top_contributors"] = (
                self.contributor_stats.top_contributors()
            )
        except GitHubAPIError as e:
            report["contributors_error"] = str(e)

        return report

    def save(self, report: Dict[str, Any]) -> str:
        """Save report to data directory and return filepath."""
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filepath = self.data_dir / f"report_{ts}.json"
        with open(filepath, "w") as f:
            json.dump(report, f, indent=2)
        return str(filepath)


class GitHubTracker:
    """Legacy tracker for backward compatibility."""

    def __init__(self, token: str, owner: str, repo: str):
        self.token = token
        self.owner = owner
        self.repo = repo
        self.base_url = "https://api.github.com"
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)

    def get_repo_info(self) -> dict:
        """Fetch basic repository information."""
        return {
            "owner": self.owner,
            "repo": self.repo,
            "tracked_at": datetime.utcnow().isoformat()
        }

    def save_report(self, report: dict) -> str:
        """Save a report to the data directory."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filepath = self.data_dir / f"report_{timestamp}.json"
        with open(filepath, "w") as f:
            json.dump(report, f, indent=2)
        return str(filepath)

    def generate_report(self) -> dict:
        """Generate a comprehensive activity report."""
        report = self.get_repo_info()
        report["status"] = "tracking_initialized"
        report["modules"] = [
            "github_tracker",
            "report_generator",
            "scheduler"
        ]
        filepath = self.save_report(report)
        report["report_file"] = filepath
        return report


def main():
    """Entry point — generate and print an activity report."""
    config = GitHubConfig()
    if not config.is_valid():
        print("Error: GITHUB_TOKEN, GITHUB_USER, and GITHUB_REPO are required.")
        return

    client = GitHubAPIClient(config.token)
    report_gen = ActivityReport(config, client)
    report = report_gen.build()
    filepath = report_gen.save(report)

    print(json.dumps(report, indent=2))
    print(f"\nReport saved to: {filepath}")
