"""LinkedIn Post Scanner — finds "I'm hiring" posts via multiple search engines.

Since we can't use LinkedIn's API, we use Google/Bing to index public LinkedIn
posts. People who post "We're hiring" or "DM me" often include emails.

This scanner uses multiple search strategies to maximize coverage of
LinkedIn hiring posts — the #1 source for direct-email job opportunities.
"""

import requests
import re
from .base import JobPosting
from ..core.email_extractor import extract_emails

HIRING_PATTERNS = [
    '"{keyword}" "hiring" site:linkedin.com/posts',
    '"{keyword}" "we are hiring" site:linkedin.com/posts',
    '"{keyword}" "join our team" "email" site:linkedin.com/posts',
    '"{keyword}" "send your resume to" site:linkedin.com',
    '"{keyword}" "drop your CV" site:linkedin.com',
    '"{keyword}" "DM or email" site:linkedin.com/posts',
    '"{keyword}" "interested candidates" "email" site:linkedin.com',
    '"{keyword}" "apply" "email me" site:linkedin.com/posts',
    '"{keyword}" "open position" "email" site:linkedin.com/posts',
    '"{keyword}" "looking for" "reach out" site:linkedin.com/posts',
]


def _search_google_cse(query: str, api_key: str, cx: str) -> list[dict]:
    try:
        resp = requests.get("https://www.googleapis.com/customsearch/v1", params={
            "key": api_key,
            "cx": cx,
            "q": query,
            "num": 10,
            "dateRestrict": "w2",
        }, timeout=15)
        resp.raise_for_status()
        return resp.json().get("items", [])
    except Exception:
        return []


def _search_serpapi(query: str, api_key: str) -> list[dict]:
    try:
        resp = requests.get("https://serpapi.com/search.json", params={
            "engine": "google",
            "q": query,
            "api_key": api_key,
            "num": 10,
            "tbs": "qdr:w2",
        }, timeout=15)
        resp.raise_for_status()
        return resp.json().get("organic_results", [])
    except Exception:
        return []


def _fetch_post_content(url: str) -> str:
    """Try to fetch the public content of a LinkedIn post page."""
    try:
        resp = requests.get(url, timeout=10, headers={
            "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
        })
        if resp.status_code == 200:
            text = re.sub(r'<[^>]+>', ' ', resp.text)
            return text[:5000]
    except Exception:
        pass
    return ""


def scan(keywords: list[str], google_api_key: str = "", google_cx: str = "",
         serp_api_key: str = "", **kwargs) -> list[JobPosting]:
    jobs = []
    seen_urls = set()

    for keyword in keywords[:5]:
        for pattern in HIRING_PATTERNS[:4]:
            query = pattern.format(keyword=keyword)

            results = []
            if google_api_key and google_cx:
                raw = _search_google_cse(query, google_api_key, google_cx)
                results.extend([{
                    "title": r.get("title", ""),
                    "snippet": r.get("snippet", ""),
                    "link": r.get("link", ""),
                } for r in raw])

            if serp_api_key:
                raw = _search_serpapi(query, serp_api_key)
                results.extend([{
                    "title": r.get("title", ""),
                    "snippet": r.get("snippet", ""),
                    "link": r.get("link", ""),
                } for r in raw])

            for result in results:
                url = result["link"]
                if url in seen_urls:
                    continue
                seen_urls.add(url)

                combined = f"{result['title']} {result['snippet']}"
                emails = extract_emails(combined)

                if not emails:
                    page_text = _fetch_post_content(url)
                    emails = extract_emails(page_text)
                    combined += f" {page_text}"

                if not emails:
                    continue

                poster_name = ""
                title_match = re.match(r"^(.+?)(?:\s+on\s+LinkedIn|\s*[-|])", result["title"])
                if title_match:
                    poster_name = title_match.group(1).strip()

                jobs.append(JobPosting(
                    source="linkedin_post",
                    title=f"Hiring post by {poster_name}" if poster_name else "LinkedIn Hiring Post",
                    company=poster_name,
                    location="",
                    description=combined[:3000],
                    url=url,
                    contact_email=emails[0],
                ))

    return jobs
