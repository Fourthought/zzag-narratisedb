# Ingestion — Data Sources

See `services/ingestion/pdf.py` and `services/ingestion/url.py` for implementation.

## `POST /documents/from-url` (`services/ingestion/url.py`)

### From GOV.UK webpage

| Field | Source |
|---|---|
| `documents.title` | `og:title` meta tag |
| `documents.publication_date` | `govuk:first-published-at` meta tag |
| `documents.url` | URL passed in |
| `metadata.vessel_type` | `gem-c-metadata` `"Vessel type"` term |
| `metadata.accident_date` | `gem-c-metadata` `"Date of occurrence"` term |
| `metadata.accident_location` | `og:description` `"Location: ..."` |

### From PDF

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

## `POST /documents` (`services/ingestion/pdf.py`)

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
