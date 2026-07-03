# Contributing

This started as a personal tool, so contributions are welcome but the bar
for merging is "keeps working for other people's configs," not "matches my
exact company list."

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest
```

Tests mock all HTTP via `pytest-httpx`, so no network access or API keys
are needed to run the suite.

## Good contributions

- A new ATS scraper (`scrapers/<ats>.py`) following the existing
  `fetch_<ats>(..., keywords, company_name, category) -> list[Job]` shape.
- Bug fixes in dedup, location filtering, or keyword matching, with a test
  reproducing the bug first.
- Documentation fixes for the setup/config walkthrough in the README.

## What to avoid

- PRs that hardcode your own company list, Discord ID, or email as the
  new default — `config/companies.yaml` should stay a reasonable example,
  not any one contributor's personal setup.
- New required config fields without a backwards-compatible default —
  existing forks' `companies.yaml` files shouldn't break on pull.

## Pull requests

1. Add a test for the behavior you're changing (see `tests/`).
2. `pytest` passes locally.
3. Keep the PR scoped to one change — easier to review, easier to revert
   if something's wrong.
