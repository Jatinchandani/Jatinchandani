"""Live integration tests — actually hit the free APIs (no keys needed)."""

import unittest
from job_hunter.scanners import remotive, arbeitnow, themuse, rss_feeds
from job_hunter.scanners.base import JobPosting


class TestRemotiveLive(unittest.TestCase):

    def test_scan_returns_jobs(self):
        jobs = remotive.scan(["python"])
        self.assertIsInstance(jobs, list)
        self.assertGreater(len(jobs), 0, "Remotive should return jobs for 'python'")

    def test_job_structure(self):
        jobs = remotive.scan(["data"])
        if jobs:
            job = jobs[0]
            self.assertIsInstance(job, JobPosting)
            self.assertEqual(job.source, "remotive")
            self.assertTrue(len(job.title) > 0)

    def test_multiple_keywords(self):
        jobs = remotive.scan(["AI", "machine learning"])
        self.assertIsInstance(jobs, list)


class TestArbeitnowLive(unittest.TestCase):

    def test_scan_returns_list(self):
        jobs = arbeitnow.scan(["python", "data", "engineer"])
        self.assertIsInstance(jobs, list)

    def test_filters_by_keyword(self):
        all_jobs = arbeitnow.scan(["xyznonexistentkeyword123"])
        self.assertEqual(len(all_jobs), 0)


class TestTheMuseLive(unittest.TestCase):

    def test_scan_returns_list(self):
        jobs = themuse.scan(["engineer"])
        self.assertIsInstance(jobs, list)


class TestRSSFeedsLive(unittest.TestCase):

    def test_scan_returns_list(self):
        jobs = rss_feeds.scan(["python", "data", "engineer", "developer"])
        self.assertIsInstance(jobs, list)

    def test_job_structure(self):
        jobs = rss_feeds.scan(["python", "developer", "engineer"])
        if jobs:
            job = jobs[0]
            self.assertIsInstance(job, JobPosting)
            self.assertEqual(job.source, "rss")


class TestScannersWithoutKeys(unittest.TestCase):
    """Scanners that need API keys should return empty lists gracefully."""

    def test_adzuna_no_key(self):
        from job_hunter.scanners import adzuna
        jobs = adzuna.scan(["python"], app_id="", api_key="")
        self.assertEqual(jobs, [])

    def test_google_search_no_key(self):
        from job_hunter.scanners import google_search
        jobs = google_search.scan(["python"], api_key="", cx="")
        self.assertEqual(jobs, [])

    def test_serp_linkedin_no_key(self):
        from job_hunter.scanners import serp_linkedin
        jobs = serp_linkedin.scan(["python"], serp_api_key="")
        self.assertEqual(jobs, [])

    def test_linkedin_posts_no_key(self):
        from job_hunter.scanners import linkedin_posts
        jobs = linkedin_posts.scan(["python"])
        self.assertEqual(jobs, [])

    def test_linkedin_alerts_no_creds(self):
        from job_hunter.scanners import linkedin_email_alerts
        jobs = linkedin_email_alerts.scan()
        self.assertEqual(jobs, [])


if __name__ == "__main__":
    unittest.main()
