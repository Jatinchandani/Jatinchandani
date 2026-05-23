"""Arbeitnow API — free, no key required. European + remote jobs."""

import requests
from .base import JobPosting
from ..core.email_extractor import extract_emails

API_URL = "https://www.arbeitnow.com/api/job-board-api"


def scan(keywords: list[str], **kwargs) -> list[JobPosting]:
    jobs = []

    try:
        resp = requests.get(API_URL, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []

    keyword_set = {kw.lower() for kw in keywords}

    for item in data.get("data", []):
        title = item.get("title", "").lower()
        desc = item.get("description", "").lower()
        tags = " ".join(item.get("tags", [])).lower()
        combined = f"{title} {desc} {tags}"

        if not any(kw in combined for kw in keyword_set):
            continue

        full_desc = item.get("description", "")
        emails = extract_emails(full_desc)

        jobs.append(JobPosting(
            source="arbeitnow",
            title=item.get("title", ""),
            company=item.get("company_name", ""),
            location=item.get("location", ""),
            description=full_desc,
            url=item.get("url", ""),
            contact_email=emails[0] if emails else None,
        ))

    return jobs
