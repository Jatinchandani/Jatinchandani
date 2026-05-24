import unittest
import os
from job_hunter.config import Config


class TestConfig(unittest.TestCase):

    def test_default_values(self):
        config = Config()
        self.assertEqual(config.your_name, "Jatin Chandani")
        self.assertEqual(config.smtp_host, "smtp.gmail.com")
        self.assertEqual(config.smtp_port, 587)
        self.assertTrue(config.dry_run)
        self.assertFalse(config.auto_send)
        self.assertTrue(config.remote_ok)

    def test_keywords_parsing(self):
        config = Config()
        self.assertIsInstance(config.keywords, list)
        self.assertGreater(len(config.keywords), 0)
        self.assertIn("AI Engineer", config.keywords)

    def test_env_override(self):
        os.environ["JH_YOUR_NAME"] = "Test User"
        os.environ["JH_DRY_RUN"] = "false"
        try:
            config = Config()
            self.assertEqual(config.your_name, "Test User")
            self.assertFalse(config.dry_run)
        finally:
            del os.environ["JH_YOUR_NAME"]
            del os.environ["JH_DRY_RUN"]

    def test_resume_text_missing_file(self):
        config = Config()
        config.resume_text_path = "/tmp/nonexistent_resume_xyz.txt"
        self.assertEqual(config.resume_text, "")

    def test_invalid_int_env_var_uses_default(self):
        os.environ["JH_SMTP_PORT"] = "not_a_number"
        try:
            config = Config()
            self.assertEqual(config.smtp_port, 587)
        finally:
            del os.environ["JH_SMTP_PORT"]


if __name__ == "__main__":
    unittest.main()
