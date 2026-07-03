import httpx
import pytest
from scrapers.ashby import fetch_ashby

KEYWORDS = frozenset(["intern", "internship"])


async def test_returns_matching_intern_jobs(httpx_mock):
    httpx_mock.add_response(
        url="https://api.ashbyhq.com/posting-api/job-board/vercel",
        json={
            "jobs": [
                {
                    "title": "Frontend Engineering Intern",
                    "jobUrl": "https://jobs.ashbyhq.com/vercel/1",
                    "location": "Remote",
                },
                {
                    "title": "Staff Engineer",
                    "jobUrl": "https://jobs.ashbyhq.com/vercel/2",
                    "location": "SF",
                },
            ]
        },
    )
    jobs = await fetch_ashby("vercel", KEYWORDS, "Vercel", 1)
    assert len(jobs) == 1
    assert jobs[0].title == "Frontend Engineering Intern"
    assert jobs[0].source == "ashby"
    assert jobs[0].location == "Remote"


async def test_filters_out_non_us_location(httpx_mock):
    httpx_mock.add_response(
        url="https://api.ashbyhq.com/posting-api/job-board/vercel",
        json={
            "jobs": [
                {"title": "Frontend Engineering Intern", "jobUrl": "https://example.com/1", "location": "Bangalore, India"},
                {"title": "Frontend Engineering Intern", "jobUrl": "https://example.com/2", "location": "New York, NY"},
            ]
        },
    )
    jobs = await fetch_ashby("vercel", KEYWORDS, "Vercel", 1)
    assert len(jobs) == 1
    assert jobs[0].url == "https://example.com/2"


async def test_returns_empty_on_404(httpx_mock):
    httpx_mock.add_response(
        url="https://api.ashbyhq.com/posting-api/job-board/notacompany",
        status_code=404,
    )
    jobs = await fetch_ashby("notacompany", KEYWORDS, "NotACompany", 1)
    assert jobs == []


async def test_returns_empty_on_network_error(httpx_mock):
    httpx_mock.add_exception(
        url="https://api.ashbyhq.com/posting-api/job-board/vercel",
        exception=httpx.ConnectError("timeout"),
    )
    jobs = await fetch_ashby("vercel", KEYWORDS, "Vercel", 1)
    assert jobs == []
