import hashlib
from typing import Optional

from fastapi import HTTPException

from services.pdf_parser import (
    extract_full_text,
    extract_metadata_from_tables,
    extract_pdf_metadata,
    extract_publication_date,
    extract_recommendations,
    extract_safety_issues,
    extract_title,
    split_into_sections,
    split_into_sentences,
)
from services.supabase.service import SupabaseService


class IngestionService:
    def __init__(self, supabase: SupabaseService):
        self.db = supabase

    def ingest(self, pdf_bytes: bytes, filename: str) -> dict:
        """Run the full 7-step pipeline. Returns the created document record."""

        # Step 1: Parse PDF
        full_text = extract_full_text(pdf_bytes)
        pdf_metadata = extract_pdf_metadata(pdf_bytes)

        # Step 2: Create document (with dedup check via hash)
        content_hash = hashlib.sha256(full_text.encode()).hexdigest()
        existing = self.db.get_records("documents", {"hash": content_hash}, limit=1)
        print(f"DEBUG: hash={content_hash[:16]}..., existing={len(existing)} items")
        if existing:
            raise HTTPException(status_code=409, detail="Document already exists")

        author = self._get_or_create_author("Marine Accident Investigation Branch")
        title = pdf_metadata.get("pdf_title") or extract_title(full_text)
        pub_date = extract_publication_date(full_text)

        document = self.db.create_record(
            "documents",
            {
                "title": title,
                "filename": filename,
                "hash": content_hash,
                "publication_date": pub_date,
                "author_id": author["id"],
            },
        )
        doc_id = document["id"]

        # Step 3: Extract and store report metadata
        metadata = extract_metadata_from_tables(pdf_bytes)
        metadata["document_id"] = doc_id
        metadata["page_count"] = pdf_metadata.get("page_count")
        metadata["pdf_subject"] = pdf_metadata.get("pdf_subject")
        self.db.create_record("chirp_report_metadata", metadata)

        # Step 4: Split into sections and store
        sections = split_into_sections(full_text)
        section_records = []
        for section in sections:
            record = self.db.create_record(
                "sections",
                {
                    "name": section["name"],
                    "document_id": doc_id,
                    "position": section["position"],
                },
            )
            record["_text"] = section["text"]
            section_records.append(record)

        # Step 5: Split sections into sentences and store
        for section_rec in section_records:
            sentences = split_into_sentences(section_rec["_text"])
            for sent in sentences:
                self.db.create_record(
                    "sentences",
                    {
                        "text": sent["text"],
                        "text_type": sent["text_type"],
                        "position": sent["position"],
                        "section_id": section_rec["id"],
                        "document_id": doc_id,
                    },
                )

        # Step 6: Extract and store safety issues
        conclusions = next(
            (s for s in sections if "CONCLUSIONS" in s["name"].upper()), None
        )
        if conclusions:
            issues = extract_safety_issues(conclusions["text"])
            for issue_text in issues:
                self.db.create_record(
                    "chirp_safety_issues",
                    {"document_id": doc_id, "name": issue_text},
                )

        # Step 7: Extract and store recommendations
        recs_section = next(
            (s for s in sections if "RECOMMENDATIONS" in s["name"].upper()), None
        )
        if recs_section:
            recs = extract_recommendations(recs_section["text"])
            for rec in recs:
                org_name = rec.get("organisation")
                org = self._get_or_create_org(org_name) if org_name else None
                self.db.create_record(
                    "chirp_recommendations",
                    {
                        "document_id": doc_id,
                        "recommendation": rec["text"],
                        "organisation_id": org["id"] if org else None,
                    },
                )

        return document

    def _get_or_create_author(self, name: str) -> dict:
        """Get existing author by name or create a new one."""
        existing = self.db.get_records("authors", {"name": name}, limit=1)
        if existing:
            return existing[0]

        return self.db.create_record("authors", {"name": name})

    def _get_or_create_org(self, name: str) -> Optional[dict]:
        """Get existing organisation by name or create a new one."""
        if not name or not name.strip():
            return None

        name = name.strip()
        existing = self.db.get_records("chirp_organisations", {"name": name}, limit=1)
        if existing:
            return existing[0]

        return self.db.create_record("chirp_organisations", {"name": name})
