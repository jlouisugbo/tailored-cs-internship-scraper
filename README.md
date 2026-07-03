# tailored-cs-internship-scraper

A self-hosted internship/co-op alert bot. It polls company career boards
(Greenhouse, Lever, Ashby, Workday) plus community-maintained GitHub
internship-list repos, filters postings by keyword and US location, dedupes
against everything it's already seen, and pushes new matches to Discord in
real time with a nightly email digest as backup. Runs entirely on GitHub
Actions' free tier — no server, no database to host.

It's built to be forked: swap in your own target companies, categories, and
notification channels in one YAML file, no code changes required for the
common case.

## Features

- **Four scraper backends** — Greenhouse, Lever, Ashby, and Workday (with
  per-tenant facet filtering for shared/multi-brand tenants), plus a generic
  scraper for GitHub repos that maintain a Markdown or JSON internship list
  (e.g. the SimplifyJobs/vanshb03-style "Summer 2027 Internships" repos).
- **Category tiers** — group companies into your own priority tiers (1, 2,
  3, ...); each tier gets a distinct Discord embed color, and you choose
  which tiers (if any) also `@mention` you directly.
- **Dedup that survives restarts** — a SQLite file tracked in the repo
  itself acts as seen-job state, committed back by the GitHub Action after
  each run, so there's no external database to provision.
