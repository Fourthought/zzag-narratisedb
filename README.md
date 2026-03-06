# CHIRPdb Backend

A production-ready backend API for CHIRP's maritime incident reporting system. Built by Tandem Creative Dev for Zig Zag AI on behalf of CHIRP.

---

## Progress

**What works:**

- `POST /documents/from-url` — scrapes a GOV.UK MAIB report page, downloads the PDF, and runs the full ingestion pipeline. Web-scraped metadata (title, publication date, vessel type, accident date, location) takes precedence over PDF-extracted values
- `POST /documents` — file upload path; all data sourced from the PDF
- Both paths: duplicate detection (SHA-256), sentence splitting and classification by text type, report metadata extraction from structured tables in the PDF
- See [INGESTION.md](INGESTION.md) for a full breakdown of what comes from where

**What is not yet built:**

- All GET endpoints (documents, sentences, authors, organisations, safety issues, recommendations)
- Embeddings routes (POST + similarity search)
- Auth middleware
- DELETE and PATCH routes

---

## The Problem

CHIRP maintains a large corpus of Marine Accident Investigation Branch (MAIB) incident reports — detailed PDF documents covering maritime accidents, safety findings, and corrective recommendations. This data is currently unstructured and difficult to query, analyse, or surface systematically.

The goal of CHIRPdb is to ingest those reports into a structured, queryable database — breaking each document down into its constituent parts (sections, sentences, safety issues, recommendations) and making them available via a clean REST API for downstream analysis and search.

---

## The Data

Source documents are MAIB investigation reports in PDF format. Each report contains:

- Incident metadata (vessel name, accident date, location, severity, etc.)
- Structured narrative sections
- Safety issues identified during the investigation
- Recommendations directed at organisations

Reports vary in length and internal structure. Extraction quality for certain fields (particularly incident metadata) depends on consistency of PDF formatting across reports and is subject to ongoing validation.

### What we extract and from where

See [INGESTION.md](INGESTION.md) for the full breakdown. In summary:

- For `POST /documents/from-url`: title, publication date, vessel type, accident date, and location come from the GOV.UK webpage. Vessel name, severity, loss of life, port of origin, destination, accident type, and all sentences come from the PDF.
- For `POST /documents`: everything comes from the PDF.

---

## System Architecture

The system is split into two distinct layers:

### 1. CHIRPdb API (this repository)

A FastAPI application responsible for:

- Ingesting MAIB reports via GOV.UK URL scraping or direct PDF upload
- Parsing PDFs into structured data: documents, sentences, and report metadata
- Storing all structured data in a PostgreSQL database (Supabase)
- Storing and querying vector embeddings via pgvector
- Serving structured data back to the client pipeline and any future consumers

The API does **not** perform semantic analysis or generate embeddings. It is a structured data store and retrieval layer.

### 2. Client NLP Pipeline (external)

A locally-operated pipeline maintained by the client, responsible for:

- Reading sentences from the API
- Applying advanced semantic NLP analysis to sentences — assigning SHIELD codes and other classifications that require semantic understanding
- Generating vector embeddings for sentences using a local model
- Writing results (embeddings, shield codes, relevance scores) back to the API

Safety issues and recommendations are extracted at ingestion time and are not processed by the NLP pipeline.

**Neither layer is useful without the other.** The API provides structure; the NLP pipeline provides intelligence.

### Ingestion pipelines

There are two ingestion routes, each with a distinct pipeline:

**`POST /documents/url`** — the primary path. Accepts a GOV.UK MAIB report URL. The scraper fetches the page and extracts structured metadata (title, publication date, vessel type, accident date, location) directly from the HTML, then downloads the PDF. The PDF parser extracts the remaining fields (vessel name, severity, loss of life, port/destination, sentences) that aren't available on the page. Both sets of data are written to the database.

**`POST /documents/pdf`** — for direct PDF uploads. Skips the scraping step entirely; all metadata and content comes from the PDF alone.

