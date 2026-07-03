import httpx
from scrapers.greenhouse import fetch_greenhouse

KEYWORDS = frozenset(["intern", "internship"])


async def test_returns_matching_intern_jobs(httpx_mock):
    httpx_mock.add_response(
        url="https://boards.greenhouse.io/v1/boards/figma/jobs",
        json={
            "jobs": [
                {
                    "title": "Software Engineering Intern",
                    "absolute_url": "https://boards.greenhouse.io/figma/jobs/1",
                    "location": {"name": "Remote"},
                },
                {
                    "title": "Senior Software Engineer",
                    "absolute_url": "https://boards.greenhouse.io/figma/jobs/2",
                    "location": {"name": "SF"},
                },
            ]
        },
    )
    jobs = await fetch_greenhouse("figma", KEYWORDS, "Figma", 1)
    assert len(jobs) == 1
    assert jobs[0].title == "Software Engineering Intern"
    assert jobs[0].source == "greenhouse"
    assert jobs[0].company == "Figma"
    assert jobs[0].category == 1
    assert jobs[0].location == "Remote"


async def test_returns_empty_on_404(httpx_mock):
    httpx_mock.add_response(
        url="https://boards.greenhouse.io/v1/boards/notacompany/jobs",
        status_code=404,
    )
    jobs = await fetch_greenhouse("notacompany", KEYWORDS, "NotACompany", 1)
    assert jobs == []


async def test_returns_empty_on_network_error(httpx_mock):
    httpx_mock.add_exception(
        url="https://boards.greenhouse.io/v1/boards/figma/jobs",
        exception=httpx.ConnectError("timeout"),
    )
    jobs = await fetch_greenhouse("figma", KEYWORDS, "Figma", 1)
    assert jobs == []


async def test_keyword_match_is_case_insensitive(httpx_mock):
    httpx_mock.add_response(
        url="https://boards.greenhouse.io/v1/boards/figma/jobs",
        json={"jobs": [
            {"title": "INTERNSHIP Engineer", "absolute_url": "https://example.com/1", "location": {"name": ""}},
        ]},
    )
    jobs = await fetch_greenhouse("figma", KEYWORDS, "Figma", 1)
    assert len(jobs) == 1


async def test_filters_out_non_us_location(httpx_mock):
    httpx_mock.add_response(
        url="https://boards.greenhouse.io/v1/boards/figma/jobs",
        json={"jobs": [
            {"title": "Software Engineering Intern", "absolute_url": "https://example.com/1", "location": {"name": "London, UK"}},
            {"title": "Software Engineering Intern", "absolute_url": "https://example.com/2", "location": {"name": "New York, NY"}},
        ]},
    )
    jobs = await fetch_greenhouse("figma", KEYWORDS, "Figma", 1)
    assert len(jobs) == 1
    assert jobs[0].location == "New York, NY"


async def test_job_id_is_deterministic(httpx_mock):
    httpx_mock.add_response(
        url="https://boards.greenhouse.io/v1/boards/figma/jobs",
        json={"jobs": [
            {"title": "SWE Intern", "absolute_url": "https://example.com/1", "location": {"name": "Remote"}},
        ]},
    )
    jobs = await fetch_greenhouse("figma", KEYWORDS, "Figma", 1)
    import hashlib
    expected_id = hashlib.sha256("Figma:SWE Intern:https://example.com/1".encode()).hexdigest()
    assert jobs[0].id == expected_id
    assert len(jobs[0].id) == 64
