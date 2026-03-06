import httpx
from fastapi import APIRouter, File, UploadFile, HTTPException
from pydantic import BaseModel

from services.ingestion import IngestionService, DuplicateDocumentError, UnsupportedDocumentError
from services.supabase.client import get_supabase
from services.supabase.service import SupabaseService

router = APIRouter(prefix="/documents")


def _get_service() -> IngestionService:
    return IngestionService(SupabaseService(get_supabase()))


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
    try:
        return _get_service().ingest(pdf_bytes, file.filename)
    except DuplicateDocumentError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except UnsupportedDocumentError as e:
        raise HTTPException(status_code=422, detail=str(e))


class FromUrlRequest(BaseModel):
    url: str


@router.post("/from-url")
def create_document_from_url(body: FromUrlRequest):
    """Scrape a GOV.UK MAIB report page and ingest the PDF.

    Fetches the page, extracts structured metadata and the PDF URL,
    downloads the PDF, and runs the full ingestion pipeline.
    Web-scraped metadata takes precedence over PDF-extracted values.

    Returns the created document record.

    Raises 404 if the GOV.UK page is not found.
    Raises 409 if the document already exists.
    Raises 422 if no PDF attachment is found on the page.
    Raises 502 on other network or upstream errors.
    """
    try:
        return _get_service().ingest_from_url(body.url)
    except DuplicateDocumentError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="MAIB report page not found")
        raise HTTPException(status_code=502, detail=f"Upstream error: {e.response.status_code}")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Network error: {e}")
