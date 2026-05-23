import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Config:
    # --- Resume ---
    resume_path: str = os.getenv("JH_RESUME_PATH", "resume.pdf")
    resume_text_path: str = os.getenv("JH_RESUME_TEXT_PATH", "resume.txt")

    # --- Your Info ---
    your_name: str = os.getenv("JH_YOUR_NAME", "Jatin Chandani")
    your_email: str = os.getenv("JH_YOUR_EMAIL", "chandanijatin28@gmail.com")
    your_linkedin: str = os.getenv("JH_YOUR_LINKEDIN", "https://linkedin.com/in/jatinchandani28")

    # --- Job Search Filters ---
    keywords: list[str] = field(default_factory=lambda: [
        kw.strip() for kw in os.getenv(
            "JH_KEYWORDS",
            "AI Engineer,ML Engineer,Data Scientist,Python Developer,GenAI,LLM,MLOps"
        ).split(",")
    ])
    location: str = os.getenv("JH_LOCATION", "Dubai")
    remote_ok: bool = os.getenv("JH_REMOTE_OK", "true").lower() == "true"

    # --- API Keys ---
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    adzuna_app_id: str = os.getenv("ADZUNA_APP_ID", "")
    adzuna_api_key: str = os.getenv("ADZUNA_API_KEY", "")
    google_cse_api_key: str = os.getenv("GOOGLE_CSE_API_KEY", "")
    google_cse_cx: str = os.getenv("GOOGLE_CSE_CX", "")
    serp_api_key: str = os.getenv("SERP_API_KEY", "")

    # --- Email (SMTP) ---
    smtp_host: str = os.getenv("JH_SMTP_HOST", "smtp.gmail.com")
    smtp_port: int = int(os.getenv("JH_SMTP_PORT", "587"))
    smtp_user: str = os.getenv("JH_SMTP_USER", "")
    smtp_password: str = os.getenv("JH_SMTP_PASSWORD", "")

    # --- Gmail IMAP (for parsing LinkedIn alert emails) ---
    imap_host: str = os.getenv("JH_IMAP_HOST", "imap.gmail.com")
    imap_user: str = os.getenv("JH_IMAP_USER", "")
    imap_password: str = os.getenv("JH_IMAP_PASSWORD", "")

    # --- Database ---
    db_path: str = os.getenv("JH_DB_PATH", "job_hunter.db")

    # --- Scheduling ---
    scan_interval_minutes: int = int(os.getenv("JH_SCAN_INTERVAL", "60"))
    max_emails_per_run: int = int(os.getenv("JH_MAX_EMAILS_PER_RUN", "10"))

    # --- Behavior ---
    dry_run: bool = os.getenv("JH_DRY_RUN", "true").lower() == "true"
    auto_send: bool = os.getenv("JH_AUTO_SEND", "false").lower() == "true"

    @property
    def resume_text(self) -> str:
        path = Path(self.resume_text_path)
        if path.exists():
            return path.read_text()
        return ""
