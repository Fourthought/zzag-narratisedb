"""PDF-only ingestion path. All data sourced from the PDF."""
import logging

from services.ingestion.shared import (
    check_duplicate,
    get_or_create_author,
    resolve_author_name,
    store_sentences,
)
from services.pdf_parser import (
    extract_publication_date,
    extract_title,
    parse_accident_date,
    parse_loss_of_life,
    parse_pdf,
)
from services.supabase.service import SupabaseService

logger = logging.getLogger(__name__)


def ingest(db: SupabaseService, pdf_bytes: bytes, filename: str) -> dict:
    """Ingest a PDF file. Returns the created document record."""
    logger.info("Step 1: Extracting text from PDF...")
    parsed = parse_pdf(pdf_bytes)
    full_text = parsed.full_text
    pdf_meta = parsed.metadata
    report_meta = parsed.report_metadata
    logger.info("  Extracted %s characters, %s pages", len(full_text), pdf_meta.page_count)

    logger.info("Step 2: Creating document record...")
    author = get_or_create_author(db, resolve_author_name(pdf_meta.pdf_author))
    document = db.create_record("documents", {
        "title": pdf_meta.pdf_title or extract_title(full_text),
        "filename": filename,
        "hash": check_duplicate(db, full_text),
        "publication_date": extract_publication_date(full_text),
        "author_id": author["id"],
    })
    doc_id = document["id"]
    logger.info("  Created document %s", doc_id)

    logger.info("Step 3: Storing report metadata...")
    db.create_record("chirp_accident_metadata", {
        "document_id": doc_id,
        "page_count": pdf_meta.page_count,
        "pdf_subject": pdf_meta.pdf_subject,
        "pdf_author": pdf_meta.pdf_author,
        "vessel_name": report_meta.vessel_name,
        "vessel_type": report_meta.vessel_type,
        "accident_date": parse_accident_date(report_meta.accident_date),
        "accident_location": report_meta.accident_location,
        "severity": report_meta.severity,
        "loss_of_life": parse_loss_of_life(report_meta.loss_of_life),
        "port_of_origin": report_meta.port_of_origin,
        "destination": report_meta.destination,
        "accident_type": report_meta.accident_type,
    })

    store_sentences(db, full_text, doc_id)
    logger.info("Ingestion complete")
    return document
