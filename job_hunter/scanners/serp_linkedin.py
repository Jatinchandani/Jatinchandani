"""SerpAPI — alternative to Google CSE for finding LinkedIn posts with emails.

SerpAPI has a free tier (100 searches/month) and provides richer snippets
from Google results, making email extraction more reliable.
"""

import requests
from .base import JobPosting
from ..core.email_extractor import extract_emails

API_URL = "https://serpapi.com/search.json"

QUERIES = [
    'site:linkedin.com/posts "hiring" "email" "{keyword}"',
    'site:linkedin.com/posts "send resume" "{keyword}"',
    'site:linkedin.com/posts "DM or email" "{keyword}"',
]


def scan(keywords: list[str], serp_api_key: str = "", **kwargs) -> list[JobPosting]:
    if not serp_api_key:
        return []

    jobs = []

    for keyword in keywords[:3]:
        for query_template in QUERIES[:2]:
            query = query_template.format(keyword=keyword)
            try:
                resp = requests.get(API_URL, params={
                    "engine": "google",
                    "q": query,
                    "api_key": serp_api_key,
                    "num": 10,
                    "tbs": "qdr:w",
                }, timeout=15)
                resp.raise_for_status()
                data = resp.json()
            except Exception:
                continue

            for result in data.get("organic_results", []):
                snippet = result.get("snippet", "")
                title = result.get("title", "")
                link = result.get("link", "")

                combined = f"{title} {snippet}"
                emails = extract_emails(combined)

                if not emails:
                    continue

                jobs.append(JobPosting(
                    source="serp_linkedin",
                    title=title,
                    company="(from LinkedIn post)",
                    location="",
                    description=snippet,
                    url=link,
                    contact_email=emails[0],
                ))

    return jobs
