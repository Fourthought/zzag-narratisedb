from services.ingestion.shared import DuplicateDocumentError, UnsupportedDocumentError
from services.ingestion import pdf as pdf_ingestion
from services.ingestion import url as url_ingestion
from services.supabase.service import SupabaseService


class IngestionService:
    def __init__(self, supabase: SupabaseService):
        self.db = supabase

    def ingest(self, pdf_bytes: bytes, filename: str) -> dict:
        return pdf_ingestion.ingest(self.db, pdf_bytes, filename)

    def ingest_from_url(self, url: str) -> dict:
        return url_ingestion.ingest_from_url(self.db, url)
