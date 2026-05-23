"""Google Custom Search — finds LinkedIn posts with email addresses.

This is the key scanner for finding LinkedIn posts where people share
job openings with their email. We search for patterns like:
  site:linkedin.com "hiring" "email" "AI engineer"
  site:linkedin.com "send your resume" "data scientist"
"""

import requests
from .base import JobPosting
from ..core.email_extractor import extract_emails

API_URL = "https://www.googleapis.com/customsearch/v1"

SEARCH_TEMPLATES = [
    'site:linkedin.com/posts "hiring" "email" {keyword}',
    'site:linkedin.com/posts "send your resume" {keyword}',
    'site:linkedin.com/posts "drop your" "resume" {keyword}',
    'site:linkedin.com/posts "apply" "email" {keyword}',
    'site:linkedin.com/feed "hiring" "email" {keyword}',
]


def scan(keywords: list[str], api_key: str = "", cx: str = "", **kwargs) -> list[JobPosting]:
    if not api_key or not cx:
        return []

    jobs = []

    for keyword in keywords[:3]:
        for template in SEARCH_TEMPLATES[:2]:
            query = template.format(keyword=keyword)
            try:
                resp = requests.get(API_URL, params={
                    "key": api_key,
                    "cx": cx,
                    "q": query,
                    "num": 10,
                    "dateRestrict": "w1",
                }, timeout=15)
                resp.raise_for_status()
                data = resp.json()
            except Exception:
                continue

            for item in data.get("items", []):
                snippet = item.get("snippet", "")
                title = item.get("title", "")
                link = item.get("link", "")

                combined_text = f"{title} {snippet}"
                emails = extract_emails(combined_text)

                if not emails:
                    continue

                jobs.append(JobPosting(
                    source="google_linkedin",
                    title=title,
                    company="(from LinkedIn post)",
                    location="",
                    description=snippet,
                    url=link,
                    contact_email=emails[0],
                ))

    return jobs
