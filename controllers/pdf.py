"""PDF ingestion pipeline. All data sourced from the PDF."""
import logging

import services.ingest_to_db as db_service
from services.pdf_parsing import parse_pdf
from services.supabase.service import SupabaseService
from utils.pdf import extract_publication_date, extract_title, parse_accident_date, parse_loss_of_life

logger = logging.getLogger(__name__)


def ingest_pdf(db: SupabaseService, pdf_bytes: bytes, filename: str) -> dict:
    logger.info("Parsing PDF...")
    parsed = parse_pdf(pdf_bytes)
    pdf_meta = parsed.metadata
    report_meta = parsed.report_metadata
    logger.info("  %s characters, %s pages", len(parsed.full_text), pdf_meta.page_count)

    author = db_service.get_or_create_author(db, db_service.resolve_author_name(pdf_meta.pdf_author))
    document = db.create_record("documents", {
        "title": pdf_meta.pdf_title or extract_title(parsed.full_text),
        "filename": filename,
        "hash": db_service.check_duplicate(db, parsed.full_text),
        "publication_date": extract_publication_date(parsed.full_text),
        "author_id": author["id"],
    })
    logger.info("  Created document %s", document["id"])

    db.create_record("chirp_accident_metadata", {
        "document_id": document["id"],
        "vessel_name": report_meta.vessel_name,
        "vessel_type": report_meta.vessel_type,
        "accident_date": parse_accident_date(report_meta.accident_date),
        "accident_location": report_meta.accident_location,
        "severity": report_meta.severity,
        "loss_of_life": parse_loss_of_life(report_meta.loss_of_life),
        "port_of_origin": report_meta.port_of_origin,
        "destination": report_meta.destination,
        "accident_type": report_meta.accident_type,
        "page_count": pdf_meta.page_count,
        "pdf_subject": pdf_meta.pdf_subject,
        "pdf_author": pdf_meta.pdf_author,
    })

    db_service.store_sentences(db, parsed.full_text, document["id"])
    return document
