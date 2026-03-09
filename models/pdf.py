from dataclasses import dataclass
from typing import Optional


@dataclass
class PdfMetadata:
    """PDF file metadata."""
    page_count: int
    pdf_title: Optional[str] = None
    pdf_author: Optional[str] = None
    pdf_subject: Optional[str] = None
    pdf_creator: Optional[str] = None
    pdf_producer: Optional[str] = None
    pdf_creation_date: Optional[str] = None
    pdf_mod_date: Optional[str] = None


@dataclass
class ReportMetadata:
    """Metadata extracted from structured tables in the PDF."""
    vessel_name: Optional[str] = None
    vessel_type: Optional[str] = None
    accident_date: Optional[str] = None
    accident_location: Optional[str] = None
    severity: Optional[str] = None
    loss_of_life: Optional[str] = None
    port_of_origin: Optional[str] = None
    destination: Optional[str] = None
    accident_type: Optional[str] = None


@dataclass
class ParsedPDF:
    """Combined output from parsing a PDF."""
    full_text: str
    metadata: PdfMetadata
    report_metadata: ReportMetadata
