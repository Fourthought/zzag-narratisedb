# Ingestion

## Code responsibilities

The ingestion code is split into four layers, each with a single concern:

Routes (`routes/documents.py`) — HTTP only. Parse the incoming request, call the appropriate controller, and map any errors to HTTP responses. No business logic.

Controllers (`controllers/`) — Orchestration. Each controller owns one pipeline end-to-end: calling the right services in the right order, merging data from multiple sources, and returning the final result. They know what needs to happen but not how each step works internally.

Services (`services/`) — Single-concern operations:
- `scraper.py` — fetches a GOV.UK MAIB report page and returns structured metadata plus the raw PDF bytes. No PDF parsing, no database.
- `pdf_parsing.py` — opens a PDF and extracts text, file metadata, and structured report metadata from tables. No database.
- `ingest_to_db.py` — all database writes: duplicate checking, author resolution, document creation, accident metadata, and sentence storage. No PDF or HTTP knowledge.

Utils (`utils/pdf/`) — Pure functions for extracting specific fields from PDF text: title, publication date, accident date, loss of life, and sentence splitting. No I/O, no side effects.

---

## Call order

URL pipeline:

```
POST /documents/url
  → controllers/url.py
      → services/scraper.py        # fetch page + download PDF
      → services/pdf_parsing.py    # extract text + metadata from PDF
      → services/ingest_to_db.py   # write document, metadata, sentences to DB
```

PDF pipeline:

```
POST /documents/pdf
  → controllers/pdf.py
      → services/pdf_parsing.py    # extract text + metadata from PDF
      → utils/pdf/                 # extract title, publication date
      → services/ingest_to_db.py   # write document, metadata, sentences to DB
```

---

## Data sources

### `POST /documents/url` (`controllers/url.py`)

#### From GOV.UK webpage

| Field | Source |
|---|---|
| `documents.title` | `og:title` meta tag |
| `documents.publication_date` | `govuk:first-published-at` meta tag |
| `documents.url` | URL passed in |
| `metadata.vessel_type` | `gem-c-metadata` `"Vessel type"` term |
| `metadata.accident_date` | `gem-c-metadata` `"Date of occurrence"` term |
| `metadata.accident_location` | `og:description` `"Location: ..."` |

#### From PDF

| Field | Source |
|---|---|
| `documents.filename` | PDF filename from download URL |
| `documents.author_id` | PDF `Author` metadata (`"Unknown"` if absent) |
| `documents.hash` | SHA-256 of full text |
| `metadata.vessel_name` | Any table (key matches `vessel.*name`) |
| `metadata.severity` | Any table (key matches `type.*casualty` etc.) |
| `metadata.loss_of_life` | Any table (key matches `injur\|fatal\|casualt`) |
| `metadata.port_of_origin` | Any table (key matches `port.*departure` etc.) |
| `metadata.destination` | Any table (key matches `port.*arrival`) |
| `metadata.accident_type` | Any table (key matches `type.*voyage` etc.) |
| `metadata.page_count` | PDF page count |
| `metadata.pdf_subject` | PDF `Subject` metadata |
| `metadata.pdf_author` | PDF `Author` metadata |
| `sentences.*` | Full text extraction (pdfplumber) |

---

### `POST /documents/pdf` (`controllers/pdf.py`)

All fields from PDF only. `documents.url` is not stored.

| Field | Source |
|---|---|
| `documents.title` | PDF `Title` metadata → text extraction fallback |
| `documents.publication_date` | Cover page month/year text |
| `documents.author_id` | PDF `Author` metadata (`"Unknown"` if absent) |
| `documents.hash` | SHA-256 of full text |
| `metadata.vessel_type` | Any table (key matches `^type$`) |
| `metadata.accident_date` | Any table (key matches `date.*time`) |
| `metadata.accident_location` | Any table (key matches `location.*incident` etc.) |
| `metadata.vessel_name` | Any table (key matches `vessel.*name`) |
| `metadata.severity` | Any table (key matches `type.*casualty` etc.) |
| `metadata.loss_of_life` | Any table (key matches `injur\|fatal\|casualt`) |
| `metadata.port_of_origin` | Any table (key matches `port.*departure` etc.) |
| `metadata.destination` | Any table (key matches `port.*arrival`) |
| `metadata.accident_type` | Any table (key matches `type.*voyage` etc.) |
| `metadata.page_count` | PDF page count |
| `metadata.pdf_subject` | PDF `Subject` metadata |
| `metadata.pdf_author` | PDF `Author` metadata |
| `sentences.*` | Full text extraction (pdfplumber) |
