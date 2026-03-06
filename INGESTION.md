# Ingestion — Data Sources

## `POST /documents/from-url` (GOV.UK page + PDF)

| Field                        | Primary source                               | Fallback                               |
| ---------------------------- | -------------------------------------------- | -------------------------------------- |
| `documents.title`            | `og:title` meta tag                          | PDF `Title` metadata → text extraction |
| `documents.publication_date` | `govuk:first-published-at` meta tag          | Cover page month/year text             |
| `documents.url`              | URL passed in                                | —                                      |
| `documents.filename`         | PDF filename from download URL               | —                                      |
| `documents.author_id`        | PDF `Author` metadata                        | `"Unknown"`                            |
| `documents.hash`             | SHA-256 of full text                         | —                                      |
| `metadata.vessel_type`       | `gem-c-metadata` `"Vessel type"` term        | Any table in the PDF (key matches `^type$`) |
| `metadata.accident_date`     | `gem-c-metadata` `"Date of occurrence"` term | Any table in the PDF (key matches `date.*time`) |
| `metadata.accident_location` | `og:description` `"Location: ..."`           | Any table in the PDF (key matches `location.*incident` etc.) |
| `metadata.vessel_name`       | Any table in the PDF (key matches `vessel.*name`) | —                             |
| `metadata.severity`          | Any table in the PDF (key matches `type.*casualty` etc.) | —                    |
| `metadata.loss_of_life`      | Any table in the PDF (key matches `injur\|fatal\|casualt`) | —                  |
| `metadata.port_of_origin`    | Any table in the PDF (key matches `port.*departure` etc.) | —                   |
| `metadata.destination`       | Any table in the PDF (key matches `port.*arrival`) | —                        |
| `metadata.accident_type`     | Any table in the PDF (key matches `type.*voyage` etc.) | —                     |
| `metadata.page_count`        | PDF page count                               | —                                      |
| `metadata.pdf_subject`       | PDF `Subject` metadata                       | —                                      |
| `metadata.pdf_author`        | PDF `Author` metadata                        | —                                      |
| `sentences.*`                | Full text extraction (pdfplumber)            | —                                      |

## `POST /documents` (file upload)

Same as above except there is no GOV.UK page — all fields come from PDF only.
`documents.url` is not stored.
