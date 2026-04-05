"""Tests for GitHub Activity Tracker modules."""

import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure src is importable
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import GitHubConfig
from api_client import GitHubAPIClient, GitHubAPIError
from github_tracker import (
    CommitTracker,
    PRTracker,
    IssueTracker,
    ContributorStats,
    ActivityReport,
)


# ---------------------------------------------------------------------------
# Config tests
# ---------------------------------------------------------------------------

class TestGitHubConfig(unittest.TestCase):
    def test_parse_env_file(self):
        """Config correctly parses a .env.github file."""
        tmp = Path("/tmp/test_env_github")
        tmp.write_text(
            "# Comment line\n"
            "GITHUB_TOKEN=ghp_testtoken123\n"
            "GITHUB_USER=testuser\n"
            "GITHUB_REPO=testrepo\n"
        )
        cfg = GitHubConfig(str(tmp))
        self.assertEqual(cfg.token, "ghp_testtoken123")
        self.assertEqual(cfg.user, "testuser")
        self.assertEqual(cfg.repo, "testrepo")
        tmp.unlink()

    def test_is_valid(self):
        """is_valid returns True when all fields are set."""
        cfg = GitHubConfig()
        cfg.token = "ghp_xxx"
        cfg.user = "u"
        cfg.repo = "r"
        self.assertTrue(cfg.is_valid())

    def test_is_valid_missing_token(self):
        """is_valid returns False when token is empty."""
        cfg = GitHubConfig()
        cfg.user = "u"
        cfg.repo = "r"
        self.assertFalse(cfg.is_valid())

    def test_repo_full_name(self):
        cfg = GitHubConfig()
        cfg.user = "owner"
        cfg.repo = "repo"
        self.assertEqual(cfg.repo_full_name(), "owner/repo")


# ---------------------------------------------------------------------------
# API Client tests (mocked HTTP)
# ---------------------------------------------------------------------------

