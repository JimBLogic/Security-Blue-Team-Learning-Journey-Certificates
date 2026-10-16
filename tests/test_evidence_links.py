"""Check public training links without inspecting or uploading personal PDFs."""
from datetime import date
from pathlib import Path
import re
import unittest
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text(encoding="utf-8")
ROWS = re.findall(
    r"^\|[^\n]*?\]\((\./certs/[^)]+)\)\s*\|\s*(\d{4}-\d{2}-\d{2})\s*\|",
    README, flags=re.MULTILINE,
)


def linked_path(uri: str) -> Path:
    decoded = unquote(uri)
    path = Path(decoded)
    if path.is_absolute() or not decoded.startswith("./certs/") or ".." in path.parts:
        raise ValueError(f"Disallowed local evidence link: {uri}")
    target = (ROOT / decoded).resolve()
    if not target.is_relative_to(ROOT) or target.is_symlink():
        raise ValueError(f"Evidence path escaped repository: {uri}")
    return target


class TrainingLinks(unittest.TestCase):
    def test_each_of_twelve_course_links_has_existing_nonplaceholder_pdf(self):
        self.assertEqual(len(ROWS), 12)
        for uri, _ in ROWS:
            evidence = linked_path(uri)
            self.assertTrue(evidence.is_file(), uri)
            self.assertEqual(evidence.suffix.lower(), ".pdf")
            self.assertGreater(evidence.stat().st_size, 1000, uri)

    def test_pdf_inventory_matches_readme_without_missing_certificates(self):
        linked = {linked_path(uri) for uri, _ in ROWS}
        on_disk = {p.resolve() for p in (ROOT / "certs").glob("*.pdf")}
        self.assertEqual(len(linked), len(ROWS))
        self.assertEqual(linked, on_disk)

    def test_missing_interview_preparation_certificate_is_truthfully_disclosed(self):
        self.assertIn("| Cybersecurity Interview Preparation", README)
        self.assertIn("no certificate file is currently included", README)
        self.assertNotIn("certs/Cybersecurity%20Interview%20Preparation", README)
        self.assertIn("not proof of paid professional experience", README)
        self.assertIn("not", README)

    def test_dates_and_pr_only_read_permissions_are_consistent(self):
        for uri, date_text in ROWS:
            self.assertLessEqual(date.fromisoformat(date_text), date(2026, 10, 16), uri)
        workflow = (ROOT / ".github/workflows/evidence-links.yml").read_text(encoding="utf-8")
        self.assertIn("pull_request:", workflow)
        self.assertIn("contents: read", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertNotIn("contents: write", workflow)
        self.assertNotIn("deploy-pages", workflow)
        self.assertNotIn("workflow_dispatch", workflow)


if __name__ == "__main__":
    unittest.main()
