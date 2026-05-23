from dataclasses import dataclass


@dataclass
class JobPosting:
    source: str
    title: str
    company: str
    location: str
    description: str
    url: str
    contact_email: str | None = None
