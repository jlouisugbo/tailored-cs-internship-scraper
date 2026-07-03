import json
import logging
import re
from datetime import datetime, timezone

import httpx

from location_filter import is_us_location
from models import Job

logger = logging.getLogger(__name__)


async def fetch_github_repo(
    repo: str,
    branch: str,
    path: str,
    company_names: frozenset[str],
    keywords: frozenset[str],
) -> list[Job]:
    url = f"https://raw.githubusercontent.com/{repo}/{branch}/{path}"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url)
        if resp.status_code == 404:
            return []
        resp.raise_for_status()
        content = resp.text
    except Exception as exc:
        logger.warning("github_repo fetch failed repo=%s: %s", repo, exc)
        return []

    now = datetime.now(timezone.utc).isoformat()
    if path.endswith(".json"):
        return _parse_json(content, company_names, keywords, now)
    return _parse_markdown(content, company_names, keywords, now)


def _parse_markdown(
    content: str,
    company_names: frozenset[str],
    keywords: frozenset[str],
    now: str,
) -> list[Job]:
    jobs = []
    for line in content.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|") if c.strip()]
        if len(cells) < 2:
            continue
        line_lower = line.lower()
        matched_company = next(
            (n for n in company_names if n.lower() in line_lower), None
        )
        if not matched_company:
            continue
        title_cell = cells[1] if len(cells) > 1 else ""
        if not any(re.search(rf'\b{re.escape(kw)}\b', title_cell.lower()) for kw in keywords):
            continue
        location = cells[2] if len(cells) > 2 else ""
        if not is_us_location(location):
            continue
        url_match = re.search(r'\[.*?\]\((https?://[^)]+)\)', line)
        url = url_match.group(1) if url_match else ""
        jobs.append(
            Job(
                company=matched_company,
                title=title_cell,
                url=url,
                location=location,
                source="github_repo",
                category=0,
                discovered_at=now,
            )
        )
    return jobs


def _parse_json(
    content: str,
    company_names: frozenset[str],
    keywords: frozenset[str],
    now: str,
) -> list[Job]:
    try:
        listings = json.loads(content)
    except json.JSONDecodeError as exc:
        logger.warning("github_repo JSON parse failed: %s", exc)
        return []
    jobs = []
    names_lower = {n.lower(): n for n in company_names}
    for item in listings:
        raw_company = item.get("company_name") or item.get("company", "")
        matched = names_lower.get(raw_company.lower())
        if not matched:
            continue
        title = item.get("title") or item.get("role", "")
        if not any(re.search(rf'\b{re.escape(kw)}\b', title.lower()) for kw in keywords):
            continue
        location = item.get("location", "")
        if not is_us_location(location):
            continue
        jobs.append(
            Job(
                company=matched,
                title=title,
                url=item.get("url") or item.get("link", ""),
                location=location,
                source="github_repo",
                category=0,
                discovered_at=now,
            )
        )
    return jobs
