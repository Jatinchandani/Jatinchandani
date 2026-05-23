"""Manual paste scanner — process job posts you copy-paste while scrolling LinkedIn.

Usage: Save posts to a text file (one per section separated by ---).
The tool will extract emails and process them automatically.

You can also pipe LinkedIn post text directly:
    echo "We're hiring an AI Engineer... email: hr@company.com" | python -m job_hunter.paste
"""

from pathlib import Path
from .base import JobPosting
from ..core.email_extractor import extract_emails
import re


def scan_text(text: str, source: str = "manual") -> list[JobPosting]:
    """Process a single pasted job post text."""
    emails = extract_emails(text)
    if not emails:
        return []

    title_match = re.search(
        r"(?:hiring|looking for|open position|role|vacancy)[:\s]*([^\n.]{10,80})",
        text, re.IGNORECASE,
    )
    title = title_match.group(1).strip() if title_match else "Job Posting"

    company_match = re.search(
        r"(?:at|@|company[:\s])\s*([A-Z][a-zA-Z0-9\s&.]{2,30})",
        text,
    )
    company = company_match.group(1).strip() if company_match else ""

    return [JobPosting(
        source=source,
        title=title,
        company=company,
        location="",
        description=text[:3000],
        url="",
        contact_email=email,
    ) for email in emails]


def scan_file(filepath: str) -> list[JobPosting]:
    """Process a file of pasted job posts, separated by --- lines."""
    path = Path(filepath)
    if not path.exists():
        return []

    content = path.read_text()
    sections = re.split(r"\n-{3,}\n", content)

    jobs = []
    for section in sections:
        section = section.strip()
        if section:
            jobs.extend(scan_text(section, source="paste_file"))
    return jobs


def scan(paste_file: str = "job_posts.txt", **kwargs) -> list[JobPosting]:
    return scan_file(paste_file)
