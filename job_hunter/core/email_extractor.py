import re


_EMAIL_RE = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
)

_BLACKLIST_DOMAINS = {
    "example.com", "test.com", "email.com", "youremail.com",
    "company.com", "domain.com", "yourcompany.com",
    "sentry.io", "github.com", "gitlab.com", "bitbucket.org",
    "shields.io", "badge.fury.io", "npmjs.com", "pypi.org",
    "gravatar.com", "wordpress.com", "w3.org",
}

_BLACKLIST_PREFIXES = {
    "noreply", "no-reply", "donotreply", "do-not-reply",
    "mailer-daemon", "postmaster", "webmaster", "hostmaster",
    "info@linkedin", "notifications@", "jobs-noreply",
}


def extract_emails(text: str) -> list[str]:
    if not text:
        return []

    raw = _EMAIL_RE.findall(text.lower())
    seen = set()
    results = []

    for email in raw:
        if email in seen:
            continue
        seen.add(email)

        domain = email.split("@")[1]
        if domain in _BLACKLIST_DOMAINS:
            continue

        if any(email.startswith(prefix) for prefix in _BLACKLIST_PREFIXES):
            continue

        results.append(email)

    return results
