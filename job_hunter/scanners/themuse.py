"""The Muse API — free, no key required. Major tech companies."""

import requests
from .base import JobPosting
from ..core.email_extractor import extract_emails

API_URL = "https://www.themuse.com/api/public/jobs"


def scan(keywords: list[str], location: str = "Dubai", **kwargs) -> list[JobPosting]:
    jobs = []

    for keyword in keywords:
        try:
            resp = requests.get(API_URL, params={
                "page": 1,
                "descending": "true",
            }, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            continue

        keyword_lower = keyword.lower()

        for item in data.get("results", [])[:30]:
            title = item.get("name", "")
            desc_html = item.get("contents", "")

            if keyword_lower not in f"{title} {desc_html}".lower():
                continue

            company_info = item.get("company", {})
            locs = item.get("locations", [])
            loc_str = ", ".join(l.get("name", "") for l in locs) if locs else "Unknown"

            emails = extract_emails(desc_html)

            jobs.append(JobPosting(
                source="themuse",
                title=title,
                company=company_info.get("name", ""),
                location=loc_str,
                description=desc_html,
                url=item.get("refs", {}).get("landing_page", ""),
                contact_email=emails[0] if emails else None,
            ))

    return jobs
