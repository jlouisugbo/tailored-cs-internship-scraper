import sqlite3
import pytest
from models import Job
import db


@pytest.fixture
def tmp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    db.init_db()
    return tmp_path / "test.db"


def make_job(**kwargs) -> Job:
    defaults = dict(
        company="Figma",
        title="Software Engineering Intern",
        url="https://boards.greenhouse.io/figma/jobs/1",
        location="Remote",
        source="greenhouse",
        category=1,
        discovered_at="2026-09-01T00:00:00+00:00",
    )
    return Job(**{**defaults, **kwargs})


def test_new_job_not_seen(tmp_db):
    job = make_job()
    with sqlite3.connect(tmp_db) as conn:
        assert not db.is_seen(conn, job.id)


def test_mark_seen_makes_job_visible(tmp_db):
    job = make_job()
    with sqlite3.connect(tmp_db) as conn:
        db.mark_seen(conn, job)
        assert db.is_seen(conn, job.id)


def test_mark_seen_twice_no_error_and_no_duplicate(tmp_db):
    job = make_job()
    with sqlite3.connect(tmp_db) as conn:
        db.mark_seen(conn, job)
        db.mark_seen(conn, job)
        count = conn.execute("SELECT COUNT(*) FROM seen_jobs").fetchone()[0]
    assert count == 1


def test_different_url_same_title_is_different_job(tmp_db):
    job_a = make_job(url="https://example.com/1")
    job_b = make_job(url="https://example.com/2")
    assert job_a.id != job_b.id
    with sqlite3.connect(tmp_db) as conn:
        db.mark_seen(conn, job_a)
        assert not db.is_seen(conn, job_b.id)


def test_add_to_digest_then_get(tmp_db):
    job = make_job()
    with sqlite3.connect(tmp_db) as conn:
        db.add_to_digest(conn, job)
        jobs = db.get_digest_jobs(conn)
    assert len(jobs) == 1
    assert jobs[0].company == "Figma"
    assert jobs[0].title == "Software Engineering Intern"


def test_get_digest_jobs_ordered_by_category(tmp_db):
    cat2 = make_job(company="Anthropic", category=2, url="https://example.com/a")
    cat1 = make_job(company="Figma", category=1, url="https://example.com/b")
    with sqlite3.connect(tmp_db) as conn:
        db.add_to_digest(conn, cat2)
        db.add_to_digest(conn, cat1)
        jobs = db.get_digest_jobs(conn)
    assert jobs[0].category == 1
    assert jobs[1].category == 2


def test_clear_digest_empties_queue(tmp_db):
    job = make_job()
    with sqlite3.connect(tmp_db) as conn:
        db.add_to_digest(conn, job)
        db.clear_digest(conn)
        assert db.get_digest_jobs(conn) == []


def test_clear_digest_does_not_affect_seen_jobs(tmp_db):
    job = make_job()
    with sqlite3.connect(tmp_db) as conn:
        db.mark_seen(conn, job)
        db.add_to_digest(conn, job)
        db.clear_digest(conn)
        assert db.is_seen(conn, job.id)
