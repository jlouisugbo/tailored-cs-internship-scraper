import json
import httpx
from scrapers.github_repo import fetch_github_repo

COMPANY_NAMES = frozenset(["Figma", "Mercury", "Vercel"])
KEYWORDS = frozenset(["intern", "internship"])

SAMPLE_README = """\
# Summer 2027 Internships

| Company | Role | Location | Application |
|---------|------|----------|-------------|
| Figma | Software Engineering Intern | SF / NYC | [Apply](https://jobs.lever.co/figma/123) |
| Google | Software Engineer | Mountain View | [Apply](https://careers.google.com/456) |
| Mercury | Product Design Intern | Remote | [Apply](https://mercury.com/jobs/789) |
| Vercel | Staff Engineer | Remote | [Apply](https://jobs.ashbyhq.com/vercel/999) |
"""


async def test_matches_known_companies_with_intern_keyword(httpx_mock):
    httpx_mock.add_response(
        url="https://raw.githubusercontent.com/vanshb03/Summer2027-Internships/dev/README.md",
        text=SAMPLE_README,
    )
    jobs = await fetch_github_repo(
        "vanshb03/Summer2027-Internships", "dev", "README.md", COMPANY_NAMES, KEYWORDS
    )
    assert len(jobs) == 2
    companies = {j.company for j in jobs}
    assert "Figma" in companies
    assert "Mercury" in companies


async def test_ignores_companies_not_in_watchlist(httpx_mock):
    httpx_mock.add_response(
        url="https://raw.githubusercontent.com/vanshb03/Summer2027-Internships/dev/README.md",
        text=SAMPLE_README,
    )
    jobs = await fetch_github_repo(
        "vanshb03/Summer2027-Internships", "dev", "README.md", COMPANY_NAMES, KEYWORDS
    )
    assert all(j.company != "Google" for j in jobs)


async def test_ignores_non_intern_roles_for_known_companies(httpx_mock):
    httpx_mock.add_response(
        url="https://raw.githubusercontent.com/vanshb03/Summer2027-Internships/dev/README.md",
        text=SAMPLE_README,
    )
    jobs = await fetch_github_repo(
        "vanshb03/Summer2027-Internships", "dev", "README.md", COMPANY_NAMES, KEYWORDS
    )
    assert all(j.company != "Vercel" for j in jobs)


async def test_extracts_url_from_markdown_link(httpx_mock):
    httpx_mock.add_response(
        url="https://raw.githubusercontent.com/vanshb03/Summer2027-Internships/dev/README.md",
        text="| Figma | Software Engineering Intern | Remote | [Apply](https://lever.co/figma/1) |",
    )
    jobs = await fetch_github_repo(
        "vanshb03/Summer2027-Internships", "dev", "README.md", COMPANY_NAMES, KEYWORDS
    )
    assert jobs[0].url == "https://lever.co/figma/1"


async def test_filters_out_non_us_location_markdown(httpx_mock):
    httpx_mock.add_response(
        url="https://raw.githubusercontent.com/vanshb03/Summer2027-Internships/dev/README.md",
        text=(
            "| Figma | Software Engineering Intern | London, UK | [Apply](https://example.com/1) |\n"
            "| Mercury | Software Engineering Intern | New York, NY | [Apply](https://example.com/2) |\n"
        ),
    )
    jobs = await fetch_github_repo(
        "vanshb03/Summer2027-Internships", "dev", "README.md", COMPANY_NAMES, KEYWORDS
    )
    assert len(jobs) == 1
    assert jobs[0].company == "Mercury"


async def test_filters_out_non_us_location_json(httpx_mock):
    listings = [
        {"company_name": "Figma", "title": "SWE Intern", "url": "https://example.com/1", "location": "Toronto, ON"},
        {"company_name": "Mercury", "title": "SWE Intern", "url": "https://example.com/2", "location": "Austin, TX"},
    ]
    httpx_mock.add_response(
        url="https://raw.githubusercontent.com/vanshb03/Summer2027-Internships/dev/listings.json",
        text=json.dumps(listings),
    )
    jobs = await fetch_github_repo(
        "vanshb03/Summer2027-Internships", "dev", "listings.json", COMPANY_NAMES, KEYWORDS
    )
    assert len(jobs) == 1
    assert jobs[0].company == "Mercury"


async def test_returns_empty_on_404(httpx_mock):
    httpx_mock.add_response(
        url="https://raw.githubusercontent.com/SimplifyJobs/Summer2027-Internships/dev/README.md",
        status_code=404,
    )
    jobs = await fetch_github_repo(
        "SimplifyJobs/Summer2027-Internships", "dev", "README.md", COMPANY_NAMES, KEYWORDS
    )
    assert jobs == []


async def test_returns_empty_on_network_error(httpx_mock):
    httpx_mock.add_exception(
        url="https://raw.githubusercontent.com/vanshb03/Summer2027-Internships/dev/README.md",
        exception=httpx.ConnectError("timeout"),
    )
    jobs = await fetch_github_repo(
        "vanshb03/Summer2027-Internships", "dev", "README.md", COMPANY_NAMES, KEYWORDS
    )
    assert jobs == []


async def test_parses_json_path(httpx_mock):
    listings = [
        {"company_name": "Figma", "title": "SWE Intern", "url": "https://example.com/1", "location": "Remote"},
        {"company_name": "Google", "title": "SWE Intern", "url": "https://example.com/2", "location": "MTV"},
    ]
    httpx_mock.add_response(
        url="https://raw.githubusercontent.com/vanshb03/Summer2027-Internships/dev/listings.json",
        text=json.dumps(listings),
    )
    jobs = await fetch_github_repo(
        "vanshb03/Summer2027-Internships", "dev", "listings.json", COMPANY_NAMES, KEYWORDS
    )
    assert len(jobs) == 1
    assert jobs[0].company == "Figma"


async def test_all_github_repo_jobs_have_category_zero(httpx_mock):
    httpx_mock.add_response(
        url="https://raw.githubusercontent.com/vanshb03/Summer2027-Internships/dev/README.md",
        text="| Figma | Software Engineering Intern | Remote | [Apply](https://example.com) |",
    )
    jobs = await fetch_github_repo(
        "vanshb03/Summer2027-Internships", "dev", "README.md", COMPANY_NAMES, KEYWORDS
    )
    assert all(j.category == 0 for j in jobs)
    assert all(j.source == "github_repo" for j in jobs)
