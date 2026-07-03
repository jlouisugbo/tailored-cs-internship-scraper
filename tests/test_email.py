from models import Job
from notifiers.email import render_html


def make_job(company: str = "Figma", category: int = 1, url: str = "https://example.com/1") -> Job:
    return Job(
        company=company,
        title="SWE Intern",
        url=url,
        location="Remote",
        source="greenhouse",
        category=category,
        discovered_at="2026-09-01T00:00:00+00:00",
    )


def test_render_contains_company_names():
    jobs = [make_job("Figma"), make_job("Mercury", url="https://example.com/2")]
    html = render_html(jobs)
    assert "Figma" in html
    assert "Mercury" in html


def test_render_contains_apply_links():
    jobs = [make_job(url="https://lever.co/figma/123")]
    html = render_html(jobs)
    assert "https://lever.co/figma/123" in html


def test_render_groups_by_category_ascending():
    jobs = [
        make_job("Anthropic", category=2, url="https://example.com/a"),
        make_job("Figma",     category=1, url="https://example.com/b"),
    ]
    html = render_html(jobs)
    assert html.index("Category 1") < html.index("Category 2")


def test_render_github_repo_category_labeled_correctly():
    jobs = [make_job("Figma", category=0)]
    html = render_html(jobs)
    assert "GitHub Repo" in html


def test_render_empty_list_returns_valid_html_no_table_rows():
    html = render_html([])
    assert "<html" in html
    assert "<tr>" not in html


def test_render_escapes_untrusted_ats_fields():
    job = Job(
        company='A&B "Corp"',
        title="<script>alert(1)</script> Intern",
        url="https://example.com/1",
        location="Remote",
        source="greenhouse",
        category=1,
        discovered_at="2026-09-01T00:00:00+00:00",
    )
    html = render_html([job])
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html
    assert "A&amp;B" in html


def test_render_collapses_multi_location_whitespace():
    job = Job(
        company="Salesforce",
        title="SWE Intern",
        url="https://example.com/1",
        location="5 Locations\nSan Francisco, CA\nPalo Alto, CA",
        source="workday",
        category=1,
        discovered_at="2026-09-01T00:00:00+00:00",
    )
    html = render_html([job])
    assert "5 Locations San Francisco, CA Palo Alto, CA" in html


def test_render_multiple_categories_all_appear():
    jobs = [
        make_job("A", category=1, url="https://example.com/1"),
        make_job("B", category=2, url="https://example.com/2"),
        make_job("C", category=3, url="https://example.com/3"),
        make_job("D", category=0, url="https://example.com/4"),
    ]
    html = render_html(jobs)
    assert "Category 1" in html
    assert "Category 2" in html
    assert "Category 3" in html
    assert "GitHub Repo" in html
