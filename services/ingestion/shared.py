import hashlib
import logging
from typing import Optional

from services.pdf_parser import split_into_sentences
from services.supabase.service import SupabaseService

logger = logging.getLogger(__name__)


class DuplicateDocumentError(Exception):
    """Raised when a document with the same content already exists."""
    pass


class UnsupportedDocumentError(Exception):
    """Raised when the document type is not supported."""
    pass


def check_duplicate(db: SupabaseService, full_text: str) -> str:
    """Return content hash, or raise DuplicateDocumentError if already ingested."""
    content_hash = hashlib.sha256(full_text.encode()).hexdigest()
    if db.get_records("documents", {"hash": content_hash}, limit=1):
        raise DuplicateDocumentError("Document already exists")
    return content_hash


def resolve_author_name(pdf_author: Optional[str]) -> str:
    if not pdf_author:
        return "Unknown"
    if "gov.uk/maib" in pdf_author.lower():
        return "MAIB"
    return pdf_author


def get_or_create_author(db: SupabaseService, name: str) -> dict:
    existing = db.get_records("authors", {"name": name}, limit=1)
    if existing:
        return existing[0]
    return db.create_record("authors", {"name": name})


def store_sentences(db: SupabaseService, full_text: str, doc_id: int) -> None:
    logger.info("Step 4: Splitting text into sentences...")
    all_sentences = split_into_sentences(full_text)
    logger.info("  Found %s sentences", len(all_sentences))
    logger.info("Step 5: Storing sentences...")
    db.create_records_batch("sentences", [
        {"text": s["text"], "text_type": s["text_type"], "position": i, "document_id": doc_id}
        for i, s in enumerate(all_sentences)
    ])
    logger.info("  Stored %s sentences", len(all_sentences))
