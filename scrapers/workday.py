import logging
import re
from datetime import datetime, timezone

import httpx

from location_filter import is_us_location
from models import Job

logger = logging.getLogger(__name__)

# Workday's CXS job-board API is per-tenant: {tenant} is the company's
# Workday account name, {host} is the wdN shard it's provisioned on (varies
# per tenant, discovered by inspecting the company's careers page network
# requests), {site} is the named career site (commonly "External").
JOBS_URL = "https://{tenant}.{host}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs"
CAREERS_BASE_URL = "https://{tenant}.{host}.myworkdayjobs.com/{site}"

PAGE_SIZE = 20
MAX_JOBS_PER_COMPANY = 5000  # guards a runaway tenant; real catalogs exit early via the < PAGE_SIZE check


def _matches(title: str, keywords: frozenset[str]) -> bool:
    t = title.lower()
    return any(re.search(rf'\b{re.escape(kw)}\b', t) for kw in keywords)


async def fetch_workday(
    tenant: str,
    host: str,
    site: str,
    keywords: frozenset[str],
    company_name: str,
    category: int,
    applied_facets: dict[str, list[str]] | None = None,
) -> list[Job]:
    url = JOBS_URL.format(tenant=tenant, host=host, site=site)
    careers_base = CAREERS_BASE_URL.format(tenant=tenant, host=host, site=site)
    jobs: list[Job] = []
    offset = 0

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            now = datetime.now(timezone.utc).isoformat()
            while offset < MAX_JOBS_PER_COMPANY:
                resp = await client.post(
                    url,
                    json={
                        "appliedFacets": applied_facets or {},
                        "limit": PAGE_SIZE,
                        "offset": offset,
                        "searchText": "",
                    },
                )
                if resp.status_code == 404:
                    return []
                resp.raise_for_status()

                postings = resp.json().get("jobPostings", [])
                if not postings:
                    break

                for posting in postings:
                    title = posting.get("title", "")
                    if not _matches(title, keywords):
                        continue
                    location = posting.get("locationsText", "")
                    if not is_us_location(location):
                        continue
                    jobs.append(
                        Job(
                            company=company_name,
                            title=title,
                            url=careers_base + posting.get("externalPath", ""),
                            location=location,
                            source="workday",
                            category=category,
                            discovered_at=now,
                        )
                    )

                if len(postings) < PAGE_SIZE:
                    break
                offset += PAGE_SIZE
    except Exception as exc:
        logger.warning("workday fetch failed for %s (%s/%s): %s", company_name, tenant, site, exc)
        return []

    return jobs
