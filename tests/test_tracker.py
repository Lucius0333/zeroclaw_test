import unittest
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from github_tracker import GitHubTracker


class TestGitHubTracker(unittest.TestCase):
    def setUp(self):
        self.tracker = GitHubTracker("test_token", "test_owner", "test_repo")
    
    def test_init(self):
        self.assertEqual(self.tracker.owner, "test_owner")
        self.assertEqual(self.tracker.repo, "test_repo")
    
    def test_get_repo_info(self):
        info = self.tracker.get_repo_info()
        self.assertIn("owner", info)
        self.assertIn("repo", info)
        self.assertIn("tracked_at", info)


if __name__ == "__main__":
    unittest.main()
