import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import db
from config_loader import (
    Config,
    CompanyConfig,
    GithubRepoConfig,
    NotificationConfig,
)


@pytest.fixture
def tmp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    db.init_db()
    return tmp_path / "test.db"


@pytest.fixture
def minimal_config():
    return Config(
        keywords=frozenset(["intern"]),
        companies=[
            CompanyConfig(name="Figma", category=1, slug="figma"),
        ],
        github_repos=[
            GithubRepoConfig(
                repo="vanshb03/Summer2027-Internships",
                branch="dev",
                path="README.md",
            )
        ],
        notification=NotificationConfig(
            discord_webhook_env="DISCORD_WEBHOOK_URL",
            email_to="you@example.com",
            email_from_env="GMAIL_ADDRESS",
            email_password_env="GMAIL_APP_PASSWORD",
            digest_hour_utc=1,
            discord_ping_user_id="999999999999999999",
            discord_ping_categories=frozenset({1}),
        ),
    )
