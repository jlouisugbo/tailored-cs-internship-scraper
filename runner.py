import asyncio
import logging
import sqlite3

import db
from config_loader import load_config
from notifiers.discord import send_alert, send_batched_alert
from scrapers.ashby import fetch_ashby
from scrapers.github_repo import fetch_github_repo
from scrapers.greenhouse import fetch_greenhouse
from scrapers.lever import fetch_lever
from scrapers.workday import fetch_workday

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


async def run() -> None:
    config = load_config()
    keywords = config.keywords
    company_names = frozenset(c.name for c in config.companies)

    db.init_db()

    tasks = []
    for company in config.companies:
        tasks.append(fetch_greenhouse(company.get_slug("greenhouse"), keywords, company.name, company.category))
        tasks.append(fetch_lever(     company.get_slug("lever"),      keywords, company.name, company.category))
        tasks.append(fetch_ashby(     company.get_slug("ashby"),      keywords, company.name, company.category))
        if company.slug_workday:
            w = company.slug_workday
            tasks.append(
                fetch_workday(w.tenant, w.host, w.site, keywords, company.name, company.category, applied_facets=w.applied_facets)
            )

    for repo_cfg in config.github_repos:
        tasks.append(
            fetch_github_repo(repo_cfg.repo, repo_cfg.branch, repo_cfg.path, company_names, keywords)
        )

    results = await asyncio.gather(*tasks)
    all_jobs = [job for job_list in results for job in job_list]
    logger.info("scraped %d raw hits across all sources", len(all_jobs))

    new_jobs = []
    with sqlite3.connect(db.DB_PATH) as conn:
        for job in all_jobs:
            if not db.is_seen(conn, job.id):
                db.mark_seen(conn, job)
                db.add_to_digest(conn, job)
                new_jobs.append(job)

    logger.info("found %d new jobs", len(new_jobs))

    if new_jobs:
        ping_categories = config.notification.discord_ping_categories
        ping_jobs = [job for job in new_jobs if job.category in ping_categories]
        other_jobs = [job for job in new_jobs if job.category not in ping_categories]
        await send_batched_alert(ping_jobs, config.notification.discord_ping_user_id)
        for job in other_jobs:
            await send_alert(job)
        logger.info("discord alerts sent for %d jobs", len(new_jobs))


if __name__ == "__main__":
    asyncio.run(run())
