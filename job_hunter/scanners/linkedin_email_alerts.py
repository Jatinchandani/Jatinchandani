"""Parse LinkedIn job alert emails from your Gmail inbox.

This is the most reliable LinkedIn source: you set up job alerts on LinkedIn,
LinkedIn emails you, and we parse those emails to extract job details.
Then we visit the job page to look for contact emails in the description.

Setup: Enable "Job alerts" on LinkedIn for your target roles/keywords.
LinkedIn will email you daily/weekly digests.
"""

import imaplib
import email
from email.header import decode_header
from html.parser import HTMLParser
from ..core.email_extractor import extract_emails
from .base import JobPosting
import re


class _HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self._text = []

    def handle_data(self, data):
        self._text.append(data)

    def get_text(self):
        return " ".join(self._text)


def _html_to_text(html: str) -> str:
    parser = _HTMLTextExtractor()
    parser.feed(html)
    return parser.get_text()


def _extract_links(html: str) -> list[str]:
    return re.findall(r'href="(https?://[^"]*linkedin\.com/jobs/view/[^"]*)"', html)


def scan(imap_host: str = "", imap_user: str = "", imap_password: str = "",
         keywords: list[str] = None, **kwargs) -> list[JobPosting]:
    if not imap_user or not imap_password:
        return []

    jobs = []

    try:
        mail = imaplib.IMAP4_SSL(imap_host or "imap.gmail.com")
        mail.login(imap_user, imap_password)
        mail.select("inbox")

        _, message_ids = mail.search(None, '(FROM "jobs-noreply@linkedin.com" UNSEEN)')

        if not message_ids[0]:
            mail.logout()
            return []

        for msg_id in message_ids[0].split()[-10:]:
            _, msg_data = mail.fetch(msg_id, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])

            subject = ""
            raw_subject = decode_header(msg["Subject"])
            for part, enc in raw_subject:
                if isinstance(part, bytes):
                    subject += part.decode(enc or "utf-8", errors="replace")
                else:
                    subject += part

            body_html = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/html":
                        body_html = part.get_payload(decode=True).decode("utf-8", errors="replace")
                        break
            else:
                body_html = msg.get_payload(decode=True).decode("utf-8", errors="replace")

            body_text = _html_to_text(body_html)
            job_links = _extract_links(body_html)
            all_emails = extract_emails(body_text)

            for link in job_links[:5]:
                jobs.append(JobPosting(
                    source="linkedin_alert",
                    title=subject,
                    company="(from LinkedIn alert)",
                    location="",
                    description=body_text[:2000],
                    url=link,
                    contact_email=all_emails[0] if all_emails else None,
                ))

        mail.logout()
    except Exception:
        pass

    return jobs
