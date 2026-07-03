import pytest
from config_loader import load_config, CompanyConfig


def test_loads_keywords(tmp_path):
    cfg = tmp_path / "companies.yaml"
    cfg.write_text("""
keywords:
  - intern
  - internship
notification:
  discord_webhook_env: DISCORD_WEBHOOK_URL
  email_to: test@example.com
  email_from_env: GMAIL_ADDRESS
  email_password_env: GMAIL_APP_PASSWORD
  digest_hour_utc: 1
github_repos: []
companies:
  - { name: Figma, category: 1, slug: figma }
""")
    config = load_config(str(cfg))
    assert "intern" in config.keywords
    assert "internship" in config.keywords


def test_keywords_are_lowercased(tmp_path):
    cfg = tmp_path / "companies.yaml"
    cfg.write_text("""
keywords:
  - Intern
  - Co-Op
notification:
  discord_webhook_env: X
  email_to: x@x.com
  email_from_env: X
  email_password_env: X
  digest_hour_utc: 1
github_repos: []
companies: []
""")
    config = load_config(str(cfg))
    assert "intern" in config.keywords
    assert "co-op" in config.keywords


def test_company_default_slug_used_for_all_ats(tmp_path):
    cfg = tmp_path / "companies.yaml"
    cfg.write_text("""
keywords: [intern]
notification:
  discord_webhook_env: X
  email_to: x@x.com
  email_from_env: X
  email_password_env: X
  digest_hour_utc: 1
github_repos: []
companies:
  - { name: Figma, category: 1, slug: figma }
""")
    config = load_config(str(cfg))
    company = config.companies[0]
    assert company.get_slug("greenhouse") == "figma"
    assert company.get_slug("lever") == "figma"
    assert company.get_slug("ashby") == "figma"


def test_company_slug_greenhouse_override(tmp_path):
    cfg = tmp_path / "companies.yaml"
    cfg.write_text("""
keywords: [intern]
notification:
  discord_webhook_env: X
  email_to: x@x.com
  email_from_env: X
  email_password_env: X
  digest_hour_utc: 1
github_repos: []
companies:
  - { name: Block, category: 3, slug: block, slug_greenhouse: block-inc }
""")
    config = load_config(str(cfg))
    company = config.companies[0]
    assert company.get_slug("greenhouse") == "block-inc"
    assert company.get_slug("lever") == "block"
    assert company.get_slug("ashby") == "block"


def test_company_slug_workday_parsed(tmp_path):
    cfg = tmp_path / "companies.yaml"
    cfg.write_text("""
keywords: [intern]
notification:
  discord_webhook_env: X
  email_to: x@x.com
  email_from_env: X
  email_password_env: X
  digest_hour_utc: 1
github_repos: []
companies:
  - { name: Acme, category: 1, slug: acme, slug_workday: { tenant: acme, host: wd1, site: External } }
""")
    config = load_config(str(cfg))
    workday = config.companies[0].slug_workday
    assert workday.tenant == "acme"
    assert workday.host == "wd1"
    assert workday.site == "External"
    assert workday.applied_facets is None


def test_company_without_slug_workday_defaults_to_none(tmp_path):
    cfg = tmp_path / "companies.yaml"
    cfg.write_text("""
keywords: [intern]
notification:
  discord_webhook_env: X
  email_to: x@x.com
  email_from_env: X
  email_password_env: X
  digest_hour_utc: 1
github_repos: []
companies:
  - { name: Figma, category: 1, slug: figma }
""")
    config = load_config(str(cfg))
    assert config.companies[0].slug_workday is None


def test_github_repos_parsed(tmp_path):
    cfg = tmp_path / "companies.yaml"
    cfg.write_text("""
keywords: [intern]
notification:
  discord_webhook_env: X
  email_to: x@x.com
  email_from_env: X
  email_password_env: X
  digest_hour_utc: 1
github_repos:
  - { repo: vanshb03/Summer2027-Internships, branch: dev, path: README.md, priority: primary }
companies: []
""")
    config = load_config(str(cfg))
    assert len(config.github_repos) == 1
    assert config.github_repos[0].repo == "vanshb03/Summer2027-Internships"
    assert config.github_repos[0].branch == "dev"


def test_notification_config_parsed(tmp_path):
    cfg = tmp_path / "companies.yaml"
    cfg.write_text("""
keywords: [intern]
notification:
  discord_webhook_env: DISCORD_WEBHOOK_URL
  email_to: you@example.com
  email_from_env: GMAIL_ADDRESS
  email_password_env: GMAIL_APP_PASSWORD
  digest_hour_utc: 1
github_repos: []
companies: []
""")
    config = load_config(str(cfg))
    assert config.notification.email_to == "you@example.com"
    assert config.notification.digest_hour_utc == 1


def test_discord_ping_settings_default_to_disabled(tmp_path):
    cfg = tmp_path / "companies.yaml"
    cfg.write_text("""
keywords: [intern]
notification:
  discord_webhook_env: X
  email_to: x@x.com
  email_from_env: X
  email_password_env: X
  digest_hour_utc: 1
github_repos: []
companies: []
""")
    config = load_config(str(cfg))
    assert config.notification.discord_ping_user_id == ""
    assert config.notification.discord_ping_categories == frozenset()


def test_discord_ping_settings_parsed_when_present(tmp_path):
    cfg = tmp_path / "companies.yaml"
    cfg.write_text("""
keywords: [intern]
notification:
  discord_webhook_env: X
  email_to: x@x.com
  email_from_env: X
  email_password_env: X
  digest_hour_utc: 1
  discord_ping_user_id: "123456789012345678"
  discord_ping_categories: [1, 2]
github_repos: []
companies: []
""")
    config = load_config(str(cfg))
    assert config.notification.discord_ping_user_id == "123456789012345678"
    assert config.notification.discord_ping_categories == frozenset({1, 2})