- **US-location filtering** — a location classifier trained on state
  abbreviations, country names, and common non-US cities filters out non-US
  postings by default (see [Customizing](#customizing) to disable).
- **Discord + email digest** — instant per-posting alerts via webhook, plus
  an optional nightly HTML digest email summarizing everything found that
  day.
- **Zero-infra deploy** — two GitHub Actions workflows (hourly scrape,
  nightly digest) are all you need; no hosting, no cron server.

## Quick start

**Prerequisites:** Python 3.12+, a Discord server you can add a webhook to
(optional), a Gmail account with an [app password](https://myaccount.google.com/apppasswords)
(optional, only needed for the email digest).

```bash
git clone https://github.com/<you>/tailored-cs-internship-scraper.git
cd tailored-cs-internship-scraper
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# fill in .env with your webhook URL / Gmail app password (see below)

# edit config/companies.yaml to your target companies — see Customizing
python runner.py     # one-off scrape + Discord alerts
python digest.py     # send the digest email for anything queued
```

Everything the scraper needs to know — which companies, which categories,
which keywords, which notification channels — lives in
[`config/companies.yaml`](config/companies.yaml). Secrets (webhook URLs,
passwords, tokens) never go in that file; they're read from environment
variables (`.env` locally, GitHub Actions secrets in CI).

## Configuring

### Environment variables

Copy `.env.example` to `.env` and fill in whichever notifiers you're using:

| Variable | Required for | How to get it |
|---|---|---|
| `DISCORD_WEBHOOK_URL` | Discord alerts | Server Settings → Integrations → Webhooks → New Webhook → Copy URL |
| `GMAIL_ADDRESS` | Email digest | The Gmail address you're sending from |
| `GMAIL_APP_PASSWORD` | Email digest | [Google App Passwords](https://myaccount.google.com/apppasswords) (requires 2FA enabled) |
| `GITHUB_TOKEN` | GitHub repo scraper (CI only) | Auto-provided by GitHub Actions; only needed to avoid unauthenticated rate limits |

If you only want Discord alerts, you can skip the two Gmail variables — the
digest step just logs "queue empty" and exits if `email_to` has no jobs
queued; it doesn't hard-fail on missing Gmail creds unless you actually run
`digest.py` with jobs pending.

### `config/companies.yaml`

```yaml
keywords:                    # a posting title must match at least one (word-boundary, case-insensitive)
  - intern
  - internship

notification:
  discord_webhook_env: DISCORD_WEBHOOK_URL   # name of the env var holding the webhook URL
  email_to: you@example.com                  # digest recipient
  email_from_env: GMAIL_ADDRESS
  email_password_env: GMAIL_APP_PASSWORD
  digest_hour_utc: 1                         # for your own reference; the workflow's cron is what actually controls timing
  discord_ping_user_id: ""                   # your Discord user ID (Developer Mode → right-click your name → Copy User ID). Blank = no pings.
  discord_ping_categories: [1]               # which categories additionally @mention you

github_repos:                # community-maintained internship-list repos to also scrape
  - repo: vanshb03/Summer2027-Internships
    branch: dev
    path: README.md
    priority: primary

companies:
  - { name: Figma, category: 1, slug: figma }
  - { name: Stripe, category: 3, slug: stripe }
```

**Adding a company:** the `slug` is tried against Greenhouse, Lever, and
Ashby every run automatically (a 404 from an ATS that doesn't apply to that
company just yields no results — it's not an error). Find the slug from the
company's careers page URL, e.g. `boards.greenhouse.io/<slug>`,
`jobs.lever.co/<slug>`, or `jobs.ashbyhq.com/<slug>`.

If a company's slug differs per platform, override just that one:

```yaml
- { name: Block, category: 3, slug: block, slug_greenhouse: block-inc }
```

**Adding a Workday company:** Workday doesn't have a predictable slug, so
you supply the tenant/host/site tuple found by inspecting the company's
careers page network requests (look for a request to
`<tenant>.<host>.myworkdayjobs.com/wday/cxs/<tenant>/<site>/jobs`):

```yaml
- { name: Zoom, category: 3, slug: zoom,
    slug_workday: { tenant: zoom, host: wd5, site: Zoom } }
```

For shared tenants where one Workday account posts for multiple
subsidiaries/brands, add `applied_facets` to filter down to just the brand
you care about (facet keys/values are Workday's own — find them by
inspecting the filter checkboxes' network requests on the careers site).

**Categories** are just integers you define — there's nothing special about
`1`/`2`/`3` beyond the embed colors in `notifiers/discord.py`'s `COLORS`
dict and whichever categories you list under `discord_ping_categories`. Add
a 4th tier by adding an entry to `COLORS` and using that number in your
company list.

**Turning off the US-location filter:** postings are dropped if
`location_filter.is_us_location()` returns `False`. If you want global
postings, the simplest change is to make every scraper call skip that
check — search for `is_us_location` across `scrapers/` and remove the
`continue`s guarding on it.

### Discord ping setup

1. Create/copy a webhook URL (see table above) and put it in
   `DISCORD_WEBHOOK_URL`.
2. To also get `@mentioned` on high-priority postings: enable Developer
   Mode in Discord (User Settings → Advanced), right-click your name in any
   server, "Copy User ID", and set `discord_ping_user_id` in
   `companies.yaml`.
3. List which categories should trigger the ping in
   `discord_ping_categories`. Leave `discord_ping_user_id` blank to disable
   pings entirely while still getting the regular embeds.

## Deploying (GitHub Actions)

The repo ships with two workflows:

- **`.github/workflows/scrape.yml`** — runs hourly, scrapes everything, and
  sends Discord alerts for anything new. Commits the updated dedup database
  back to the repo (`data/seen_jobs.db`) so state persists between runs
  without an external database.
- **`.github/workflows/digest.yml`** — runs nightly, sends the queued
  digest email, and clears the queue.

To deploy: fork this repo, then add these under **Settings → Secrets and
variables → Actions**:

- `DISCORD_WEBHOOK_URL`
- `GMAIL_ADDRESS`
- `GMAIL_APP_PASSWORD`

(`GITHUB_TOKEN` is provided automatically — no setup needed.) Both
workflows need `permissions: contents: write` (already set) so they can
commit the dedup state back.

## Architecture

```
runner.py            hourly entrypoint: fan out to all scrapers concurrently,
                      dedup against SQLite, alert on anything new
digest.py             nightly entrypoint: email everything queued since the
                      last digest, then clear the queue
config_loader.py      parses config/companies.yaml into typed dataclasses
db.py                 SQLite schema + dedup/digest-queue operations
location_filter.py    US-vs-non-US location classifier
models.py             Job dataclass (content-hash id for dedup)
scrapers/              one fetch_<ats>() per source, all returning list[Job]
notifiers/             discord.py (webhook alerts), email.py (HTML digest)
```

Every scraper follows the same shape —
`fetch_<source>(..., keywords, company_name, category) -> list[Job]` — so
adding a new ATS backend means writing one new file in `scrapers/` with
that signature, wiring it into the loop in `runner.py`, and adding whatever
config fields it needs to `config_loader.py` and `companies.yaml`.

## Testing

```bash
pip install -r requirements.txt
pytest
```

Tests use `pytest-httpx` to mock all outbound HTTP, so the suite runs fully
offline. No live API keys or network access needed.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)
