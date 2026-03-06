"""URL ingestion path. Web-scraped fields take precedence; PDF supplies the rest."""
import logging

from services.ingestion.shared import (
    check_duplicate,
    get_or_create_author,
    resolve_author_name,
    store_sentences,
)
from services.maib_scraper import scrape as scrape_maib
from services.pdf_parser import parse_accident_date, parse_loss_of_life, parse_pdf
from services.supabase.service import SupabaseService

logger = logging.getLogger(__name__)

# Fields sourced from the GOV.UK webpage:
#   title, publication_date, vessel_type, accident_date, accident_location
#
# Fields sourced from the PDF:
#   vessel_name, severity, loss_of_life, port_of_origin, destination,
#   accident_type, page_count, pdf_subject, pdf_author, sentences


def ingest_from_url(db: SupabaseService, url: str) -> dict:
    """Scrape a GOV.UK MAIB report page and ingest the PDF.

    Raises httpx.HTTPStatusError on HTTP errors fetching the page or PDF.
    Raises httpx.RequestError on network failures.
    Raises ValueError if no PDF is found on the page.
    Returns the created document record.
    """
    logger.info("Scraping %s...", url)
    scraped = scrape_maib(url)

    logger.info("Step 1: Extracting text from PDF...")
    parsed = parse_pdf(scraped.pdf_bytes)
    full_text = parsed.full_text
    pdf_meta = parsed.metadata
    report_meta = parsed.report_metadata
    logger.info("  Extracted %s characters, %s pages", len(full_text), pdf_meta.page_count)

    logger.info("Step 2: Creating document record...")
    author = get_or_create_author(db, resolve_author_name(pdf_meta.pdf_author))
    document = db.create_record("documents", {
        "title": scraped.title,
        "filename": scraped.pdf_url.split("/")[-1],
        "hash": check_duplicate(db, full_text),
        "publication_date": scraped.publication_date,
        "author_id": author["id"],
        "url": url,
    })
    doc_id = document["id"]
    logger.info("  Created document %s", doc_id)

    logger.info("Step 3: Storing report metadata...")
    db.create_record("chirp_accident_metadata", {
        "document_id": doc_id,
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

    store_sentences(db, full_text, doc_id)
    logger.info("Ingestion complete")
    return document