In both cases, a SHA-256 hash of the document text is used to detect and reject duplicates. See [INGESTION.md](INGESTION.md) for the full field-by-field breakdown.

### Code responsibilities

The ingestion code is split into four layers, each with a single concern:

**Routes** (`routes/documents.py`) — HTTP only. Parse the incoming request, call the appropriate controller, and map any errors to HTTP responses. No business logic.

**Controllers** (`controllers/`) — Orchestration. Each controller owns one pipeline end-to-end: calling the right services in the right order, merging data from multiple sources, and returning the final result. They know what needs to happen but not how each step works internally.

**Services** (`services/`) — Single-concern operations:
- `scraper.py` — fetches a GOV.UK MAIB report page and returns structured metadata plus the raw PDF bytes. No PDF parsing, no database.
- `pdf_parsing.py` — opens a PDF and extracts text, file metadata, and structured report metadata from tables. No database.
- `ingest_to_db.py` — all database writes: duplicate checking, author resolution, document creation, accident metadata, and sentence storage. No PDF or HTTP knowledge.

**Utils** (`utils/pdf/`) — Pure functions for extracting specific fields from PDF text: title, publication date, accident date, loss of life, and sentence splitting. No I/O, no side effects.

#### URL pipeline call order

```
POST /documents/url
  → controllers/url.py
      → services/scraper.py        # fetch page + download PDF
      → services/pdf_parsing.py    # extract text + metadata from PDF
      → services/ingest_to_db.py   # write document, metadata, sentences to DB
```

#### PDF pipeline call order

```
POST /documents/pdf
  → controllers/pdf.py
      → services/pdf_parsing.py    # extract text + metadata from PDF
      → utils/pdf/                 # extract title, publication date
      → services/ingest_to_db.py   # write document, metadata, sentences to DB
```

### Interaction flow

1. Reports are ingested via `POST /documents/url` or `POST /documents/pdf`
2. The client pipeline fetches sentences from the API
3. The client pipeline runs semantic NLP analysis — assigning SHIELD codes, generating embeddings, and scoring relevance
4. The client pipeline writes results back to the API
5. The API serves fully enriched data, enabling similarity search and structured querying

---

## SHIELD Codes

SHIELD codes are a domain-specific classification taxonomy used by CHIRP to categorise safety-relevant content within incident reports. They are assigned at the sentence level by the client's NLP pipeline, not by this API. The API stores them and makes them queryable.

---

## Infrastructure

- **Database:** Supabase (managed PostgreSQL + pgvector), London region
- **API hosting:** Docker Compose on Tandem server (Germany)
- **TLS / ingress:** Cloudflare reverse proxy
- **Embeddings:** Client-generated, dimension fixed at 384

See `ai-docs/ZigZag_ADR_20260223.md` for the full architectural decision record.

---

## Getting Started

### Prerequisites

- Python 3.11+
- [Poetry](https://python-poetry.org/)
- A Supabase project with `SUPABASE_SERVICE_ROLE_KEY` access

### Environment variables

Copy `.env.example` to `.env` and populate:

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

`SUPABASE_SERVICE_ROLE_KEY` is required for write operations — the anon key will not work due to RLS policies.

### Install dependencies

```bash
poetry install
```

### Run locally

```bash
poetry run uvicorn main:app --reload
```

### Ingest from a GOV.UK URL

```bash
curl -X POST http://localhost:8000/documents/from-url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.gov.uk/maib-reports/..."}'
```

### Ingest from a PDF file

```bash
curl -X POST http://localhost:8000/documents \
  -F "file=@path/to/report.pdf"
```

### Bulk ingest from the MAIB links list

```bash
./scripts/ingest-from-links.sh        # first 10
./scripts/ingest-from-links.sh 50     # custom limit
```

---

## API Reference

See `docs/API.md` for the full route list.

## Database Schema

See `docs/schema.sql` for the current schema (reference only).
