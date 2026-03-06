import httpx
from fastapi import APIRouter, File, UploadFile, HTTPException
from pydantic import BaseModel

from controllers import pdf as pdf_controller
from controllers import url as url_controller
from services.ingest_to_db import DuplicateDocumentError
from services.supabase.client import get_supabase
from services.supabase.service import SupabaseService

router = APIRouter(prefix="/documents")


def _get_db() -> SupabaseService:
    return SupabaseService(get_supabase())


@router.post("/pdf")
def ingest_pdf(file: UploadFile = File(...)):
    """Upload and ingest a PDF document.

    Returns the created document record.
    Raises 409 if the document already exists.
    """
    try:
        return pdf_controller.ingest_pdf(_get_db(), file.file.read(), file.filename)
    except DuplicateDocumentError as e:
        raise HTTPException(status_code=409, detail=str(e))


class FromUrlRequest(BaseModel):
    url: str


@router.post("/url")
def ingest_from_url(body: FromUrlRequest):
    """Scrape a GOV.UK MAIB report page and ingest the PDF.

    Returns the created document record.
    Raises 404 if the GOV.UK page is not found.
    Raises 409 if the document already exists.
    Raises 422 if no PDF attachment is found on the page.
    Raises 502 on other network or upstream errors.
    """
    try:
        return url_controller.ingest_from_url(_get_db(), body.url)
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
