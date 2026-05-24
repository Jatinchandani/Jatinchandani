"""CLI entry point: python -m job_hunter"""

import argparse
import logging
import time
import sys
from .config import Config
from .pipeline import run_pipeline
from .core.database import JobDatabase
from .core.ai_drafter import draft_email
from .core.email_sender import send_email


def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )


def cmd_run(args, config: Config):
    if args.live:
        config.dry_run = False
    if args.auto_send:
        config.auto_send = True
        config.dry_run = False
    run_pipeline(config)


def cmd_loop(args, config: Config):
    if args.live:
        config.dry_run = False
    if args.auto_send:
        config.auto_send = True
        config.dry_run = False

    logger = logging.getLogger("job_hunter")
    interval = config.scan_interval_minutes

    logger.info(f"Starting continuous scan loop (every {interval} minutes)")
    logger.info("Press Ctrl+C to stop.\n")

    while True:
        try:
            run_pipeline(config)
            logger.info(f"\nSleeping {interval} minutes until next scan...\n")
            time.sleep(interval * 60)
        except KeyboardInterrupt:
            logger.info("\nStopped by user.")
            break


def cmd_paste(args, config: Config):
    logger = logging.getLogger("job_hunter")
    db = JobDatabase(config.db_path)

    logger.info("Paste the job post text below (Ctrl+D or Ctrl+Z when done):")
    text = sys.stdin.read()

    from .scanners.manual_paste import scan_text
    jobs = scan_text(text, source="manual_paste")

    if not jobs:
        logger.info("No email addresses found in the pasted text.")
        return

    for job in jobs:
        job_id = db.save_job(
            source=job.source, title=job.title, company=job.company,
            location=job.location, description=job.description,
            url=job.url, contact_email=job.contact_email,
        )
        if not job_id:
            logger.info(f"Job already seen: {job.title}")
            continue
        if not config.anthropic_api_key:
            logger.info(f"Saved job: {job.title} -> {job.contact_email} (no API key for drafting)")
            continue
        try:
            result = draft_email(
                job_title=job.title, company=job.company,
                job_description=job.description,
                resume_text=config.resume_text,
                candidate_name=config.your_name,
                candidate_email=config.your_email,
                candidate_linkedin=config.your_linkedin,
                api_key=config.anthropic_api_key,
            )
            db.save_application(job_id, job.contact_email, result["subject"], result["body"])
            logger.info(f"\nTo: {job.contact_email}")
            logger.info(f"Subject: {result['subject']}")
            logger.info(f"Body:\n{result['body']}")
        except Exception as e:
            logger.error(f"Failed to draft email for {job.title}: {e}")


def cmd_review(args, config: Config):
    logger = logging.getLogger("job_hunter")
    db = JobDatabase(config.db_path)

    with db._conn() as conn:
        drafts = conn.execute("""
            SELECT a.id, a.email_to, a.email_subject, a.email_body,
                   j.title, j.company, j.url
            FROM applications a
            JOIN jobs j ON j.id = a.job_id
            WHERE a.status = 'drafted'
            ORDER BY a.id DESC
        """).fetchall()

    if not drafts:
        logger.info("No drafts to review.")
        return

    for draft in drafts:
        print(f"\n{'='*60}")
        print(f"Draft #{draft['id']}")
        print(f"Job:     {draft['title']} at {draft['company']}")
        print(f"To:      {draft['email_to']}")
        print(f"Subject: {draft['email_subject']}")
        print(f"URL:     {draft['url']}")
        print(f"-" * 60)
        print(draft['email_body'])
        print(f"{'='*60}")

        if args.send:
            choice = input("Send this email? (y/n/q): ").strip().lower()
            if choice == "q":
                break
            if choice == "y":
                try:
                    send_email(
                        smtp_host=config.smtp_host, smtp_port=config.smtp_port,
                        smtp_user=config.smtp_user, smtp_password=config.smtp_password,
                        from_email=config.your_email, to_email=draft['email_to'],
                        subject=draft['email_subject'], body=draft['email_body'],
                        resume_path=config.resume_path,
                    )
                    db.mark_sent(draft['id'])
                    logger.info("  -> Sent!")
                except Exception as e:
                    logger.error(f"  -> Failed: {e}")


def cmd_stats(args, config: Config):
    db = JobDatabase(config.db_path)
    stats = db.get_stats()
    print(f"\n{'='*40}")
    print(f"  Job Hunter Stats")
    print(f"{'='*40}")
    print(f"  Total jobs found:    {stats['total_jobs']}")
    print(f"  Jobs with email:     {stats['jobs_with_email']}")
    print(f"  Emails drafted:      {stats['emails_drafted']}")
    print(f"  Emails sent:         {stats['emails_sent']}")
    print(f"{'='*40}\n")


def main():
    parser = argparse.ArgumentParser(
        prog="job_hunter",
        description="Automated job scanner and email application tool",
    )
    parser.add_argument("-v", "--verbose", action="store_true")

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    verbose_flag = dict(action="store_true", help="Enable verbose output")

    run_parser = subparsers.add_parser("run", help="Run a single scan cycle")
    run_parser.add_argument("-v", "--verbose", **verbose_flag)
    run_parser.add_argument("--live", action="store_true", help="Disable dry-run mode")
    run_parser.add_argument("--auto-send", action="store_true", help="Auto-send drafted emails")

    loop_parser = subparsers.add_parser("loop", help="Run continuously on a schedule")
    loop_parser.add_argument("-v", "--verbose", **verbose_flag)
    loop_parser.add_argument("--live", action="store_true", help="Disable dry-run mode")
    loop_parser.add_argument("--auto-send", action="store_true", help="Auto-send drafted emails")

    paste_parser = subparsers.add_parser("paste", help="Paste a job post and process it")
    paste_parser.add_argument("-v", "--verbose", **verbose_flag)

    review_parser = subparsers.add_parser("review", help="Review drafted emails")
    review_parser.add_argument("-v", "--verbose", **verbose_flag)
    review_parser.add_argument("--send", action="store_true", help="Option to send each draft")

    stats_parser = subparsers.add_parser("stats", help="Show lifetime statistics")
    stats_parser.add_argument("-v", "--verbose", **verbose_flag)

    args = parser.parse_args()
    setup_logging(args.verbose)
    config = Config()

    commands = {
        "run": cmd_run,
        "loop": cmd_loop,
        "paste": cmd_paste,
        "review": cmd_review,
        "stats": cmd_stats,
    }

    if args.command in commands:
        commands[args.command](args, config)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
