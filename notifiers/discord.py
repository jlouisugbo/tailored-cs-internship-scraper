import asyncio
import logging
import os

import httpx

from models import Job

logger = logging.getLogger(__name__)

COLORS: dict[int, int] = {
    1: 5763719,   # green
    2: 3447003,   # blue
    3: 16776960,  # yellow
    0: 9807270,   # gray — github_repo source
}

MAX_EMBEDS_PER_MESSAGE = 10  # Discord's hard limit per message


def _build_embed(job: Job) -> dict:
    label = f"Cat {job.category}" if job.category > 0 else "GitHub Repo"
    return {
        "title": f"New Intern Role — {job.company}",
        "description": (
            f"**{job.title}** | {job.location}\n[Apply →]({job.url})"
        ),
        "color": COLORS.get(job.category, COLORS[0]),
        "fields": [
            {"name": "Source",   "value": job.source, "inline": True},
            {"name": "Category", "value": label,       "inline": True},
        ],
        "timestamp": job.discovered_at,
    }


async def _post(webhook_url: str, payload: dict, log_label: str) -> None:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(webhook_url, json=payload)
        resp.raise_for_status()
        await asyncio.sleep(0.5)  # stay under Discord's ~5 req/s webhook limit
    except Exception as exc:
        logger.error("discord alert failed %s: %s", log_label, exc)


async def send_alert(job: Job) -> None:
    webhook_url = os.environ["DISCORD_WEBHOOK_URL"]
    payload = {"embeds": [_build_embed(job)]}
    await _post(webhook_url, payload, f"company={job.company} title={job.title}")


async def send_batched_alert(jobs: list[Job], ping_user_id: str = "") -> None:
    if not jobs:
        return
    webhook_url = os.environ["DISCORD_WEBHOOK_URL"]
    for i in range(0, len(jobs), MAX_EMBEDS_PER_MESSAGE):
        chunk = jobs[i:i + MAX_EMBEDS_PER_MESSAGE]
        payload: dict = {"embeds": [_build_embed(job) for job in chunk]}
        if ping_user_id:
            payload["content"] = f"<@{ping_user_id}>"
            payload["allowed_mentions"] = {"parse": ["users"]}
        await _post(webhook_url, payload, f"batch of {len(chunk)} roles")
