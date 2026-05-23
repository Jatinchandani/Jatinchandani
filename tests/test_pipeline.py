"""Integration test — run the full pipeline end-to-end in dry-run mode."""

import unittest
import tempfile
import os
from job_hunter.config import Config
from job_hunter.pipeline import run_scanners, save_jobs, run_pipeline
from job_hunter.core.database import JobDatabase


class TestPipelineIntegration(unittest.TestCase):

    def setUp(self):
        self.tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp_db.close()
        self.config = Config()
        self.config.db_path = self.tmp_db.name
        self.config.dry_run = True

    def tearDown(self):
        os.unlink(self.tmp_db.name)

    def test_run_scanners_returns_jobs(self):
        jobs = run_scanners(self.config)
        self.assertIsInstance(jobs, list)
        self.assertGreater(len(jobs), 0, "Should find at least some jobs from free APIs")

    def test_save_jobs_deduplicates(self):
        db = JobDatabase(self.config.db_path)
        jobs = run_scanners(self.config)

        first_save = save_jobs(db, jobs)
        second_save = save_jobs(db, jobs)

        self.assertGreater(len(first_save), 0)
        self.assertEqual(len(second_save), 0, "Second save should find 0 new jobs")

    def test_full_pipeline_dry_run(self):
        run_pipeline(self.config)

        db = JobDatabase(self.config.db_path)
        stats = db.get_stats()
        self.assertGreater(stats["total_jobs"], 0)
        self.assertEqual(stats["emails_sent"], 0, "Dry run should not send emails")

    def test_pipeline_stats_consistent(self):
        run_pipeline(self.config)
        db = JobDatabase(self.config.db_path)
        stats = db.get_stats()

        self.assertGreaterEqual(stats["total_jobs"], stats["jobs_with_email"])
        self.assertGreaterEqual(stats["emails_drafted"], stats["emails_sent"])


if __name__ == "__main__":
    unittest.main()
