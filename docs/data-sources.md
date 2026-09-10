# Data sources — decision

Three candidate sources for French-language job postings were evaluated against three criteria: terms of use (ToS/CGU), `robots.txt` compliance, and availability of an official API. The project's stated commitment (see README) is to collect data "with rate limiting and `robots.txt` compliance" — any source that fails either the legal or the technical check is disqualified regardless of volume.

## Sources evaluated

| Source | Terms of use | `robots.txt` | Official API | Verdict |
|---|---|---|---|---|
| **France Travail** (formerly Pôle Emploi) | Public employment service; API designed for third-party reuse | Does not block the main offer/search pages (only blocks admin and candidate-account paths: `/espacecandidat/`, `/modules/`, etc.) | **Yes** — `francetravail.io`, "Offres d'emploi" API, OAuth2 client-credentials flow, free developer tier, **10 req/s** quota | **Selected** |
| **Indeed** | No explicit anti-scraping clause found in the reviewed ToS section | Explicitly disallows `/jobs`, `/viewjob`, `/q-`, `/l-` — precisely the listing and search-result paths needed | No active public third-party API | **Rejected** |
| **Welcome to the Jungle** | Section 10 of the Terms explicitly prohibits using "spiders, robots... to scrape or otherwise copy the Website" | Disallows query-string search pages (`/*?`) | None | **Rejected** |

## Decision

**France Travail's public API is the sole data source for this project.**

## Justification

- It is the only candidate offering a sanctioned, documented programmatic access path — no scraping (and therefore no `robots.txt` ambiguity or ToS risk) is required at all.
- Indeed's `robots.txt` disallows exactly the pages this project would need (`/jobs`, `/viewjob`, search results). Respecting `robots.txt` — a stated project commitment — makes Indeed unusable as a source, independent of any ToS question.
- Welcome to the Jungle's Terms of Service contain an explicit, unambiguous scraping prohibition. There is no technical or legal path to using it that fits this project's constraints.
- Restricting to one clean, low-risk, high-volume source is preferable to combining it with a source that requires justifying a legal or technical gray area.

## Volume estimate

France Travail's national job database (all sectors) is large enough that a filtered subset (e.g., IT/tech categories) should comfortably exceed the ~500 postings targeted by this project (see README: "~500 postings, of which ~150 are hand-annotated").

**Not independently verified yet** — the exact current count must be confirmed by querying the API directly (the `/offres/search` endpoint returns a total result count per query) once developer credentials are set up.

## API access

- **Product:** "Offres d'emploi" (job offers) API on `francetravail.io`
- **Auth:** OAuth2 client-credentials flow; `client_id`/`client_secret` generated via a registered application, stored in `.env` (git-ignored, never committed)
- **Rate limit:** 10 requests/second

## Open items before scraping starts

- [x] Create a `francetravail.io` developer account and register an application to obtain `client_id`/`client_secret`.
- [x] Confirm current API scopes, quotas, and rate limits directly on the developer portal — 10 req/s confirmed.
- [ ] Confirm the exact volume available for the target job categories via a live query, before finalizing the ~500-posting collection plan.
