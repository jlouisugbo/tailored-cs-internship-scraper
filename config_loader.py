from dataclasses import dataclass
import yaml


@dataclass
class WorkdaySlug:
    tenant: str
    host: str
    site: str
    # Optional Workday facet filter, for shared/multi-brand tenants where a
    # parent company's subsidiaries all post through one tenant. Keys/values
    # must match Workday's own facet IDs for that tenant.
    applied_facets: dict[str, list[str]] | None = None


@dataclass
class CompanyConfig:
    name: str
    category: int
    slug: str
    slug_greenhouse: str = ""
    slug_lever: str = ""
    slug_ashby: str = ""
    slug_workday: WorkdaySlug | None = None

    def get_slug(self, ats: str) -> str:
        override = getattr(self, f"slug_{ats}", "")
        return override or self.slug


@dataclass
class GithubRepoConfig:
    repo: str
    branch: str
    path: str
    priority: str = "primary"


@dataclass
class NotificationConfig:
    discord_webhook_env: str
    email_to: str
    email_from_env: str
    email_password_env: str
    digest_hour_utc: int
    discord_ping_user_id: str = ""
    discord_ping_categories: frozenset[int] = frozenset()


@dataclass
class Config:
    keywords: frozenset[str]
    companies: list[CompanyConfig]
    github_repos: list[GithubRepoConfig]
    notification: NotificationConfig


def _parse_workday_slug(raw: dict | None) -> WorkdaySlug | None:
    if not raw:
        return None
    return WorkdaySlug(
        tenant=raw["tenant"],
        host=raw["host"],
        site=raw["site"],
        applied_facets=raw.get("applied_facets"),
    )


def load_config(path: str = "config/companies.yaml") -> Config:
    with open(path) as f:
        data = yaml.safe_load(f)

    keywords = frozenset(kw.lower() for kw in data["keywords"])

    companies = [
        CompanyConfig(
            name=c["name"],
            category=c["category"],
            slug=c["slug"],
            slug_greenhouse=c.get("slug_greenhouse", ""),
            slug_lever=c.get("slug_lever", ""),
            slug_ashby=c.get("slug_ashby", ""),
            slug_workday=_parse_workday_slug(c.get("slug_workday")),
        )
        for c in data.get("companies", [])
    ]

    github_repos = [
        GithubRepoConfig(
            repo=r["repo"],
            branch=r["branch"],
            path=r["path"],
            priority=r.get("priority", "primary"),
        )
        for r in data.get("github_repos", [])
    ]

    n = data["notification"]
    notification = NotificationConfig(
        discord_webhook_env=n["discord_webhook_env"],
        email_to=n["email_to"],
        email_from_env=n["email_from_env"],
        email_password_env=n["email_password_env"],
        digest_hour_utc=int(n["digest_hour_utc"]),
        discord_ping_user_id=n.get("discord_ping_user_id", ""),
        discord_ping_categories=frozenset(n.get("discord_ping_categories", [])),
    )

    return Config(
        keywords=keywords,
        companies=companies,
        github_repos=github_repos,
        notification=notification,
    )
