import sqlite3
from pathlib import Path
from models import Job

DB_PATH = Path("data/seen_jobs.db")


def init_db() -> None:
    DB_PATH.parent.mkdir(exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS seen_jobs (
                id         TEXT PRIMARY KEY,
                company    TEXT NOT NULL,
                title      TEXT NOT NULL,
                url        TEXT NOT NULL,
                location   TEXT,
                source     TEXT NOT NULL,
                category   INTEGER NOT NULL,
                first_seen TEXT NOT NULL,
                last_seen  TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS digest_queue (
                id        TEXT PRIMARY KEY,
                company   TEXT NOT NULL,
                title     TEXT NOT NULL,
                url       TEXT NOT NULL,
                location  TEXT,
                source    TEXT NOT NULL,
                category  INTEGER NOT NULL,
                queued_at TEXT NOT NULL
            )
        """)
        conn.commit()


def is_seen(conn: sqlite3.Connection, job_id: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM seen_jobs WHERE id = ?", (job_id,)
    ).fetchone()
    return row is not None


def mark_seen(conn: sqlite3.Connection, job: Job) -> None:
    conn.execute(
        """
        INSERT INTO seen_jobs (id, company, title, url, location, source, category, first_seen, last_seen)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET last_seen = excluded.last_seen
        """,
        (job.id, job.company, job.title, job.url, job.location,
         job.source, job.category, job.discovered_at, job.discovered_at),
    )
    conn.commit()


def add_to_digest(conn: sqlite3.Connection, job: Job) -> None:
    conn.execute(
        """
        INSERT OR IGNORE INTO digest_queue
            (id, company, title, url, location, source, category, queued_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (job.id, job.company, job.title, job.url, job.location,
         job.source, job.category, job.discovered_at),
    )
    conn.commit()


def get_digest_jobs(conn: sqlite3.Connection) -> list[Job]:
    rows = conn.execute(
        """
        SELECT company, title, url, location, source, category, queued_at
        FROM digest_queue
        ORDER BY category ASC, queued_at ASC
        """
    ).fetchall()
    return [
        Job(
            company=r[0],
            title=r[1],
            url=r[2],
            location=r[3] or "",
            source=r[4],
            category=r[5],
            discovered_at=r[6],
        )
        for r in rows
    ]


def clear_digest(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM digest_queue")
    conn.commit()