class TestGitHubAPIClient(unittest.TestCase):
    def setUp(self):
        self.client = GitHubAPIClient("ghp_test")

    @patch("src.api_client.urllib.request.urlopen")
    def test_get_repo(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(
            {"full_name": "owner/repo", "private": False}
        ).encode()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        result = self.client.get_repo("owner", "repo")
        self.assertEqual(result["full_name"], "owner/repo")

    @patch("src.api_client.urllib.request.urlopen")
    def test_get_commits(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps([
            {"sha": "abc123", "commit": {"author": {"name": "Dev", "date": "2026-01-01"}, "message": "fix"}}
        ]).encode()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        commits = self.client.get_commits("owner", "repo")
        self.assertEqual(len(commits), 1)
        self.assertEqual(commits[0]["sha"], "abc123")

    @patch("src.api_client.urllib.request.urlopen")
    def test_list_pull_requests(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps([
            {"number": 1, "title": "PR1", "user": {"login": "dev"}, "created_at": "2026-01-01", "html_url": "https://..."}
        ]).encode()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        prs = self.client.list_pull_requests("owner", "repo")
        self.assertEqual(len(prs), 1)
        self.assertEqual(prs[0]["number"], 1)

    @patch("src.api_client.urllib.request.urlopen")
    def test_list_issues(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps([
            {"number": 1, "title": "Bug", "user": {"login": "user"}, "created_at": "2026-01-01", "html_url": "https://..."}
        ]).encode()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        issues = self.client.list_issues("owner", "repo")
        self.assertEqual(len(issues), 1)

    @patch("src.api_client.urllib.request.urlopen")
    def test_get_contributors(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps([
            {"login": "dev1", "contributions": 42, "html_url": "https://..."}
        ]).encode()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        contributors = self.client.get_contributors("owner", "repo")
        self.assertEqual(contributors[0]["login"], "dev1")
        self.assertEqual(contributors[0]["contributions"], 42)

    @patch("src.api_client.urllib.request.urlopen")
    def test_api_error(self, mock_urlopen):
        import urllib.error
        mock_error = urllib.error.HTTPError(
            "https://api.github.com/test", 404, "Not Found", {}, None
        )
        mock_error.read = MagicMock(return_value=b'{"message": "Not Found"}')
        mock_urlopen.side_effect = mock_error

        with self.assertRaises(GitHubAPIError) as ctx:
            self.client.get_repo("owner", "repo")
        self.assertEqual(ctx.exception.status, 404)


# ---------------------------------------------------------------------------
# Tracker module tests (mocked API client)
# ---------------------------------------------------------------------------

class TestCommitTracker(unittest.TestCase):
    def setUp(self):
        self.mock_client = MagicMock()
        self.mock_config = MagicMock()
        self.mock_config.user = "owner"
        self.mock_config.repo = "repo"
        self.tracker = CommitTracker(self.mock_client, self.mock_config)

    def test_recent_commits(self):
        self.mock_client.get_commits.return_value = [
            {
                "sha": "abc123def456",
                "commit": {
                    "author": {"name": "Dev", "date": "2026-04-01T00:00:00Z"},
                    "message": "feat: add new feature\n\nLong description",
                },
            }
        ]
        commits = self.tracker.recent_commits()
        self.assertEqual(len(commits), 1)
        self.assertEqual(commits[0]["sha"], "abc123d")
        self.assertEqual(commits[0]["message"], "feat: add new feature")

    def test_commit_count_last_week(self):
        self.mock_client.get_commit_activity.return_value = [
            {"total": 5, "week": 1}
        ]
        count = self.tracker.commit_count_last_week()
        self.assertEqual(count, 5)

    def test_commit_count_last_week_error(self):
        self.mock_client.get_commit_activity.side_effect = GitHubAPIError(
            500, "", ""
        )
        count = self.tracker.commit_count_last_week()
        self.assertEqual(count, 0)


class TestPRTracker(unittest.TestCase):
    def setUp(self):
        self.mock_client = MagicMock()
        self.mock_config = MagicMock()
        self.mock_config.user = "owner"
        self.mock_config.repo = "repo"
        self.tracker = PRTracker(self.mock_client, self.mock_config)

    def test_open_prs(self):
        self.mock_client.list_pull_requests.return_value = [
            {
                "number": 1,
                "title": "Add feature",
                "user": {"login": "dev"},
                "created_at": "2026-04-01",
                "html_url": "https://github.com/...",
            }
        ]
        prs = self.tracker.open_prs()
        self.assertEqual(len(prs), 1)
        self.assertEqual(prs[0]["title"], "Add feature")

    def test_pr_summary(self):
        self.mock_client.list_pull_requests.return_value = [
            {
                "number": 1,
                "title": "PR1",
                "user": {"login": "dev"},
                "created_at": "2026-04-01",
                "html_url": "https://...",
            },
            {
                "number": 2,
                "title": "PR2",
                "user": {"login": "dev2"},
                "created_at": "2026-04-02",
                "html_url": "https://...",
            },
        ]
        summary = self.tracker.pr_summary()
        self.assertEqual(summary["open_count"], 2)


class TestIssueTracker(unittest.TestCase):
    def setUp(self):
        self.mock_client = MagicMock()
        self.mock_config = MagicMock()
        self.mock_config.user = "owner"
        self.mock_config.repo = "repo"
        self.tracker = IssueTracker(self.mock_client, self.mock_config)

    def test_open_issues_filters_prs(self):
        self.mock_client.list_issues.return_value = [
            {
                "number": 1,
                "title": "Bug report",
                "user": {"login": "user"},
                "created_at": "2026-04-01",
                "html_url": "https://...",
            },
            {
                "number": 2,
                "title": "PR",
                "user": {"login": "dev"},
                "created_at": "2026-04-01",
                "html_url": "https://...",
                "pull_request": {"url": "..."},
            },
        ]
        issues = self.tracker.open_issues()
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["title"], "Bug report")


class TestContributorStats(unittest.TestCase):
    def setUp(self):
        self.mock_client = MagicMock()
        self.mock_config = MagicMock()
        self.mock_config.user = "owner"
        self.mock_config.repo = "repo"
        self.stats = ContributorStats(self.mock_client, self.mock_config)

    def test_top_contributors(self):
        self.mock_client.get_contributors.return_value = [
            {"login": "dev1", "contributions": 100, "html_url": "https://..."},
            {"login": "dev2", "contributions": 50, "html_url": "https://..."},
        ]
        top = self.stats.top_contributors(limit=5)
        self.assertEqual(len(top), 2)
        self.assertEqual(top[0]["contributions"], 100)


class TestActivityReport(unittest.TestCase):
    def setUp(self):
        self.mock_client = MagicMock()
        self.mock_config = MagicMock()
        self.mock_config.user = "owner"
        self.mock_config.repo = "repo"
        self.mock_config.repo_full_name.return_value = "owner/repo"

        # Setup mock return values for all API calls
        self.mock_client.get_commits.return_value = [
            {
                "sha": "abc123",
                "commit": {
                    "author": {"name": "Dev", "date": "2026-04-01"},
                    "message": "fix: bug",
                },
            }
        ]
        self.mock_client.get_commit_activity.return_value = [{"total": 3}]
        self.mock_client.list_pull_requests.return_value = []
        self.mock_client.list_issues.return_value = []
        self.mock_client.get_contributors.return_value = []

        self.report = ActivityReport(self.mock_config, self.mock_client)

    def test_build_report(self):
        report = self.report.build()
        self.assertIn("repository", report)
        self.assertIn("generated_at", report)
        self.assertIn("recent_commits", report)
        self.assertIn("pull_requests", report)
        self.assertIn("open_issues", report)
        self.assertIn("top_contributors", report)
        self.assertEqual(len(report["recent_commits"]), 1)

    def test_save_report(self):
        report = self.report.build()
        filepath = self.report.save(report)
        self.assertTrue(Path(filepath).exists())
        with open(filepath) as f:
            loaded = json.load(f)
        self.assertEqual(loaded["repository"], "owner/repo")
        Path(filepath).unlink()


# ---------------------------------------------------------------------------
# Legacy tests (still work)
# ---------------------------------------------------------------------------

class TestGitHubTrackerLegacy(unittest.TestCase):
    """Ensure backward compatibility with original GitHubTracker class."""

    def test_init(self):
        from github_tracker import GitHubTracker
        tracker = GitHubTracker("test_token", "test_owner", "test_repo")
        self.assertEqual(tracker.owner, "test_owner")
        self.assertEqual(tracker.repo, "test_repo")


if __name__ == "__main__":
    unittest.main()
