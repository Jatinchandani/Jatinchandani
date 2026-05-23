import unittest
import tempfile
import os
from job_hunter.scanners.manual_paste import scan_text, scan_file


class TestManualPaste(unittest.TestCase):

    def test_scan_text_with_email(self):
        text = """We're hiring a Senior Data Scientist at TechCorp!
        Send your resume to jobs@techcorp.io
        #hiring #datascience"""
        jobs = scan_text(text)
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].contact_email, "jobs@techcorp.io")
        self.assertEqual(jobs[0].source, "manual")

    def test_scan_text_no_email(self):
        text = "Great company, apply on our website!"
        jobs = scan_text(text)
        self.assertEqual(len(jobs), 0)

    def test_scan_text_multiple_emails(self):
        text = "Contact hr@a.com or tech@b.com for the ML role"
        jobs = scan_text(text)
        self.assertEqual(len(jobs), 2)

    def test_scan_file(self):
        content = """Hiring ML Engineer! Email: ml@startup.ai
---
Looking for Data Analyst, send CV to careers@data.co
---
No email here, just a random post"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(content)
            path = f.name

        try:
            jobs = scan_file(path)
            self.assertEqual(len(jobs), 2)
            emails = {j.contact_email for j in jobs}
            self.assertIn("ml@startup.ai", emails)
            self.assertIn("careers@data.co", emails)
        finally:
            os.unlink(path)

    def test_scan_file_nonexistent(self):
        jobs = scan_file("/tmp/does_not_exist_12345.txt")
        self.assertEqual(len(jobs), 0)

    def test_title_extraction(self):
        text = "We are hiring a Senior Python Developer. Email dev@co.com"
        jobs = scan_text(text)
        self.assertEqual(len(jobs), 1)
        self.assertIn("Python Developer", jobs[0].title)

    def test_custom_source(self):
        text = "Apply at hr@firm.com for the role"
        jobs = scan_text(text, source="linkedin_copy")
        self.assertEqual(jobs[0].source, "linkedin_copy")


if __name__ == "__main__":
    unittest.main()
