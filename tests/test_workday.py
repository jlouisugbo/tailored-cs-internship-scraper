import json

import httpx
from scrapers.workday import fetch_workday

KEYWORDS = frozenset(["intern", "internship"])
JOBS_URL = "https://acme.wd1.myworkdayjobs.com/wday/cxs/acme/External/jobs"


async def test_returns_matching_intern_jobs(httpx_mock):
    httpx_mock.add_response(
        url=JOBS_URL,
        json={
            "jobPostings": [
                {
                    "title": "Manufacturing Engineering Intern",
                    "externalPath": "/job/Minneapolis/Mfg-Eng-Intern_R12345",
                    "locationsText": "Minneapolis, MN",
                },
                {
                    "title": "Senior Director, Sales",
                    "externalPath": "/job/Remote/Sr-Dir_R99999",
                    "locationsText": "Remote",
                },
            ]
        },
    )
    jobs = await fetch_workday("acme", "wd1", "External", KEYWORDS, "Acme", 1)
    assert len(jobs) == 1
    job = jobs[0]
    assert job.title == "Manufacturing Engineering Intern"
    assert job.url == "https://acme.wd1.myworkdayjobs.com/External/job/Minneapolis/Mfg-Eng-Intern_R12345"
    assert job.location == "Minneapolis, MN"
    assert job.source == "workday"
    assert job.category == 1


async def test_paginates_across_pages(httpx_mock):
    httpx_mock.add_response(
        url=JOBS_URL,
        json={
            "jobPostings": [
                {"title": f"Quality Intern {i}", "externalPath": f"/job/{i}", "locationsText": "Remote"}
                for i in range(20)
            ]
        },
    )
    httpx_mock.add_response(
        url=JOBS_URL,
        json={"jobPostings": [{"title": "Quality Intern 20", "externalPath": "/job/20", "locationsText": "Remote"}]},
    )
    jobs = await fetch_workday("acme", "wd1", "External", KEYWORDS, "Acme", 1)
    assert len(jobs) == 21


async def test_returns_empty_on_404(httpx_mock):
    httpx_mock.add_response(url=JOBS_URL, status_code=404)
    jobs = await fetch_workday("acme", "wd1", "External", KEYWORDS, "Acme", 1)
    assert jobs == []


async def test_returns_empty_on_network_error(httpx_mock):
    httpx_mock.add_exception(url=JOBS_URL, exception=httpx.ConnectError("timeout"))
    jobs = await fetch_workday("acme", "wd1", "External", KEYWORDS, "Acme", 1)
    assert jobs == []


async def test_sends_applied_facets_when_provided(httpx_mock):
    httpx_mock.add_response(url=JOBS_URL, json={"jobPostings": []})
    facets = {"CF_CDSE_REC_JOB_Req_OpCo_Extended": ["Beckman Coulter - Diagnostics"]}
    await fetch_workday("acme", "wd1", "External", KEYWORDS, "Acme", 1, applied_facets=facets)
    sent_body = json.loads(httpx_mock.get_requests()[0].content)
    assert sent_body["appliedFacets"] == facets


async def test_defaults_applied_facets_to_empty_dict(httpx_mock):
    httpx_mock.add_response(url=JOBS_URL, json={"jobPostings": []})
    await fetch_workday("acme", "wd1", "External", KEYWORDS, "Acme", 1)
    sent_body = json.loads(httpx_mock.get_requests()[0].content)
    assert sent_body["appliedFacets"] == {}


async def test_filters_out_non_us_location(httpx_mock):
    httpx_mock.add_response(
        url=JOBS_URL,
        json={
            "jobPostings": [
                {"title": "Software Engineering Intern", "externalPath": "/job/1", "locationsText": "Toronto, ON"},
                {"title": "Software Engineering Intern", "externalPath": "/job/2", "locationsText": "Austin, TX"},
            ]
        },
    )
    jobs = await fetch_workday("acme", "wd1", "External", KEYWORDS, "Acme", 1)
    assert len(jobs) == 1
    assert jobs[0].location == "Austin, TX"
