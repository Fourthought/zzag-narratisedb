"""Parse a PDF into structured data. No DB knowledge."""
import io
import re

import pdfplumber

from models.pdf import ParsedPDF, PdfMetadata, ReportMetadata


def parse_pdf(pdf_bytes: bytes) -> ParsedPDF:
    """Parse PDF and extract all data in a single pass."""
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        full_text = _extract_full_text(pdf)
        metadata = _extract_metadata(pdf)
        tables = _extract_tables(pdf)

    report_metadata = _parse_metadata_from_tables(tables)
    return ParsedPDF(full_text=full_text, metadata=metadata, report_metadata=report_metadata)


def _extract_full_text(pdf: pdfplumber.PDF) -> str:
    text_parts = []
    for page in pdf.pages:
        page_text = page.extract_text()
        if page_text:
            text_parts.append(page_text)

    if not text_parts:
        return ""

    result = text_parts[0]
    for part in text_parts[1:]:
        last_char = result.rstrip()[-1] if result.rstrip() else ""
        separator = "\n\n" if last_char in ".!?" else "\n"
        result += separator + part

    return result


def _extract_metadata(pdf: pdfplumber.PDF) -> PdfMetadata:
    metadata = PdfMetadata(page_count=len(pdf.pages))
    if hasattr(pdf, "metadata") and pdf.metadata:
        raw = pdf.metadata
        metadata.pdf_title = raw.get("Title")
        metadata.pdf_author = raw.get("Author")
        metadata.pdf_subject = raw.get("Subject")
        metadata.pdf_creator = raw.get("Creator")
        metadata.pdf_producer = raw.get("Producer")
        metadata.pdf_creation_date = raw.get("CreationDate")
        metadata.pdf_mod_date = raw.get("ModDate")
    return metadata


def _extract_tables(pdf: pdfplumber.PDF) -> list[list[list[str]]]:
    all_tables = []
    for page in pdf.pages:
        tables = page.extract_tables()
        if tables:
            all_tables.extend(tables)
    return all_tables


def _parse_metadata_from_tables(tables: list[list[list[str]]]) -> ReportMetadata:
    metadata = ReportMetadata()
    key_patterns = {
        "vessel_name": r"(?i)vessel.{0,5}name",
        "vessel_type": r"(?i)^type$",
        "accident_date": r"(?i)date.*time",
        "accident_location": r"(?i)location.*incident|location.*accident",
        "severity": r"(?i)type.*casualty|type.*marine|type.*incident",
        "loss_of_life": r"(?i)injur|fatal|casualt",
        "port_of_origin": r"(?i)port.*departure|port.*origin",
        "destination": r"(?i)port.*arrival",
        "accident_type": r"(?i)type.*voyage|voyage.*type",
    }

    for table in tables:
        for row in table:
            if not row or len(row) < 2:
                continue
            key_cell = str(row[0]).strip() if row[0] else ""
            value_cell = str(row[1]).strip() if row[1] else ""
            if not key_cell or not value_cell or value_cell.lower() in ["none", "n/a", "-", "not applicable"]:
                continue
            for field, pattern in key_patterns.items():
                if re.search(pattern, key_cell):
                    if not getattr(metadata, field):
                        setattr(metadata, field, value_cell)
                    break

    return metadata
