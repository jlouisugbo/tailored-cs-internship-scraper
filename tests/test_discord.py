import json
import httpx
from models import Job
from notifiers.discord import send_alert, send_batched_alert, COLORS


def make_job(category: int = 1, company: str = "Figma", title: str = "Software Engineering Intern") -> Job:
    return Job(
        company=company,
        title=title,
        url="https://boards.greenhouse.io/figma/jobs/1",
        location="Remote",
        source="greenhouse",
        category=category,
        discovered_at="2026-09-01T00:00:00+00:00",
    )


async def test_posts_embed_to_webhook(httpx_mock, monkeypatch):
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/test/token")
    httpx_mock.add_response(
        url="https://discord.com/api/webhooks/test/token",
        status_code=204,
    )
    await send_alert(make_job())
    requests = httpx_mock.get_requests()
    assert len(requests) == 1
    body = json.loads(requests[0].content)
    assert body["embeds"][0]["title"] == "New Intern Role — Figma"
    assert "Software Engineering Intern" in body["embeds"][0]["description"]
    assert "https://boards.greenhouse.io/figma/jobs/1" in body["embeds"][0]["description"]


async def test_category_1_uses_green_color(httpx_mock, monkeypatch):
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/test/token")
    httpx_mock.add_response(url="https://discord.com/api/webhooks/test/token", status_code=204)
    await send_alert(make_job(category=1))
    body = json.loads(httpx_mock.get_requests()[0].content)
    assert body["embeds"][0]["color"] == COLORS[1]


async def test_category_0_uses_gray_color(httpx_mock, monkeypatch):
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/test/token")
    httpx_mock.add_response(url="https://discord.com/api/webhooks/test/token", status_code=204)
    await send_alert(make_job(category=0))
    body = json.loads(httpx_mock.get_requests()[0].content)
    assert body["embeds"][0]["color"] == COLORS[0]


async def test_send_alert_never_pings(httpx_mock, monkeypatch):
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/test/token")
    httpx_mock.add_response(url="https://discord.com/api/webhooks/test/token", status_code=204)
    await send_alert(make_job(category=1))
    body = json.loads(httpx_mock.get_requests()[0].content)
    assert "content" not in body
    assert "allowed_mentions" not in body


async def test_does_not_raise_on_webhook_failure(httpx_mock, monkeypatch, caplog):
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/test/token")
    httpx_mock.add_exception(
        url="https://discord.com/api/webhooks/test/token",
        exception=httpx.ConnectError("timeout"),
    )
    await send_alert(make_job())  # must not raise
    assert "discord alert failed" in caplog.text


async def test_batched_alert_sends_one_message_for_multiple_roles(httpx_mock, monkeypatch):
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/test/token")
    httpx_mock.add_response(url="https://discord.com/api/webhooks/test/token", status_code=204)
    jobs = [
        make_job(company="Figma", title="Role 1"),
        make_job(company="Mercury", title="Role 2"),
        make_job(company="Vercel", title="Role 3"),
    ]
    await send_batched_alert(jobs, ping_user_id="999999999999999999")
    requests = httpx_mock.get_requests()
    assert len(requests) == 1
    body = json.loads(requests[0].content)
    assert len(body["embeds"]) == 3
    assert body["content"] == "<@999999999999999999>"
    assert body["allowed_mentions"] == {"parse": ["users"]}


async def test_batched_alert_no_ping_when_user_id_not_configured(httpx_mock, monkeypatch):
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/test/token")
    httpx_mock.add_response(url="https://discord.com/api/webhooks/test/token", status_code=204)
    await send_batched_alert([make_job()])
    body = json.loads(httpx_mock.get_requests()[0].content)
    assert "content" not in body
    assert "allowed_mentions" not in body


async def test_batched_alert_does_nothing_for_empty_list(httpx_mock, monkeypatch):
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/test/token")
    await send_batched_alert([])
    assert httpx_mock.get_requests() == []


async def test_batched_alert_splits_into_chunks_of_ten(httpx_mock, monkeypatch):
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/test/token")
    httpx_mock.add_response(url="https://discord.com/api/webhooks/test/token", status_code=204)
    httpx_mock.add_response(url="https://discord.com/api/webhooks/test/token", status_code=204)
    jobs = [make_job(company=f"Company{i}", title=f"Role {i}") for i in range(12)]
    await send_batched_alert(jobs, ping_user_id="999999999999999999")
    requests = httpx_mock.get_requests()
    assert len(requests) == 2
    first_body = json.loads(requests[0].content)
    second_body = json.loads(requests[1].content)
    assert len(first_body["embeds"]) == 10
    assert len(second_body["embeds"]) == 2
    assert first_body["content"] == "<@999999999999999999>"
    assert second_body["content"] == "<@999999999999999999>"
