"""Sharing-policy regression tests for contributor guidance."""

import unittest

from tools.audit_share import allowed


class ContributorGuidancePolicyTests(unittest.TestCase):
    def test_canonical_guidance_and_pr_template_are_allowed(self):
        for path in ("AGENTS.md", ".github/PULL_REQUEST_TEMPLATE.md"):
            with self.subTest(path=path):
                self.assertTrue(allowed(path))

    def test_guidance_allowlist_does_not_admit_unrelated_files(self):
        for path in (
            "OTHER_INSTRUCTIONS.md",
            ".github/credentials.json",
            ".github/PULL_REQUEST_TEMPLATE.env",
            "Game/AGENTS.md",
            "backups/AGENTS.md",
        ):
            with self.subTest(path=path):
                self.assertFalse(allowed(path))


if __name__ == "__main__":
    unittest.main()
