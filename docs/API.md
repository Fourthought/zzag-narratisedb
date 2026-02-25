# CHIRPdb API Routes

## Documents

| Method | Route                                   | Description                                                                                | Role           |
| ------ | --------------------------------------- | ------------------------------------------------------------------------------------------ | -------------- |
| POST   | `/documents`                            | Ingest document, extract recommendations, safety issues, identify organisations and author | Admin          |
| GET    | `/documents`                            | List all documents with author                                                             | Admin, Analyst |
| GET    | `/documents/{id}`                       | Document metadata with author                                                              | Admin, Analyst |
| GET    | `/documents/{id}/full`                  | Reconstructed document — all sentences ordered by position                                 | Admin, Analyst |
| GET    | `/documents/{id}/sections`              | List sections within a document                                                            | Admin, Analyst |
| GET    | `/documents/{id}/sections/{section_id}` | Reconstructed section — ordered sentences with relevance and shield codes                  | Admin, Analyst |
| GET    | `/documents/{id}/sentences`             | All sentences for a document with relevance and shield codes                               | Admin, Analyst |
| GET    | `/documents/{id}/metadata`              | CHIRP incident metadata                                                                    | Admin, Analyst |
| GET    | `/documents/{id}/recommendations`       | All recommendations with organisations                                                     | Admin, Analyst |
| GET    | `/documents/{id}/safety-issues`         | All safety issues with their constituent sentences                                         | Admin, Analyst |
| DELETE | `/documents/{id}`                       | Delete document and all related records                                                    | Admin          |

---

## Authors

| Method | Route                     | Description                  | Role           |
| ------ | ------------------------- | ---------------------------- | -------------- |
| GET    | `/authors`                | List all authors             | Admin, Analyst |
| GET    | `/authors/{id}`           | Get author detail            | Admin, Analyst |
| GET    | `/authors/{id}/documents` | All documents by this author | Admin, Analyst |
| PATCH  | `/authors/{id}`           | Update author fields         | Admin          |

---

## Sentences

| Method | Route                       | Description                                           | Role           |
| ------ | --------------------------- | ----------------------------------------------------- | -------------- |
| GET    | `/sentences/{id}`           | Single sentence with relevance score and shield codes | Admin, Analyst |
| PATCH  | `/sentences/{id}/relevance` | Update relevance score                                | Admin, Analyst |

---

## Shield Codes

| Method | Route                                           | Description                                                     | Role           |
| ------ | ----------------------------------------------- | --------------------------------------------------------------- | -------------- |
| POST   | `/documents/{id}/shield-codes`                  | Apply shield code(s) to multiple sentences (external)           | Admin, Analyst |
| POST   | `/sentences/{id}/shield-codes`                  | Apply shield code(s) to a sentence (external)                   | Admin, Analyst |
| DELETE | `/sentences/{id}/shield-codes/{shield_code_id}` | Remove a shield code from a sentence                            | Admin, Analyst |
| GET    | `/shield-codes`                                 | List all shield codes with categories                           | Admin, Analyst |
| GET    | `/shield-codes/{id}`                            | Get shield code detail                                          | Admin, Analyst |
| GET    | `/shield-codes/{id}/sentences`                  | All sentences tagged with this shield code, grouped by document | Admin, Analyst |

---

## Safety Issues

| Method | Route                                         | Description                                                  | Role           |
| ------ | --------------------------------------------- | ------------------------------------------------------------ | -------------- |
| GET    | `/safety-issues/{id}`                         | Safety issue with all constituent sentences and shield codes | Admin, Analyst |
| POST   | `/safety-issues/{id}/sentences`               | Add sentence to a safety issue                               | Admin          |
| DELETE | `/safety-issues/{id}/sentences/{sentence_id}` | Remove sentence from a safety issue                          | Admin          |

---

## Recommendations

| Method | Route                   | Description                                        | Role           |
| ------ | ----------------------- | -------------------------------------------------- | -------------- |
| GET    | `/recommendations/{id}` | Single recommendation with organisation            | Admin, Analyst |
| PATCH  | `/recommendations/{id}` | Update recommendation fields (e.g. is_implemented) | Admin, Analyst |
| DELETE | `/recommendations/{id}` | Delete a recommendation                            | Admin          |

---

## Organisations

| Method | Route                                 | Description                                       | Role           |
| ------ | ------------------------------------- | ------------------------------------------------- | -------------- |
| GET    | `/organisations`                      | List all organisations                            | Admin, Analyst |
| GET    | `/organisations/{id}`                 | Organisation detail                               | Admin, Analyst |
| GET    | `/organisations/{id}/recommendations` | All recommendations directed at this organisation | Admin, Analyst |
| PATCH  | `/organisations/{id}`                 | Update organisation name                          | Admin          |

---

## Notes

- No POST on recommendations, organisations, authors, sentences, sections, or safety issues — all created during document ingestion
- Shield codes on sentences are posted externally after ingestion
- Reconstructed endpoints (full document, section) assemble ordered sentences via `position`
- Provenance chain: sentence → document; shield code → sentence → document; safety issue → sentences → document
- `chirp_shield_code_categories` has no direct routes — always returned as part of shield code responses
