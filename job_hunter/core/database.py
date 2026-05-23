import sqlite3
from datetime import datetime
from pathlib import Path


class JobDatabase:
    def __init__(self, db_path: str = "job_hunter.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    title TEXT NOT NULL,
                    company TEXT,
                    location TEXT,
                    description TEXT,
                    url TEXT,
                    contact_email TEXT,
                    found_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'new'
                );

                CREATE TABLE IF NOT EXISTS applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER NOT NULL,
                    email_to TEXT NOT NULL,
                    email_subject TEXT,
                    email_body TEXT,
                    sent_at TIMESTAMP,
                    status TEXT DEFAULT 'drafted',
                    FOREIGN KEY (job_id) REFERENCES jobs(id)
                );

                CREATE UNIQUE INDEX IF NOT EXISTS idx_jobs_url
                    ON jobs(url) WHERE url IS NOT NULL;

                CREATE UNIQUE INDEX IF NOT EXISTS idx_jobs_email_title
                    ON jobs(contact_email, title) WHERE contact_email IS NOT NULL;
            """)

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def job_exists(self, url: str = None, email: str = None, title: str = None) -> bool:
        with self._conn() as conn:
            if url:
                row = conn.execute("SELECT 1 FROM jobs WHERE url = ?", (url,)).fetchone()
                if row:
                    return True
            if email and title:
                row = conn.execute(
                    "SELECT 1 FROM jobs WHERE contact_email = ? AND title = ?",
                    (email, title)
                ).fetchone()
                if row:
                    return True
        return False

    def save_job(self, source: str, title: str, company: str, location: str,
                 description: str, url: str, contact_email: str) -> int | None:
        if self.job_exists(url=url, email=contact_email, title=title):
            return None
        with self._conn() as conn:
            cursor = conn.execute(
                """INSERT INTO jobs (source, title, company, location, description, url, contact_email)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (source, title, company, location, description, url, contact_email)
            )
            return cursor.lastrowid

    def save_application(self, job_id: int, email_to: str, subject: str, body: str) -> int:
        with self._conn() as conn:
            cursor = conn.execute(
                """INSERT INTO applications (job_id, email_to, email_subject, email_body)
                   VALUES (?, ?, ?, ?)""",
                (job_id, email_to, subject, body)
            )
            return cursor.lastrowid

    def mark_sent(self, application_id: int):
        with self._conn() as conn:
            conn.execute(
                "UPDATE applications SET status = 'sent', sent_at = ? WHERE id = ?",
                (datetime.utcnow().isoformat(), application_id)
            )

    def mark_job_applied(self, job_id: int):
        with self._conn() as conn:
            conn.execute("UPDATE jobs SET status = 'applied' WHERE id = ?", (job_id,))

    def get_new_jobs_with_email(self) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT * FROM jobs
                   WHERE status = 'new' AND contact_email IS NOT NULL
                   ORDER BY found_at DESC"""
            ).fetchall()
            return [dict(r) for r in rows]

    def get_stats(self) -> dict:
        with self._conn() as conn:
            total = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
            with_email = conn.execute(
                "SELECT COUNT(*) FROM jobs WHERE contact_email IS NOT NULL"
            ).fetchone()[0]
            applied = conn.execute(
                "SELECT COUNT(*) FROM applications WHERE status = 'sent'"
            ).fetchone()[0]
            drafted = conn.execute(
                "SELECT COUNT(*) FROM applications WHERE status = 'drafted'"
            ).fetchone()[0]
            return {
                "total_jobs": total,
                "jobs_with_email": with_email,
                "emails_sent": applied,
                "emails_drafted": drafted,
            }
