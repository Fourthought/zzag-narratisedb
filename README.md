# CHIRPdb Backend

A production-ready backend API for CHIRP's maritime incident reporting system. Built by Tandem Creative Dev for Zig Zag AI on behalf of CHIRP.

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

**From the PDF file metadata** (embedded in the file itself):

| Field | Notes |
|-------|-------|
| Title | Used as the document title |
| Page count | Stored against the report metadata record |
| Subject | Stored against the report metadata record |

**From the PDF contents** (the text of the document):

| Field | Notes |
|-------|-------|
| Publication date | Extracted from the cover page |
| Vessel name | Extracted from the document's incident summary |
| Accident date | Extracted from the document's incident summary |
| Accident location | Extracted from the document's incident summary |
| Severity | Extracted from the document's incident summary |
| Vessel type | Extracted from the document's incident summary |
| Loss of life | Extracted from the document's incident summary |
| Port of origin | Extracted from the document's incident summary |
| Destination | Extracted from the document's incident summary |
| Accident type | Extracted from the document's incident summary |
| Sections | The document split into named narrative sections |
| Sentences | Each section split into individual sentences, typed as paragraph, list item, or heading |
| Safety issues | Extracted from the safety/conclusions section |
| Recommendations | Extracted from the recommendations section, with associated organisations |

---

## System Architecture

The system is split into two distinct layers:

### 1. CHIRPdb API (this repository)

A FastAPI application responsible for:

- Accepting PDF uploads and running the ingestion pipeline
- Parsing PDFs into structured data: documents, sections, sentences, safety issues, recommendations
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

### Interaction flow

1. A PDF is uploaded to `POST /documents` — the API computes a SHA256 hash of the document content and rejects it with a `409 Conflict` if it has been ingested before. Otherwise it ingests the PDF, extracts structure, and stores documents, sections, sentences, safety issues, and recommendations
2. The client pipeline fetches sentences from the API
3. The client pipeline runs semantic NLP analysis on the sentences — assigning SHIELD codes, generating embeddings, and applying any other classifications that require semantic understanding
4. The client pipeline writes results back to the API (embeddings, shield codes, relevance scores for sentences)
5. The API now serves fully enriched data — sentences with SHIELD codes and embeddings — enabling similarity search and structured querying. Safety issues and recommendations are stored as extracted at ingestion time and linked to their constituent sentences

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

### Ingest a PDF

```bash
curl -X POST http://localhost:8000/documents \
  -F "file=@path/to/report.pdf"
```

---

## API Reference

See `docs/API.md` for the full route list.

## Database Schema

See `docs/schema.sql` for the current schema (reference only).
