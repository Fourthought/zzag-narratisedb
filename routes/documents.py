from fastapi import APIRouter, File, UploadFile, HTTPException

from services.ingestion import IngestionService, DuplicateDocumentError, UnsupportedDocumentError
from services.supabase.client import get_supabase
from services.supabase.service import SupabaseService

router = APIRouter(prefix="/documents")


@router.post("")
def create_document(file: UploadFile = File(...)):
    """Upload and ingest a PDF document into the database.

    Accepts a PDF file (MAIB report), parses it into structured data,
    and stores it across multiple database tables.

    Returns the created document record.

    Raises 409 if a document with the same content already exists.
    Raises 422 if the document type is not supported.
    """
    pdf_bytes = file.file.read()
    client = get_supabase()
    service = IngestionService(SupabaseService(client))
    try:
        document = service.ingest(pdf_bytes, file.filename)
        return document
    except DuplicateDocumentError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except UnsupportedDocumentError as e:
        raise HTTPException(status_code=422, detail=str(e))
