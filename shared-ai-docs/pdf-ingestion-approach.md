# PDF Ingestion Approach

## Context

CHIRPdb is a backend service (FastAPI + Supabase/PostgreSQL) for CHIRP's maritime incident reporting system. It provides structured storage and a RESTful API for MAIB (Marine Accident Investigation Branch) accident investigation reports.

The system does **not** perform NLP analysis. It is a storage and API layer that:
1. Ingests PDF reports, parses them into structured data, and stores them
2. Serves that data to an external analysis tool (Zig Zag's NLP pipeline)
3. Receives analysis results (shield codes, embeddings, relevance scores) back via POST
4. Serves the enriched data to a frontend for browsing, filtering, and similarity search

## Data Flow

### 1. Analyst uploads a PDF
A user uploads a single MAIB PDF report via the API. The ingestion pipeline parses it and writes structured data to Supabase:
- **Document record** — title, filename, content hash (for deduplication), publication date, author
- **Report metadata** — vessel name, vessel type, location, accident date, severity, loss of life, etc. (from the structured tables on page 2 of each MAIB report)
- **Sections** — the document split into its top-level sections (Synopsis, Factual Information, Analysis, Conclusions, Action Taken, Recommendations), each with a `position` for ordering and a `document_id`
- **Sentences** — each section's text split into sentences, each with a `position` within its section, a `text_type` (paragraph, list item, heading, table row), and references to both `section_id` and `document_id`
- **Safety issues** — extracted from Section 3 (Conclusions) using text parsing, not NLP
- **Recommendations** — extracted from Section 5 using text parsing, with the target organisation

### 2. Analyst selects a document for analysis
An analyst uses Zig Zag's analysis tool to browse documents in the database and manually selects one to analyse. This is a deliberate, human-driven action — not an automated batch pipeline.

### 3. Analyst runs analysis
The analysis tool pulls the document's sentences from the API and runs its NLP pipeline:
- Shield code classification per sentence
- Relevance scoring
- Embedding generation (384-dim vectors, generated client-side per ADR-05)

### 4. Analysis results posted back
The tool POSTs results to the API:
- Shield code assignments stored in `chirp_analysis` and `chirp_analysis_shield_codes`
- Embeddings stored via pgvector on sentences
- Relevance scores updated on sentence records

### 5. Frontend users browse and search
A frontend (built separately, not by us) queries the API to:
- Browse incidents with filters (vessel type, location, date range)
- View reports section by section (reconstructed from sentences ordered by position)
- See which shield codes apply to which sentences
- Run vector similarity searches across analysed documents

## PDF Structure (MAIB Reports)

MAIB reports follow a consistent high-level structure, though the depth and subsections vary between reports:

```
Cover page (title, vessel name, location, date, severity, report number)
Legal disclaimer / copyright page
Contents
Glossary of abbreviations and acronyms
SYNOPSIS
SECTION 1 – FACTUAL INFORMATION
  1.1  Particulars of {vessel} and accident  ← structured tables (vessel, voyage, casualty)
  1.2  Background
  1.3  Narrative (with subsections)
  1.4+ Variable subsections (environmental conditions, vessel details, regulations, etc.)
SECTION 2 – ANALYSIS
  2.1  Aim
  2.2+ Variable subsections
SECTION 3 – CONCLUSIONS
  3.1  Safety issues directly contributing... that have been addressed or resulted in recommendations
  3.2  Other safety issues directly contributing...
  3.3  Safety issues not directly contributing... that have been addressed or resulted in recommendations
SECTION 4 – ACTION TAKEN
  4.1  MAIB actions
  4.2  Actions taken by other organisations
SECTION 5 – RECOMMENDATIONS
  Numbered recommendations (e.g. 2025/147) directed at specific organisations
ANNEXES (optional)
```

Key observations:
- The **vessel/voyage/casualty tables** on page 2 (Section 1.1) are structured key-value tables — these map directly to `chirp_report_metadata`
- **Safety issues** in Section 3 are numbered lists under subcategory headings, with references back to analysis sections (e.g. `[2.5.1]`)
- **Recommendations** in Section 5 have MAIB reference codes (e.g. `2025/147`) and are directed at named organisations
- Reports vary significantly in length — Karin is 28 pages, Finnmaster is 99+ pages
- Subsection structure within the main sections varies between reports

## Ingestion Pipeline Steps

For each uploaded PDF:

### Step 1: Parse PDF text
Extract all text from the PDF. The cover page contains the title, vessel name, location, date, and severity classification. Page 2 typically contains the structured vessel/voyage/casualty tables.

### Step 2: Create document record
- Generate a content hash for deduplication (check against existing `documents.hash`)
- Extract title from cover page
- Extract publication date from cover page (e.g. "OCTOBER 2025")
- Look up or create author record (typically "Marine Accident Investigation Branch")
- Insert into `documents` table

### Step 3: Extract report metadata
Parse the structured tables from Section 1.1 (Particulars of vessel and accident):
- **Vessel Particulars**: vessel name, flag, type, registered owner, construction, year of build, length, gross tonnage
- **Voyage Particulars**: port of departure, port of arrival, type of voyage, manning
- **Marine Casualty Information**: date and time, type of casualty, location of incident, injuries/fatalities, vessel operation, environmental conditions

Insert into `chirp_report_metadata` with `document_id`.

### Step 4: Split into sections
Identify top-level section boundaries by matching headings:
- `SYNOPSIS`
- `SECTION 1 – FACTUAL INFORMATION` (or similar patterns)
- `SECTION 2 – ANALYSIS`
- `SECTION 3 – CONCLUSIONS`
- `SECTION 4 – ACTION TAKEN`
- `SECTION 5 – RECOMMENDATIONS`
- `GLOSSARY OF ABBREVIATIONS AND ACRONYMS`

Create a `sections` record for each with `document_id`, `name`, and `position`.

### Step 5: Split sections into sentences
For each section, split the text content into sentences. Each sentence gets:
- `text` — the sentence text
- `text_type` — paragraph, list_item, heading, table_row
- `position` — ordinal position within the section
- `section_id` — FK to the section
- `document_id` — FK to the document (denormalised)

### Step 6: Extract safety issues
From Section 3 (Conclusions), parse the numbered safety issues. The conclusions section has subcategories (3.1, 3.2, 3.3) each containing numbered items. Each safety issue is stored in `chirp_safety_issues` with `document_id` and `name` (the issue text).

Link safety issues to their corresponding sentences via `chirp_safety_issue_sentences`.

### Step 7: Extract recommendations
From Section 5, parse the numbered recommendations. Each recommendation has:
- A reference code (e.g. `2025/147`)
- A target organisation (e.g. "Orkney Islands Council Harbour Authority")
- The recommendation text (may include sub-bullets)

Store in `chirp_recommendations` with `document_id`, `recommendation` text, and `organisation_id` (look up or create in `chirp_organisations`).

## Reference: Existing CHIRP Repo Code

The existing Zig Zag CHIRP repo (`/home/jack/tandemhub/zigzag/CHIRP/`) uses web scraping to ingest MAIB reports from gov.uk HTML pages. Our pipeline does the same extraction but from PDFs. The patterns below should be adapted.

### Section extraction pattern
From `chirp/collect/documentprocessors/maib_processor.py` — the approach of finding a header, then collecting lines until the next header:

```python
# Safety issues extraction — find header, collect until next section
def _extract_safety_issues(self, soup):
    text = soup.get_text()
    cleaned_lines = [ln.strip() for ln in text.split('\n') if ln.strip()]
    safety_indices = [i for i, line in enumerate(cleaned_lines) if line == 'Safety issues']

    for start_idx in safety_indices:
        safety_lines = []
        stop_headers = {
            'Recommendations', 'MAIB actions taken',
            'Statement from the Chief Inspector of Marine Accidents',
            'Related publications', 'Updates to this page'
        }
        for ln in cleaned_lines[start_idx + 1:]:
            if ln in stop_headers:
                break
            if len(ln) >= 20 or ln.startswith(('-', '*')) or (ln.split('.', 1)[0].isdigit() and '.' in ln):
                safety_lines.append(ln)
        if safety_lines:
            return '\n'.join(safety_lines)
    return ""

# Recommendations extraction — same pattern
def _extract_recommendations(self, soup):
    text = soup.get_text()
    cleaned_lines = [ln.strip() for ln in text.split('\n') if ln.strip()]
    rec_indices = [i for i, line in enumerate(cleaned_lines) if line == 'Recommendations']

    for start_idx in rec_indices:
        rec_lines = []
        stop_headers = {
            'MAIB actions taken', 'Related publications',
            'Updates to this page', 'Further reading'
        }
        for ln in cleaned_lines[start_idx + 1:]:
            if ln in stop_headers:
                break
            if len(ln) >= 15 or ln.startswith(('-', '*')) or (ln.split('.', 1)[0].isdigit() and '.' in ln):
                rec_lines.append(ln)
        if rec_lines:
            return '\n'.join(rec_lines)
    return ""
```

**Adaptation needed**: In PDFs, the section headers are uppercase (e.g. `SECTION 3 – CONCLUSIONS`, `SECTION 5 – RECOMMENDATIONS`) rather than the HTML heading text. The stop-header detection needs to use PDF heading patterns instead of HTML page structure.

### Metadata extraction pattern
From `maib_processor.py` — extracting key-value metadata by finding label lines:

```python
# Location extraction — find "Location:" label, grab value from same or next line
def _extract_location(self, soup):
    text = soup.get_text()
    cleaned_lines = [ln.strip() for ln in text.split('\n') if ln.strip()]
    for i, line in enumerate(cleaned_lines):
        if line.startswith('Location:'):
            location = line.replace('Location:', '').strip()
            if location and ':' not in location:
                return location
            if i + 1 < len(cleaned_lines):
                next_line = cleaned_lines[i + 1]
                if next_line and not next_line.endswith(':'):
                    return next_line
    return ""
```

**Adaptation needed**: In the PDF, the vessel/voyage/casualty metadata is in structured **tables** (key-value pairs in two columns), not free-form text with labels. The PDF parser needs to handle table extraction from the Section 1.1 tables. The keys are consistent: "Vessel's name", "Flag", "Type", "Date and time", "Location of incident", "Injuries/fatalities", etc.

### Document creation and deduplication pattern
From `chirp/process/chirp_sqlliteadapter.py`:

```python
# Deduplication — check by ID or by content match
self.cursor.execute('''
    SELECT id FROM documents
    WHERE id = ? OR (filename = ? AND content = ? AND filepath = ?)
''', (document.document_id, document.filename, document.content, str(document.filepath)))

if self.cursor.fetchone() is not None:
    return None  # duplicate, skip
```

**Adaptation needed**: Our deduplication uses a content hash stored in `documents.hash`. Hash the full PDF text content and check against existing records before inserting.

### Full ingestion orchestration
From `chirp/collect/documentprocessors/create_chirpdb.py`:

```python
def create_chirpdb():
    scraper = MAIBWebScraper()

    for url in urls:
        # 1. Extract metadata
        metadata = scraper.extract_metadata(url)

        # 2. Extract sections
        sections = scraper.read(url)

        # 3. Enrich with geo data
        location = metadata.metadata.get("location", "")
        lat_long = get_lat_long(location)
        metadata.metadata["lat_long"] = lat_long

        # 4. Build full content from sections
        content = "\n\n".join([section.content for section in sections])

        # 5. Create document object
        document = Document(
            filename=metadata.title or f"maib_report_{i}",
            content=content,
            filepath=url,
            metadata=metadata
        )

        # 6. Store in database
        doc_id = adapter.create(document)
```

**Adaptation needed**: Our pipeline replaces the web scraper with a PDF parser, stores into Supabase via the existing `SupabaseService`, and adds the section/sentence decomposition steps that the original didn't do (it stored content as a single blob).

## Schema Changes Required

The current `sections` table needs two new columns:

```sql
ALTER TABLE public.sections
  ADD COLUMN document_id bigint REFERENCES public.documents(id),
  ADD COLUMN position integer;
```

This denormalises the document relationship (also available via sentences) and adds ordering.

## Database Tables Involved

### Written at ingestion time:
- `documents` — one row per PDF
- `authors` — lookup/create for the publishing body (MAIB)
- `chirp_report_metadata` — vessel/voyage/casualty data from Section 1.1 tables
- `sections` — top-level document sections with position and document_id
- `sentences` — section text split into sentences with position, text_type, section_id, document_id
- `chirp_safety_issues` — from Section 3 (Conclusions)
- `chirp_safety_issue_sentences` — links safety issues to their sentences
- `chirp_recommendations` — from Section 5
- `chirp_organisations` — target organisations for recommendations

### Written by analysis tool (POST back to API):
- `chirp_analysis` — analysis record per sentence
- `chirp_analysis_shield_codes` — shield code assignments per sentence
- Sentence updates: `relevance_score`, embeddings (pgvector)
