"""URL ingestion pipeline. Web-scraped metadata + PDF for remaining fields."""
import logging

import services.ingest_to_db as db_service
from services.pdf_parsing import parse_pdf
from services.scraper import scrape
from services.supabase.service import SupabaseService
from utils.pdf import parse_accident_date, parse_loss_of_life

logger = logging.getLogger(__name__)

# Fields sourced from the GOV.UK webpage:
#   title, publication_date, vessel_type, accident_date, accident_location
#
# Fields sourced from the PDF:
#   vessel_name, severity, loss_of_life, port_of_origin, destination,
#   accident_type, page_count, pdf_subject, pdf_author, sentences


def ingest_from_url(db: SupabaseService, url: str) -> dict:
    logger.info("Scraping %s...", url)
    scraped = scrape(url)

    logger.info("Parsing PDF...")
    parsed = parse_pdf(scraped.pdf_bytes)
    pdf_meta = parsed.metadata
    report_meta = parsed.report_metadata
    logger.info("  %s characters, %s pages", len(parsed.full_text), pdf_meta.page_count)

    author = db_service.get_or_create_author(db, db_service.resolve_author_name(pdf_meta.pdf_author))
    document = db.create_record("documents", {
        "title": scraped.title,
        "filename": scraped.pdf_url.split("/")[-1],
        "hash": db_service.check_duplicate(db, parsed.full_text),
        "publication_date": scraped.publication_date,
        "author_id": author["id"],
        "url": url,
    })
    logger.info("  Created document %s", document["id"])

    db.create_record("chirp_accident_metadata", {
        "document_id": document["id"],
        # From webpage
        "vessel_type": scraped.vessel_type,
        "accident_date": parse_accident_date(scraped.accident_date),
        "accident_location": scraped.accident_location,
        # From PDF
        "vessel_name": report_meta.vessel_name,
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
