import sqlite3
from unittest.mock import AsyncMock, patch
import db
from models import Job


def make_job(company: str = "Figma", url_suffix: str = "1", category: int = 1) -> Job:
    return Job(
        company=company,
        title="SWE Intern",
        url=f"https://example.com/{url_suffix}",
        location="Remote",
        source="greenhouse",
        category=category,
        discovered_at="2026-09-01T00:00:00+00:00",
    )


async def test_new_category_1_job_triggers_batched_discord_alert(tmp_db, minimal_config):
    job = make_job()
    with patch("runner.load_config", return_value=minimal_config), \
         patch("runner.fetch_greenhouse", return_value=[job]), \
         patch("runner.fetch_lever",      return_value=[]), \
         patch("runner.fetch_ashby",      return_value=[]), \
         patch("runner.fetch_github_repo",return_value=[]), \
         patch("runner.send_alert", new_callable=AsyncMock) as mock_alert, \
         patch("runner.send_batched_alert", new_callable=AsyncMock) as mock_batched:
        import runner
        await runner.run()
        mock_batched.assert_called_once_with([job], "999999999999999999")
        mock_alert.assert_not_called()


async def test_new_non_category_1_job_uses_individual_alert(tmp_db, minimal_config):
    job = make_job(category=2)
    with patch("runner.load_config", return_value=minimal_config), \
         patch("runner.fetch_greenhouse", return_value=[job]), \
         patch("runner.fetch_lever",      return_value=[]), \
         patch("runner.fetch_ashby",      return_value=[]), \
         patch("runner.fetch_github_repo",return_value=[]), \
         patch("runner.send_alert", new_callable=AsyncMock) as mock_alert, \
         patch("runner.send_batched_alert", new_callable=AsyncMock) as mock_batched:
        import runner
        await runner.run()
        mock_alert.assert_called_once_with(job)
        mock_batched.assert_called_once_with([], "999999999999999999")


async def test_multiple_category_1_jobs_in_one_run_are_batched_together(tmp_db, minimal_config):
    job1 = make_job(company="Figma", url_suffix="1")
    job2 = make_job(company="Mercury", url_suffix="2")
    with patch("runner.load_config", return_value=minimal_config), \
         patch("runner.fetch_greenhouse", return_value=[job1, job2]), \
         patch("runner.fetch_lever",      return_value=[]), \
         patch("runner.fetch_ashby",      return_value=[]), \
         patch("runner.fetch_github_repo",return_value=[]), \
         patch("runner.send_alert", new_callable=AsyncMock), \
         patch("runner.send_batched_alert", new_callable=AsyncMock) as mock_batched:
        import runner
        await runner.run()
        mock_batched.assert_called_once_with([job1, job2], "999999999999999999")


async def test_seen_job_not_re_alerted(tmp_db, minimal_config):
    job = make_job()
    with sqlite3.connect(tmp_db) as conn:
        db.mark_seen(conn, job)

    with patch("runner.load_config", return_value=minimal_config), \
         patch("runner.fetch_greenhouse", return_value=[job]), \
         patch("runner.fetch_lever",      return_value=[]), \
         patch("runner.fetch_ashby",      return_value=[]), \
         patch("runner.fetch_github_repo",return_value=[]), \
         patch("runner.send_alert", new_callable=AsyncMock) as mock_alert, \
         patch("runner.send_batched_alert", new_callable=AsyncMock) as mock_batched:
        import runner
        await runner.run()
        mock_alert.assert_not_called()
        mock_batched.assert_not_called()


async def test_new_job_added_to_digest_queue(tmp_db, minimal_config):
    job = make_job()
    with patch("runner.load_config", return_value=minimal_config), \
         patch("runner.fetch_greenhouse", return_value=[job]), \
         patch("runner.fetch_lever",      return_value=[]), \
         patch("runner.fetch_ashby",      return_value=[]), \
         patch("runner.fetch_github_repo",return_value=[]), \
         patch("runner.send_alert", new_callable=AsyncMock), \
         patch("runner.send_batched_alert", new_callable=AsyncMock):
        import runner
        await runner.run()

    with sqlite3.connect(tmp_db) as conn:
        queued = db.get_digest_jobs(conn)
    assert len(queued) == 1
    assert queued[0].company == "Figma"


async def test_duplicate_across_sources_only_alerted_once(tmp_db, minimal_config):
    job = make_job()
    with patch("runner.load_config", return_value=minimal_config), \
         patch("runner.fetch_greenhouse", return_value=[job]), \
         patch("runner.fetch_lever",      return_value=[job]),  \
         patch("runner.fetch_ashby",      return_value=[job]),  \
         patch("runner.fetch_github_repo",return_value=[]), \
         patch("runner.send_alert", new_callable=AsyncMock), \
         patch("runner.send_batched_alert", new_callable=AsyncMock) as mock_batched:
        import runner
        await runner.run()
        mock_batched.assert_called_once_with([job], "999999999999999999")
