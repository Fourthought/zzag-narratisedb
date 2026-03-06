import hashlib
import logging
from typing import Optional

import httpx

from services.maib_scraper import ScrapedReport, scrape as scrape_maib
from services.pdf_parser import (
    parse_pdf,
    extract_publication_date,
    extract_title,
    parse_accident_date,
    parse_loss_of_life,
    split_into_sentences,
)
from services.supabase.service import SupabaseService

logger = logging.getLogger(__name__)


class DuplicateDocumentError(Exception):
    """Raised when a document with the same content already exists."""
    pass


class UnsupportedDocumentError(Exception):
    """Raised when the document type is not supported."""
    pass


class IngestionService:
    def __init__(self, supabase: SupabaseService):
        self.db = supabase

    def ingest(self, pdf_bytes: bytes, filename: str) -> dict:
        """Ingest a PDF file. Returns the created document record."""
        return self._ingest_pdf(pdf_bytes, filename)

    def ingest_from_url(self, url: str) -> dict:
        """Scrape a GOV.UK MAIB report page and ingest the PDF.

        Raises httpx.HTTPStatusError on HTTP errors fetching the page or PDF.
        Raises httpx.RequestError on network failures.
        Raises ValueError if no PDF is found on the page.
        Returns the created document record.
        """
        logger.info("Scraping %s...", url)
        scraped = scrape_maib(url)
        filename = scraped.pdf_url.split("/")[-1]
        return self._ingest_pdf(scraped.pdf_bytes, filename, source_url=url, web=scraped)

    def _ingest_pdf(
        self,
        pdf_bytes: bytes,
        filename: str,
        source_url: Optional[str] = None,
        web: Optional[ScrapedReport] = None,
    ) -> dict:
        """Run the full ingestion pipeline. Returns the created document record."""

        logger.info("Step 1: Extracting text from PDF...")
        parsed = parse_pdf(pdf_bytes)
        full_text = parsed.full_text
        pdf_metadata = parsed.metadata
        report_metadata = parsed.report_metadata
        logger.info("  Extracted %s characters, %s pages", len(full_text), pdf_metadata.page_count)

        logger.info("Step 2: Creating document record...")
        content_hash = hashlib.sha256(full_text.encode()).hexdigest()
        existing = self.db.get_records("documents", {"hash": content_hash}, limit=1)
        if existing:
            raise DuplicateDocumentError("Document already exists")

        pdf_author = pdf_metadata.pdf_author
        author_name = self._resolve_author_name(pdf_author)
        author = self._get_or_create_author(author_name)
        title = (web and web.title) or pdf_metadata.pdf_title or extract_title(full_text)
        pub_date = (web and web.publication_date) or extract_publication_date(full_text)

        document = self.db.create_record(
            "documents",
            {
                "title": title,
                "filename": filename,
                "hash": content_hash,
                "publication_date": pub_date,
                "author_id": author["id"],
                "url": source_url,
            },
        )
        doc_id = document["id"]
        logger.info("  Created document %s: %s...", doc_id, title[:60])

        logger.info("Step 3: Storing report metadata...")
        self.db.create_record("chirp_report_metadata", {
            "document_id": doc_id,
            "page_count": pdf_metadata.page_count,
            "pdf_subject": pdf_metadata.pdf_subject,
            "pdf_author": pdf_author,
            "vessel_name": report_metadata.vessel_name,
            "vessel_type": (web and web.vessel_type) or report_metadata.vessel_type,
            "accident_date": parse_accident_date((web and web.accident_date) or report_metadata.accident_date),
            "accident_location": (web and web.accident_location) or report_metadata.accident_location,
            "severity": report_metadata.severity,
            "loss_of_life": parse_loss_of_life(report_metadata.loss_of_life),
            "port_of_origin": report_metadata.port_of_origin,
            "destination": report_metadata.destination,
            "accident_type": report_metadata.accident_type,
        })
        logger.info("  Metadata stored")

        logger.info("Step 4: Splitting text into sentences...")
        all_sentences = split_into_sentences(full_text)
        logger.info("  Found %s sentences", len(all_sentences))

        logger.info("Step 5: Storing sentences...")
        sentence_records = [
            {
                "text": sent["text"],
                "text_type": sent["text_type"],
                "position": position,
                "document_id": doc_id,
            }
            for position, sent in enumerate(all_sentences)
        ]
        self.db.create_records_batch("sentences", sentence_records)
        logger.info("  Stored %s sentences", len(all_sentences))

        logger.info("Ingestion complete")
        return document

    def _resolve_author_name(self, pdf_author: Optional[str]) -> str:
        if not pdf_author:
            return "Unknown"
        if "gov.uk/maib" in pdf_author.lower():
            return "MAIB"
        return pdf_author

    def _get_or_create_author(self, name: str) -> dict:
        """Get existing author by name or create a new one."""
        existing = self.db.get_records("authors", {"name": name}, limit=1)
        if existing:
            return existing[0]

        return self.db.create_record("authors", {"name": name})
