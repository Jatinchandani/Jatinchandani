"""Remotive.com — free API, no key required. Remote jobs only."""

import requests
from .base import JobPosting
from ..core.email_extractor import extract_emails


API_URL = "https://remotive.com/api/remote-jobs"


def scan(keywords: list[str], **kwargs) -> list[JobPosting]:
    jobs = []

    for keyword in keywords:
        try:
            resp = requests.get(API_URL, params={"search": keyword}, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            continue

        for item in data.get("jobs", [])[:20]:
            desc = item.get("description", "")
            emails = extract_emails(desc)

            jobs.append(JobPosting(
                source="remotive",
                title=item.get("title", ""),
                company=item.get("company_name", ""),
                location=item.get("candidate_required_location", "Remote"),
                description=desc,
                url=item.get("url", ""),
                contact_email=emails[0] if emails else None,
            ))

    return jobs
