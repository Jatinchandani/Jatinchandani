"""Test email construction (not actual sending)."""

import unittest
import tempfile
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path


class TestEmailConstruction(unittest.TestCase):

    def test_build_email_with_attachment(self):
        msg = MIMEMultipart()
        msg["From"] = "sender@test.com"
        msg["To"] = "recipient@test.com"
        msg["Subject"] = "Application for AI Engineer"
        msg.attach(MIMEText("Hello, I am applying...", "plain"))

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"%PDF-1.4 fake resume content")
            resume_path = f.name

        try:
            with open(resume_path, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename={Path(resume_path).name}",
            )
            msg.attach(part)

            raw = msg.as_string()
            self.assertIn("From: sender@test.com", raw)
            self.assertIn("To: recipient@test.com", raw)
            self.assertIn("Application for AI Engineer", raw)
            self.assertIn("Hello, I am applying...", raw)
            self.assertIn("Content-Disposition: attachment", raw)
        finally:
            os.unlink(resume_path)

    def test_build_email_without_attachment(self):
        msg = MIMEMultipart()
        msg["From"] = "me@test.com"
        msg["To"] = "them@test.com"
        msg["Subject"] = "Test"
        msg.attach(MIMEText("Body text", "plain"))

        raw = msg.as_string()
        self.assertIn("Body text", raw)
        self.assertNotIn("Content-Disposition: attachment", raw)


if __name__ == "__main__":
    unittest.main()
