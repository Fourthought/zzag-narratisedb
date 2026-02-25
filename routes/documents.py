from fastapi import APIRouter, File, UploadFile

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
