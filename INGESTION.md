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
| `metadata.vessel_type`       | `gem-c-metadata` `"Vessel type"` term        | Section 1.1 table                      |
| `metadata.accident_date`     | `gem-c-metadata` `"Date of occurrence"` term | Section 1.1 table                      |
| `metadata.accident_location` | `og:description` `"Location: ..."`           | Section 1.1 table                      |
| `metadata.vessel_name`       | Section 1.1 table                            | —                                      |
| `metadata.severity`          | Section 1.1 table                            | —                                      |
| `metadata.loss_of_life`      | Section 1.1 table                            | —                                      |
| `metadata.port_of_origin`    | Section 1.1 table                            | —                                      |
| `metadata.destination`       | Section 1.1 table                            | —                                      |
| `metadata.accident_type`     | Section 1.1 table                            | —                                      |
| `metadata.page_count`        | PDF page count                               | —                                      |
| `metadata.pdf_subject`       | PDF `Subject` metadata                       | —                                      |
| `metadata.pdf_author`        | PDF `Author` metadata                        | —                                      |
| `sentences.*`                | Full text extraction (pdfplumber)            | —                                      |

## `POST /documents` (file upload)

Same as above except there is no GOV.UK page — all fields come from PDF only.
`documents.url` is not stored.
