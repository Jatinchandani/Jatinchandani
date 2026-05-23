"""RSS feed scanner — polls job board RSS feeds for new postings.

Many boards expose RSS/Atom feeds. We check for emails in each posting.
Add your own feeds to FEED_URLS below.
"""

import xml.etree.ElementTree as ET
import requests
from .base import JobPosting
from ..core.email_extractor import extract_emails

FEED_URLS = [
    "https://remotive.com/remote-jobs/software-dev/feed",
    "https://remotive.com/remote-jobs/data/feed",
    "https://weworkremotely.com/categories/remote-back-end-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-full-stack-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss",
]


def scan(keywords: list[str], extra_feeds: list[str] = None, **kwargs) -> list[JobPosting]:
    feeds = FEED_URLS + (extra_feeds or [])
    keyword_set = {kw.lower() for kw in keywords}
    jobs = []

    for feed_url in feeds:
        try:
            resp = requests.get(feed_url, timeout=15, headers={
                "User-Agent": "JobHunter/1.0 (RSS reader)"
            })
            resp.raise_for_status()
            root = ET.fromstring(resp.content)
        except Exception:
            continue

        ns = {"atom": "http://www.w3.org/2005/Atom"}
        items = root.findall(".//item") or root.findall(".//atom:entry", ns)

        for item in items[:20]:
            title_el = item.find("title") or item.find("atom:title", ns)
            title = title_el.text if title_el is not None and title_el.text else ""

            desc_el = (
                item.find("description")
                or item.find("content:encoded", {"content": "http://purl.org/rss/1.0/modules/content/"})
                or item.find("atom:content", ns)
                or item.find("atom:summary", ns)
            )
            desc = desc_el.text if desc_el is not None and desc_el.text else ""

            link_el = item.find("link") or item.find("atom:link", ns)
            link = ""
            if link_el is not None:
                link = link_el.text or link_el.get("href", "")

            combined = f"{title} {desc}".lower()
            if not any(kw in combined for kw in keyword_set):
                continue

            emails = extract_emails(desc)

            jobs.append(JobPosting(
                source="rss",
                title=title.strip(),
                company="",
                location="",
                description=desc[:3000],
                url=link.strip() if isinstance(link, str) else "",
                contact_email=emails[0] if emails else None,
            ))

    return jobs
