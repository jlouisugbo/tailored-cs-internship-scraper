import httpx
from scrapers.lever import fetch_lever

KEYWORDS = frozenset(["intern", "internship"])


async def test_returns_matching_intern_jobs(httpx_mock):
    httpx_mock.add_response(
        url="https://api.lever.co/v0/postings/mercury?mode=json",
        json=[
            {
                "text": "Software Engineering Intern",
                "hostedUrl": "https://jobs.lever.co/mercury/1",
                "categories": {"location": "Remote"},
            },
            {
                "text": "Engineering Manager",
                "hostedUrl": "https://jobs.lever.co/mercury/2",
                "categories": {"location": "Remote"},
            },
        ],
    )
    jobs = await fetch_lever("mercury", KEYWORDS, "Mercury", 1)
    assert len(jobs) == 1
    assert jobs[0].title == "Software Engineering Intern"
    assert jobs[0].source == "lever"
    assert jobs[0].url == "https://jobs.lever.co/mercury/1"


async def test_returns_empty_on_404(httpx_mock):
    httpx_mock.add_response(
        url="https://api.lever.co/v0/postings/notacompany?mode=json",
        status_code=404,
    )
    jobs = await fetch_lever("notacompany", KEYWORDS, "NotACompany", 1)
    assert jobs == []


async def test_returns_empty_on_network_error(httpx_mock):
    httpx_mock.add_exception(
        url="https://api.lever.co/v0/postings/mercury?mode=json",
        exception=httpx.ConnectError("timeout"),
    )
    jobs = await fetch_lever("mercury", KEYWORDS, "Mercury", 1)
    assert jobs == []


async def test_empty_array_response_returns_no_jobs(httpx_mock):
    httpx_mock.add_response(
        url="https://api.lever.co/v0/postings/mercury?mode=json",
        json=[],
    )
    jobs = await fetch_lever("mercury", KEYWORDS, "Mercury", 1)
    assert jobs == []


async def test_keyword_match_is_case_insensitive(httpx_mock):
    httpx_mock.add_response(
        url="https://api.lever.co/v0/postings/mercury?mode=json",
        json=[{"text": "INTERNSHIP Program", "hostedUrl": "https://example.com/1", "categories": {"location": "Remote"}}],
    )
    jobs = await fetch_lever("mercury", KEYWORDS, "Mercury", 1)
    assert len(jobs) == 1


async def test_filters_out_non_us_location(httpx_mock):
    httpx_mock.add_response(
        url="https://api.lever.co/v0/postings/mercury?mode=json",
        json=[
            {"text": "Software Engineering Intern", "hostedUrl": "https://example.com/1", "categories": {"location": "Toronto, ON"}},
            {"text": "Software Engineering Intern", "hostedUrl": "https://example.com/2", "categories": {"location": "New York, NY"}},
        ],
    )
    jobs = await fetch_lever("mercury", KEYWORDS, "Mercury", 1)
    assert len(jobs) == 1
    assert jobs[0].url == "https://example.com/2"


async def test_job_id_is_deterministic(httpx_mock):
    httpx_mock.add_response(
        url="https://api.lever.co/v0/postings/mercury?mode=json",
        json=[{"text": "SWE Intern", "hostedUrl": "https://example.com/1", "categories": {"location": "Remote"}}],
    )
    jobs = await fetch_lever("mercury", KEYWORDS, "Mercury", 1)
    import hashlib
    expected_id = hashlib.sha256("Mercury:SWE Intern:https://example.com/1".encode()).hexdigest()
    assert jobs[0].id == expected_id
    assert len(jobs[0].id) == 64
