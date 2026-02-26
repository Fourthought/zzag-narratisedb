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
    split_into_sentences,
)
from services.supabase.service import SupabaseService


class IngestionService:
    def __init__(self, supabase: SupabaseService):
        self.db = supabase

    def ingest(self, pdf_bytes: bytes, filename: str) -> dict:
        """Run the full ingestion pipeline. Returns the created document record."""

        print("Step 1: Extracting text from PDF...")
        full_text = extract_full_text(pdf_bytes)
        pdf_metadata = extract_pdf_metadata(pdf_bytes)
        print(f"  Extracted {len(full_text)} characters, {pdf_metadata.get('page_count')} pages")

        print("Step 2: Creating document record...")
        content_hash = hashlib.sha256(full_text.encode()).hexdigest()
        existing = self.db.get_records("documents", {"hash": content_hash}, limit=1)
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
        print(f"  Created document {doc_id}: {title[:60]}...")

        print("Step 3: Storing report metadata...")
        metadata = extract_metadata_from_tables(pdf_bytes)
        metadata["document_id"] = doc_id
        metadata["page_count"] = pdf_metadata.get("page_count")
        metadata["pdf_subject"] = pdf_metadata.get("pdf_subject")
        self.db.create_record("chirp_report_metadata", metadata)
        print("  Metadata stored")

        print("Step 4: Splitting text into sentences...")
        all_sentences = split_into_sentences(full_text)
        print(f"  Found {len(all_sentences)} sentences")

        print("Step 5: Storing sentences...")
        for position, sent in enumerate(all_sentences):
            sentence_data = {
                "text": sent["text"],
                "text_type": sent["text_type"],
                "position": position,
                "document_id": doc_id,
            }
            if "relevance_score" in sent:
                sentence_data["relevance_score"] = sent["relevance_score"]
            self.db.create_record("sentences", sentence_data)
        print(f"  Stored {len(all_sentences)} sentences")

        print("Step 6: Extracting safety issues...")
        conclusions_text = self._extract_section_text(all_sentences, "CONCLUSION", "RECOMMENDATION")
        if conclusions_text:
            issues = extract_safety_issues(conclusions_text)
            print(f"  Found {len(issues)} safety issues")
            for issue_text in issues:
                self.db.create_record(
                    "chirp_safety_issues",
                    {"document_id": doc_id, "name": issue_text},
                )
        else:
            print("  No CONCLUSIONS section found")

        print("Step 7: Extracting recommendations...")
        recommendations_text = self._extract_section_text(all_sentences, "RECOMMENDATION", None)
        if recommendations_text:
            recs = extract_recommendations(recommendations_text)
            print(f"  Found {len(recs)} recommendations")
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
        else:
            print("  No RECOMMENDATIONS section found")

        print("Ingestion complete")
        return document

    def _extract_section_text(self, sentences: list, start_heading: str, end_heading: str | None) -> str:
        """Extract text from sentences between two headings (exclusive).

        Args:
            sentences: List of sentence dicts
            start_heading: Text of heading to start from (case-insensitive, partial match)
            end_heading: Text of heading to end at (exclusive), or None for end of document

        Returns:
            Joined text of sentences between the headings
        """
        in_section = False
        section_sentences = []

        for sent in sentences:
            if sent["text_type"] == "heading":
                if in_section and end_heading and end_heading in sent["text"].upper():
                    # Reached end heading
                    break
                if start_heading in sent["text"].upper():
                    # Found start heading - include sentences after this
                    in_section = True
                    continue
            elif in_section:
                section_sentences.append(sent["text"])

        return "\n".join(section_sentences)

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
