import os
from pathlib import Path


def _env(key: str, default: str = "") -> str:
    return os.getenv(key, default)


def _env_bool(key: str, default: str = "false") -> bool:
    return os.getenv(key, default).lower() == "true"


def _env_int(key: str, default: str = "0") -> int:
    return int(os.getenv(key, default))


class Config:
    def __init__(self):
        self.resume_path = _env("JH_RESUME_PATH", "resume.pdf")
        self.resume_text_path = _env("JH_RESUME_TEXT_PATH", "resume.txt")

        self.your_name = _env("JH_YOUR_NAME", "Jatin Chandani")
        self.your_email = _env("JH_YOUR_EMAIL", "chandanijatin28@gmail.com")
        self.your_linkedin = _env("JH_YOUR_LINKEDIN", "https://linkedin.com/in/jatinchandani28")

        self.keywords = [
            kw.strip() for kw in _env(
                "JH_KEYWORDS",
                "AI Engineer,ML Engineer,Data Scientist,Python Developer,GenAI,LLM,MLOps"
            ).split(",")
        ]
        self.location = _env("JH_LOCATION", "Dubai")
        self.remote_ok = _env_bool("JH_REMOTE_OK", "true")

        self.anthropic_api_key = _env("ANTHROPIC_API_KEY")
        self.adzuna_app_id = _env("ADZUNA_APP_ID")
        self.adzuna_api_key = _env("ADZUNA_API_KEY")
        self.google_cse_api_key = _env("GOOGLE_CSE_API_KEY")
        self.google_cse_cx = _env("GOOGLE_CSE_CX")
        self.serp_api_key = _env("SERP_API_KEY")

        self.smtp_host = _env("JH_SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = _env_int("JH_SMTP_PORT", "587")
        self.smtp_user = _env("JH_SMTP_USER")
        self.smtp_password = _env("JH_SMTP_PASSWORD")

        self.imap_host = _env("JH_IMAP_HOST", "imap.gmail.com")
        self.imap_user = _env("JH_IMAP_USER")
        self.imap_password = _env("JH_IMAP_PASSWORD")

        self.db_path = _env("JH_DB_PATH", "job_hunter.db")

        self.scan_interval_minutes = _env_int("JH_SCAN_INTERVAL", "60")
        self.max_emails_per_run = _env_int("JH_MAX_EMAILS_PER_RUN", "10")

        self.dry_run = _env_bool("JH_DRY_RUN", "true")
        self.auto_send = _env_bool("JH_AUTO_SEND")

    @property
    def resume_text(self) -> str:
        path = Path(self.resume_text_path)
        if path.exists():
            return path.read_text()
        return ""
