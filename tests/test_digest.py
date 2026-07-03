import sqlite3
from unittest.mock import patch
import db
from models import Job


def make_job(url_suffix: str = "1") -> Job:
    return Job(
        company="Figma",
        title="SWE Intern",
        url=f"https://example.com/{url_suffix}",
        location="Remote",
        source="greenhouse",
        category=1,
        discovered_at="2026-09-01T00:00:00+00:00",
    )


def test_sends_email_when_queue_has_jobs(tmp_db, minimal_config):
    job = make_job()
    with sqlite3.connect(tmp_db) as conn:
        db.add_to_digest(conn, job)

    with patch("digest.load_config", return_value=minimal_config), \
         patch("digest.send_digest") as mock_send:
        import digest
        digest.run()
        mock_send.assert_called_once()
        sent_jobs = mock_send.call_args[0][0]
        assert len(sent_jobs) == 1
        assert sent_jobs[0].company == "Figma"


def test_skips_email_when_queue_is_empty(tmp_db, minimal_config):
    with patch("digest.load_config", return_value=minimal_config), \
         patch("digest.send_digest") as mock_send:
        import digest
        digest.run()
        mock_send.assert_not_called()


def test_clears_queue_after_successful_send(tmp_db, minimal_config):
    job = make_job()
    with sqlite3.connect(tmp_db) as conn:
        db.add_to_digest(conn, job)

    with patch("digest.load_config", return_value=minimal_config), \
         patch("digest.send_digest"):
        import digest
        digest.run()

    with sqlite3.connect(tmp_db) as conn:
        assert db.get_digest_jobs(conn) == []


def test_does_not_clear_queue_on_send_failure(tmp_db, minimal_config):
    job = make_job()
    with sqlite3.connect(tmp_db) as conn:
        db.add_to_digest(conn, job)

    with patch("digest.load_config", return_value=minimal_config), \
         patch("digest.send_digest", side_effect=Exception("SMTP error")):
        import digest
        digest.run()  # must not raise

    with sqlite3.connect(tmp_db) as conn:
        remaining = db.get_digest_jobs(conn)
    assert len(remaining) == 1
