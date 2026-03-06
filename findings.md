# Metadata Extraction — Findings & Plan

## Context

MAIB reports are published on gov.uk. Each report has a dedicated webpage with structured
metadata, and a PDF attachment containing the full report text.

Example: https://www.gov.uk/maib-reports/foundering-of-the-yacht-bayesian-with-loss-of-7-lives

---

## What the webpage gives us

The GOV.UK page contains reliable, structured metadata we can scrape directly:

| Field | Source | Example |
|---|---|---|
| `vessel_type` | `<dd class="gem-c-metadata__definition">` | "Recreational craft - sail" |
| `accident_date` | `<dd class="gem-c-metadata__definition">` | "19 August 2024" |
| `publication_date` | `<meta name="govuk:first-published-at">` | "2025-05-14T23:58:41+01:00" |
| `accident_location` | `<meta property="og:description">` | "Location: 0.5 nautical miles south-east of Porticello, Italy." |
| ~~`severity`~~ | ~~`<span class="attachment-inline">` link text~~ | Not reliable — link text varies per report |
| `title` | `<meta property="og:title">` | "Foundering of the yacht Bayesian with loss of 7 lives" |
| PDF URL | `<span class="attachment-inline"> a[href$=".pdf"]` | `https://assets.publishing.service.gov.uk/.../2025-Bayesian-InterimReport.pdf` |

The metadata uses the GOV.UK Design System `gem-c-metadata` pattern, which is consistent
across all MAIB report pages.

---

## What still requires the PDF

| Field | Reason |
|---|---|
| `severity` | Attachment link text varies per report — not reliable |
| `sentences` | Full text extraction — the entire NLP pipeline |
| `vessel_name` | Not a structured field on the webpage |
| `loss_of_life` | Not a structured field (sometimes in page title, not reliable) |
| `port_of_origin` / `destination` | Only in Section 1.1 table in the PDF |
| `page_count` | PDF only |

For `vessel_name`, `loss_of_life`, `port_of_origin`, `destination`: MAIBInvReport-format PDFs
have a structured Section 1.1 table we can rely on. Older formats are less consistent.

---

## Plan

### New endpoint: `POST /documents/from-url`

Accepts `{ "url": "https://www.gov.uk/maib-reports/..." }` and runs the full ingestion pipeline.

**Flow:**
1. Fetch the GOV.UK page with httpx
2. Parse metadata + PDF URL using BeautifulSoup (`gem-c-metadata__term/definition` pairs)
3. Download the PDF bytes from `assets.publishing.service.gov.uk`
4. Run existing PDF ingestion pipeline for sentences + table-extracted fields
5. Web metadata takes precedence over PDF-extracted values for shared fields

### Keep existing `POST /documents` (file upload)

Still needed for PDFs that aren't on the MAIB website (e.g. local files, other sources).
For file uploads, continue using table extraction for MAIBInvReport-format docs, and
cover page parsing as fallback.

### New dependency

`beautifulsoup4` — HTML parsing for the GOV.UK page scraper.

### New file: `services/maib_scraper.py`

Responsible for:
- Fetching a MAIB report page
- Extracting structured metadata from the HTML
- Returning PDF URL + metadata as a dataclass
- Downloading the PDF bytes

---

## Current state of PDF-based extraction (for reference)

After work done in this branch:

- MAIBInvReport-format docs (newer): table extraction works well for most fields
- Non-MAIBInvReport docs: `cover_parser.py` using spaCy exists but is not yet wired in
  (spaCy required downgrading from Python 3.14 → 3.13)
- `publication_date`: uses last month+year match on cover page text; falls back to PDF
  creation date (not yet implemented — was in progress when URL approach was discovered)
- `loss_of_life` and `accident_date` type parsing: implemented in `ingestion.py`
