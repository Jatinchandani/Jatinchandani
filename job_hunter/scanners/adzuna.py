"""Adzuna API — free tier: 250 requests/month. Covers 16 countries including UAE."""

import requests
from .base import JobPosting
from ..core.email_extractor import extract_emails

API_URL = "https://api.adzuna.com/v1/api/jobs/{country}/search/{page}"

COUNTRY_MAP = {
    "dubai": "ae", "uae": "ae", "abu dhabi": "ae",
    "uk": "gb", "london": "gb",
    "us": "us", "usa": "us", "new york": "us",
    "canada": "ca", "india": "in", "germany": "de",
    "singapore": "sg", "australia": "au",
}


def _resolve_country(location: str) -> str:
    loc = location.lower().strip()
    for key, code in COUNTRY_MAP.items():
        if key in loc:
            return code
    return "ae"


def scan(keywords: list[str], location: str = "Dubai",
         app_id: str = "", api_key: str = "", **kwargs) -> list[JobPosting]:
    if not app_id or not api_key:
        return []

    country = _resolve_country(location)
    jobs = []

    for keyword in keywords:
        try:
            url = API_URL.format(country=country, page=1)
            resp = requests.get(url, params={
                "app_id": app_id,
                "app_key": api_key,
                "what": keyword,
                "results_per_page": 20,
                "content-type": "application/json",
            }, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            continue

        for item in data.get("results", []):
            desc = item.get("description", "")
            emails = extract_emails(desc)

            jobs.append(JobPosting(
                source="adzuna",
                title=item.get("title", ""),
                company=item.get("company", {}).get("display_name", ""),
                location=item.get("location", {}).get("display_name", ""),
                description=desc,
                url=item.get("redirect_url", ""),
                contact_email=emails[0] if emails else None,
            ))

    return jobs
