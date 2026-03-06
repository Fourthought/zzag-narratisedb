# CHIRPdb Backend

A production-ready backend API for CHIRP's maritime incident reporting system. Built by Tandem Creative Dev for Zig Zag AI on behalf of CHIRP.

---

## Progress

What works:

- `POST /documents/url` — scrapes a GOV.UK MAIB report page, downloads the PDF, and runs the full ingestion pipeline
- `POST /documents/pdf` — file upload path; all data sourced from the PDF
- Both paths: duplicate detection (SHA-256), sentence splitting and classification by text type, report metadata extraction from structured tables in the PDF
- See [INGESTION.md](INGESTION.md) for a full breakdown of what comes from where

What is not yet built:

- GET endpoints for sentences, authors, organisations, safety issues, recommendations
- Embeddings routes (POST + similarity search)
- Auth middleware
- DELETE and PATCH routes

### Ingestion

See [INGESTION.md](INGESTION.md) for a full breakdown of what is extracted and from where.

### Development scripts

All scripts are in `scripts/development/`. They default to `http://localhost:8000` but respect `API_URL`.

```bash
# Ingest reports from docs/maib_links.json (default: first 10)
./scripts/development/ingest-from-links.sh
./scripts/development/ingest-from-links.sh 50

# Fetch full text for a single document, saved to output/{id}.txt
./scripts/development/get-full-text.sh <document-id>

# Fetch full text for all documents, saved to output/{id}.txt
./scripts/development/extract-all-documents.sh

# Truncate all non-reference tables (local Supabase only)
./scripts/development/truncate-db.sh
```

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

The API does not perform semantic analysis or generate embeddings. It is a structured data store and retrieval layer.

### 2. Client NLP Pipeline (external)

A locally-operated pipeline maintained by the client, responsible for:

- Reading sentences from the API
- Applying advanced semantic NLP analysis to sentences — assigning SHIELD codes and other classifications that require semantic understanding
- Generating vector embeddings for sentences using a local model
- Writing results (embeddings, shield codes, relevance scores) back to the API

Safety issues and recommendations are extracted at ingestion time and are not processed by the NLP pipeline.

Neither layer is useful without the other. The API provides structure; the NLP pipeline provides intelligence.

### Ingestion pipelines

There are two ingestion routes, each with a distinct pipeline:

`POST /documents/url` — the primary path. Accepts a GOV.UK MAIB report URL. The scraper fetches the page and extracts structured metadata (title, publication date, vessel type, accident date, location) directly from the HTML, then downloads the PDF. The PDF parser extracts the remaining fields (vessel name, severity, loss of life, port/destination, sentences) that aren't available on the page. Both sets of data are written to the database.

`POST /documents/pdf` — for direct PDF uploads. Skips the scraping step entirely; all metadata and content comes from the PDF alone.

In both cases, a SHA-256 hash of the document text is used to detect and reject duplicates. See [INGESTION.md](INGESTION.md) for a detailed breakdown of what comes from where, including code responsibilities and call order.

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

- Database: Supabase (managed PostgreSQL + pgvector), London region
- API hosting: Docker Compose on Tandem server (Germany)
- TLS / ingress: Cloudflare reverse proxy
- Embeddings: Client-generated, dimension fixed at 384

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
curl -X POST http://localhost:8000/documents/url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.gov.uk/maib-reports/..."}'
```

### Ingest from a PDF file

```bash
curl -X POST http://localhost:8000/documents/pdf \
  -F "file=@path/to/report.pdf"
```

---

## API Reference

See `docs/API.md` for the full route list.

## Database Schema

See `docs/schema.sql` for the current schema (reference only).
