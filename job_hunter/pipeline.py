"""Main pipeline: scan -> extract -> draft -> send."""

import logging
from .config import Config
from .core.database import JobDatabase
from .core.ai_drafter import draft_email
from .core.email_sender import send_email
from .scanners import (
    remotive,
    adzuna,
    arbeitnow,
    themuse,
    google_search,
    serp_linkedin,
    linkedin_email_alerts,
    linkedin_posts,
    rss_feeds,
    manual_paste,
)
from .scanners.base import JobPosting

logger = logging.getLogger("job_hunter")


def run_scanners(config: Config) -> list[JobPosting]:
    all_jobs = []

    scanners = [
        ("Remotive", lambda: remotive.scan(config.keywords)),
        ("Arbeitnow", lambda: arbeitnow.scan(config.keywords)),
        ("The Muse", lambda: themuse.scan(config.keywords, config.location)),
        ("Adzuna", lambda: adzuna.scan(
            config.keywords, config.location,
            config.adzuna_app_id, config.adzuna_api_key,
        )),
        ("Google/LinkedIn", lambda: google_search.scan(
            config.keywords, config.google_cse_api_key, config.google_cse_cx,
        )),
        ("SerpAPI/LinkedIn", lambda: serp_linkedin.scan(
            config.keywords, config.serp_api_key,
        )),
        ("LinkedIn Posts", lambda: linkedin_posts.scan(
            config.keywords,
            google_api_key=config.google_cse_api_key,
            google_cx=config.google_cse_cx,
            serp_api_key=config.serp_api_key,
        )),
        ("LinkedIn Alerts", lambda: linkedin_email_alerts.scan(
            config.imap_host, config.imap_user, config.imap_password,
            config.keywords,
        )),
        ("RSS Feeds", lambda: rss_feeds.scan(config.keywords)),
        ("Manual Paste File", lambda: manual_paste.scan()),
    ]

    for name, scanner_fn in scanners:
        try:
            logger.info(f"Scanning {name}...")
            jobs = scanner_fn()
            logger.info(f"  -> Found {len(jobs)} jobs ({sum(1 for j in jobs if j.contact_email)} with emails)")
            all_jobs.extend(jobs)
        except Exception as e:
            logger.warning(f"  -> {name} failed: {e}")

    return all_jobs


def save_jobs(db: JobDatabase, jobs: list[JobPosting]) -> list[dict]:
    new_jobs = []
    for job in jobs:
        job_id = db.save_job(
            source=job.source,
            title=job.title,
            company=job.company,
            location=job.location,
            description=job.description,
            url=job.url,
            contact_email=job.contact_email,
        )
        if job_id is not None:
            new_jobs.append({"id": job_id, **vars(job)})
    return new_jobs


def draft_and_send(config: Config, db: JobDatabase) -> int:
    actionable = db.get_new_jobs_with_email()
    if not actionable:
        logger.info("No new jobs with email addresses to process.")
        return 0

    resume_text = config.resume_text
    if not resume_text:
        logger.warning("No resume text found. Set JH_RESUME_TEXT_PATH or create resume.txt")
        return 0

    count = 0

    for job in actionable[:config.max_emails_per_run]:
        logger.info(f"Drafting email for: {job['title']} -> {job['contact_email']}")

        try:
            result = draft_email(
                job_title=job["title"],
                company=job["company"] or "",
                job_description=job["description"] or "",
                resume_text=resume_text,
                candidate_name=config.your_name,
                candidate_email=config.your_email,
                candidate_linkedin=config.your_linkedin,
                api_key=config.anthropic_api_key,
            )
        except Exception as e:
            logger.error(f"  -> Draft failed: {e}")
            continue

        app_id = db.save_application(
            job_id=job["id"],
            email_to=job["contact_email"],
            subject=result["subject"],
            body=result["body"],
        )

        if config.dry_run:
            logger.info(f"  -> [DRY RUN] Draft saved (app #{app_id})")
            logger.info(f"     Subject: {result['subject']}")
            logger.info(f"     To: {job['contact_email']}")
        elif config.auto_send:
            try:
                send_email(
                    smtp_host=config.smtp_host,
                    smtp_port=config.smtp_port,
                    smtp_user=config.smtp_user,
                    smtp_password=config.smtp_password,
                    from_email=config.your_email,
                    to_email=job["contact_email"],
                    subject=result["subject"],
                    body=result["body"],
                    resume_path=config.resume_path,
                )
                db.mark_sent(app_id)
                db.mark_job_applied(job["id"])
                logger.info(f"  -> Sent!")
            except Exception as e:
                logger.error(f"  -> Send failed: {e}")
                continue
        else:
            logger.info(f"  -> Draft saved. Use --send to send, or --auto-send to auto-send.")

        count += 1

    return count


def run_pipeline(config: Config):
    db = JobDatabase(config.db_path)

    logger.info("=" * 60)
    logger.info("JOB HUNTER - Automated Job Application Pipeline")
    logger.info("=" * 60)
    logger.info(f"Keywords: {', '.join(config.keywords)}")
    logger.info(f"Location: {config.location}")
    logger.info(f"Mode: {'DRY RUN' if config.dry_run else 'LIVE'}")
    logger.info("")

    jobs = run_scanners(config)
    logger.info(f"\nTotal found: {len(jobs)} jobs")

    new_jobs = save_jobs(db, jobs)
    logger.info(f"New (not seen before): {len(new_jobs)}")

    with_email = [j for j in new_jobs if j.get("contact_email")]
    logger.info(f"New with email: {len(with_email)}")

    if config.anthropic_api_key:
        count = draft_and_send(config, db)
        logger.info(f"\nProcessed: {count} emails")
    else:
        logger.warning("\nNo ANTHROPIC_API_KEY set — skipping email drafting.")
        logger.info("Set it to enable AI-powered personalized email drafting.")

    stats = db.get_stats()
    logger.info(f"\n--- Lifetime Stats ---")
    logger.info(f"Total jobs found: {stats['total_jobs']}")
    logger.info(f"Jobs with emails: {stats['jobs_with_email']}")
    logger.info(f"Emails drafted:   {stats['emails_drafted']}")
    logger.info(f"Emails sent:      {stats['emails_sent']}")
