import logging
import re
from datetime import datetime, timezone

import httpx

from location_filter import is_us_location
from models import Job

logger = logging.getLogger(__name__)


def _matches(title: str, keywords: frozenset[str]) -> bool:
    t = title.lower()
    return any(re.search(rf'\b{re.escape(kw)}\b', t) for kw in keywords)


async def fetch_greenhouse(
    slug: str,
    keywords: frozenset[str],
    company_name: str,
    category: int,
) -> list[Job]:
    url = f"https://boards.greenhouse.io/v1/boards/{slug}/jobs"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
        if resp.status_code == 404:
            return []
        resp.raise_for_status()
        data = resp.json()
        now = datetime.now(timezone.utc).isoformat()
        jobs = []
        for item in data.get("jobs", []):
            title = item.get("title", "")
            if not _matches(title, keywords):
                continue
            location = (item.get("location") or {}).get("name", "")
            if not is_us_location(location):
                continue
            jobs.append(
                Job(
                    company=company_name,
                    title=title,
                    url=item.get("absolute_url", ""),
                    location=location,
                    source="greenhouse",
                    category=category,
                    discovered_at=now,
                )
            )
        return jobs
    except Exception as exc:
        logger.warning("greenhouse fetch failed slug=%s: %s", slug, exc)
        return []
