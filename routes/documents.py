from fastapi import APIRouter, File, UploadFile, Response
from fastapi.responses import PlainTextResponse

from services.ingestion import IngestionService
from services.supabase.client import get_supabase
from services.supabase.service import SupabaseService

router = APIRouter(prefix="/documents")


@router.post("")
async def create_document(file: UploadFile = File(...)):
    """Upload and ingest a PDF document into the database.

    Accepts a PDF file (MAIB report), parses it into structured data,
    and stores it across multiple database tables.

    Returns the created document record.

    Raises 409 if a document with the same content already exists.
    """
    pdf_bytes = await file.read()
    client = get_supabase()
    service = IngestionService(SupabaseService(client))
    document = service.ingest(pdf_bytes, file.filename)
    return document


@router.get("/{id}/full", response_class=PlainTextResponse)
async def get_document_full(id: int, min_relevance: int | None = None):
    """Reconstructed document — all sentences ordered by position.

    Query params:
    - min_relevance: Filter out sentences with relevance_score below this value (0-10)
                     0 = TOC/metadata, None = include all
    """
    client = get_supabase()

    # Build query with optional relevance filter
    query = (
        client.table("sentences")
        .select("text, text_type, sections(name, position)")
        .eq("document_id", id)
        .order("section_id")
        .order("position")
    )

    if min_relevance is not None:
        # Filter: relevance_score >= min_relevance OR relevance_score IS NULL (not yet scored)
        query = query.or_(f"relevance_score.gte.{min_relevance},relevance_score.is.null")

    sentences_result = query.execute()

    # Reconstruct as plain text with proper formatting
    lines = []
    for sent in sentences_result.data:
        text = sent["text"]
        text_type = sent["text_type"]

        # Add blank line before headings
        if text_type == "heading":
            lines.append("")
            lines.append(text)
        else:
            lines.append(text)

    return "\n".join(lines).strip()


@router.get("/{id}/full.json")
async def get_document_full_json(id: int, min_relevance: int | None = None):
    """Reconstructed document as JSON — sentences with metadata."""
    client = get_supabase()

    # Get document with author
    doc_result = (
        client.table("documents")
        .select("*, authors(*)")
        .eq("id", id)
        .single()
        .execute()
    )
    document = doc_result.data

    # Build query with optional relevance filter
    query = (
        client.table("sentences")
        .select("*, sections(name, position)")
        .eq("document_id", id)
        .order("section_id")
        .order("position")
    )

    if min_relevance is not None:
        query = query.or_(f"relevance_score.gte.{min_relevance},relevance_score.is.null")

    sentences_result = query.execute()

    return {
        **document,
        "sentences": sentences_result.data,
    }
