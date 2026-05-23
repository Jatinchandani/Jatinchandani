import unittest
import tempfile
import os
from job_hunter.core.database import JobDatabase


class TestJobDatabase(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db = JobDatabase(self.tmp.name)

    def tearDown(self):
        os.unlink(self.tmp.name)

    def test_save_and_retrieve_job(self):
        job_id = self.db.save_job(
            source="test", title="AI Engineer", company="TestCo",
            location="Dubai", description="Build ML models",
            url="https://example.com/1", contact_email="hr@testco.com",
        )
        self.assertIsNotNone(job_id)
        jobs = self.db.get_new_jobs_with_email()
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["title"], "AI Engineer")
        self.assertEqual(jobs[0]["contact_email"], "hr@testco.com")

    def test_duplicate_url_rejected(self):
        self.db.save_job("test", "Job A", "Co", "Dubai", "desc",
                         "https://example.com/dup", "a@co.com")
        result = self.db.save_job("test", "Job B", "Co", "Dubai", "desc",
                                  "https://example.com/dup", "b@co.com")
        self.assertIsNone(result)

    def test_duplicate_email_title_rejected(self):
        self.db.save_job("test", "ML Engineer", "Co", "Dubai", "desc",
                         None, "hr@firm.com")
        result = self.db.save_job("test", "ML Engineer", "Co2", "Remote", "other",
                                  None, "hr@firm.com")
        self.assertIsNone(result)

    def test_different_jobs_accepted(self):
        id1 = self.db.save_job("test", "Job A", "Co", "Dubai", "desc",
                               "https://a.com", "a@co.com")
        id2 = self.db.save_job("test", "Job B", "Co", "Dubai", "desc",
                               "https://b.com", "b@co.com")
        self.assertIsNotNone(id1)
        self.assertIsNotNone(id2)
        self.assertNotEqual(id1, id2)

    def test_save_application(self):
        job_id = self.db.save_job("test", "Role", "Co", "Dubai", "desc",
                                  "https://x.com", "hr@x.com")
        app_id = self.db.save_application(job_id, "hr@x.com",
                                          "Application for Role", "Hello...")
        self.assertIsNotNone(app_id)

    def test_mark_sent(self):
        job_id = self.db.save_job("test", "Role", "Co", "Dubai", "desc",
                                  "https://x.com", "hr@x.com")
        app_id = self.db.save_application(job_id, "hr@x.com", "Subj", "Body")
        self.db.mark_sent(app_id)
        self.db.mark_job_applied(job_id)

        stats = self.db.get_stats()
        self.assertEqual(stats["emails_sent"], 1)

    def test_stats_empty_db(self):
        stats = self.db.get_stats()
        self.assertEqual(stats["total_jobs"], 0)
        self.assertEqual(stats["jobs_with_email"], 0)
        self.assertEqual(stats["emails_sent"], 0)
        self.assertEqual(stats["emails_drafted"], 0)

    def test_stats_counts(self):
        self.db.save_job("test", "J1", "C", "D", "d", "https://1.com", "a@b.com")
        self.db.save_job("test", "J2", "C", "D", "d", "https://2.com", None)
        self.db.save_job("test", "J3", "C", "D", "d", "https://3.com", "c@d.com")

        stats = self.db.get_stats()
        self.assertEqual(stats["total_jobs"], 3)
        self.assertEqual(stats["jobs_with_email"], 2)

    def test_job_exists_by_url(self):
        self.db.save_job("test", "J", "C", "L", "d", "https://u.com", None)
        self.assertTrue(self.db.job_exists(url="https://u.com"))
        self.assertFalse(self.db.job_exists(url="https://other.com"))

    def test_job_exists_by_email_title(self):
        self.db.save_job("test", "Dev", "C", "L", "d", None, "x@y.com")
        self.assertTrue(self.db.job_exists(email="x@y.com", title="Dev"))
        self.assertFalse(self.db.job_exists(email="x@y.com", title="Other"))


if __name__ == "__main__":
    unittest.main()
