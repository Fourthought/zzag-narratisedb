# CHIRPdb Backend — Claude Context

## Project

FastAPI backend for CHIRP's maritime incident reporting system. Built by Tandem Creative Dev for Zig Zag AI (on behalf of CHIRP).

## Stack

- **Framework:** FastAPI + Poetry
- **Database:** Supabase (PostgreSQL + pgvector)
- **Deployment:** Docker Compose on Tandem server, Cloudflare for TLS/ingress
- **PDF parsing:** pdfplumber + nltk
- **Auth:** API key per user, scoped to role (Admin/Analyst) — not yet implemented

## Architecture decisions

See `ai-docs/ZigZag_ADR_20260223.md` for the full ADR. Key points:

- No IaC — Docker Compose only
- Embeddings are **client-generated** and POSTed to the API — no generation server-side
- Vector dimension fixed at 384
- `SUPABASE_SERVICE_ROLE_KEY` required for writes (bypasses RLS)

## What's built

- `POST /documents` — PDF ingestion pipeline (7 steps)
- `GET /shield-codes` — shield code listing

## What's not built yet

- All GET endpoints (documents, sections, sentences, authors, organisations, safety issues, recommendations)
- Embeddings routes (POST + similarity search)
- Auth middleware
- DELETE, PATCH routes

## Conventions

- Keep PDF parsing logic in `services/pdf_parser.py` (pure functions, no DB)
- Keep DB orchestration in `services/ingestion.py`
- `SupabaseService` in `services/supabase/service.py` is the DB abstraction layer — use it, don't call the Supabase client directly from routes
- Don't make claims about extraction quality without testing against the sample PDFs in `samples/`

## Data flow & responsibilities

- **API extracts at ingestion:** documents, sections, sentences, safety issues, recommendations, report metadata
- **Client NLP pipeline enriches:** sentences (embeddings, SHIELD codes, relevance scores)
- Safety issues and recommendations are NOT processed by the NLP pipeline — they're stored as extracted and linked to constituent sentences via join tables

## API spec

See `docs/API.md` for the full planned route list.

## Schema

See `docs/schema.sql` for the current database schema (reference only — not runnable).
