import io
import re
from dataclasses import dataclass
from typing import Optional

import pdfplumber

# Month name to number mapping
MONTH_MAP = {
    "january": 1, "jan": 1,
    "february": 2, "feb": 2,
    "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "may": 5,
    "june": 6, "jun": 6,
    "july": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sep": 9, "sept": 9,
    "october": 10, "oct": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12,
}

# Constants
COVER_PAGE_CHAR_LIMIT = 500


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
    """Metadata extracted from Section 1.1 tables."""
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


def _extract_full_text(pdf: pdfplumber.PDF) -> str:
    """Extract all text from all pages, concatenated."""
    text_parts = []
    for page in pdf.pages:
        page_text = page.extract_text()
        if page_text:
            text_parts.append(page_text)
    return "\n\n".join(text_parts)


def _extract_metadata(pdf: pdfplumber.PDF) -> PdfMetadata:
    """Extract PDF file metadata."""
    metadata = PdfMetadata(page_count=len(pdf.pages))

    if hasattr(pdf, 'metadata') and pdf.metadata:
        raw_metadata = pdf.metadata
        metadata.pdf_title = raw_metadata.get("Title")
        metadata.pdf_author = raw_metadata.get("Author")
        metadata.pdf_subject = raw_metadata.get("Subject")
        metadata.pdf_creator = raw_metadata.get("Creator")
        metadata.pdf_producer = raw_metadata.get("Producer")
        metadata.pdf_creation_date = raw_metadata.get("CreationDate")
        metadata.pdf_mod_date = raw_metadata.get("ModDate")

    return metadata


def _extract_tables(pdf: pdfplumber.PDF) -> list[list[list[str]]]:
    """Extract all tables from all pages using pdfplumber.extract_tables()."""
    all_tables = []
    for page in pdf.pages:
        tables = page.extract_tables()
        if tables:
            all_tables.extend(tables)
    return all_tables


def parse_pdf(pdf_bytes: bytes) -> ParsedPDF:
    """Parse PDF and extract all data in a single pass."""
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        full_text = _extract_full_text(pdf)
        metadata = _extract_metadata(pdf)
        tables = _extract_tables(pdf)

    report_metadata = _parse_metadata_from_tables(tables)
    return ParsedPDF(
        full_text=full_text,
        metadata=metadata,
        report_metadata=report_metadata,
    )


def _parse_metadata_from_tables(tables: list[list[list[str]]]) -> ReportMetadata:
    """Parse Section 1.1 tables into ReportMetadata."""
    metadata = ReportMetadata()

    # Look for key-value pairs in tables
    key_patterns = {
        "vessel_name": r"(?i)vessel.*name|name.*vessel",
        "vessel_type": r"(?i)vessel.*type|type.*vessel",
        "accident_date": r"(?i)date.*accident|accident.*date",
        "accident_location": r"(?i)location|where",
        "severity": r"(?i)severity|serious",
        "loss_of_life": r"(?i)loss.*life|fatalities|casualties",
        "port_of_origin": r"(?i)port.*origin|departure.*port|from",
        "destination": r"(?i)destination|to\b",
        "accident_type": r"(?i)accident.*type|type.*accident|incident.*type",
    }

    for table in tables:
        for row in table:
            if not row or len(row) < 2:
                continue
            key_cell = str(row[0]).strip() if row[0] else ""
            value_cell = str(row[1]).strip() if row[1] else ""

            if not key_cell or not value_cell or value_cell.lower() in ["none", "n/a", "-"]:
                continue

            for metadata_key, pattern in key_patterns.items():
                if re.match(pattern, key_cell):
                    current_value = getattr(metadata, metadata_key)
                    if not current_value:
                        setattr(metadata, metadata_key, value_cell)
                    break

    return metadata


def extract_title(full_text: str) -> str:
    """Extract the report title from the cover page text."""
    lines = full_text.split("\n")
    title_candidates = []

    for i, line in enumerate(lines):
        line = line.strip()
        # Title is typically on first page, early in document
        if i > 50:
            break
        # Skip empty lines, page numbers, and common headers
        if not line or line.isdigit() or len(line) < 10:
            continue
        if "marine accident investigation" in line.lower():
            continue
        if "report" in line.lower():
            title_candidates.append(line)

    # Return the first substantial title candidate
    if title_candidates:
        return title_candidates[0][:500]

    # Fallback: first non-empty line that looks like a title
    for line in lines[:30]:
        line = line.strip()
        if len(line) > 15 and len(line) < 200:
            return line[:500]

    return "Untitled Report"


def extract_publication_date(full_text: str) -> Optional[str]:
    """Extract publication date from cover page (e.g. 'OCTOBER 2025').
    Returns ISO date format YYYY-MM-DD or None.
    """
    # Try ISO date format first
    iso_pattern = r"\b(\d{4}-\d{2}-\d{2})\b"
    iso_matches = re.findall(iso_pattern, full_text[:COVER_PAGE_CHAR_LIMIT])
    if iso_matches:
        return iso_matches[0]

    # Pattern for month year (e.g., "September 2023", "OCTOBER 2025")
    month_year_pattern = r"\b([A-Za-z]+)\s+(\d{4})\b"
    matches = re.findall(month_year_pattern, full_text[:COVER_PAGE_CHAR_LIMIT])

    for month_name, year in matches:
        month_lower = month_name.lower()
        if month_lower in MONTH_MAP:
            month_num = MONTH_MAP[month_lower]
            # Use first day of the month since we don't have the day
            return f"{year}-{month_num:02d}-01"

    return None


def _classify_lines(text: str) -> list[dict]:
    """Classify each line and group into blocks.

    Returns a list of {"type": "paragraph|list_item|heading", "text": "..."}.
    """
    blocks = []
    current_paragraph = []
    current_list_item = None

    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped:
            # Empty line ends current paragraph and any ongoing list item
            if current_paragraph:
                blocks.append({"type": "paragraph", "text": " ".join(current_paragraph)})
                current_paragraph = []
            if current_list_item:
                blocks.append({"type": "list_item", "text": current_list_item})
                current_list_item = None
            continue

        text_type = "paragraph"

        # Check for heading (explicit patterns only)
        if len(stripped) < 80:
            # SECTION X pattern (e.g., "SECTION 1 - FACTUAL INFORMATION")
            if re.match(r"^SECTION\s+\d+", stripped, re.IGNORECASE):
                text_type = "heading"
            # Subsection pattern (e.g., "1.1", "1.2.3", "2.3.1")
            elif re.match(r"^\d+\.\d+(\.\d+)?\s+", stripped):
                text_type = "heading"
            # SYNOPSIS (explicit heading)
            elif stripped == "SYNOPSIS":
                text_type = "heading"

        # Check for list item (only if not already a heading)
        if text_type == "paragraph":
            # Bullet points (including unicode bullet ●)
            if re.match(r"^[\-\*●]\s+", stripped):
                text_type = "list_item"
            # Numbered patterns
            elif re.match(r"^[a-zA-Z0-9][.\)]\s+", stripped):
                text_type = "list_item"
            elif re.match(r"^\([a-zA-Z0-9]\)\s+", stripped):
                text_type = "list_item"

        # Handle based on type
        if text_type == "heading":
            # Save any pending accumulations first
            if current_list_item:
                blocks.append({"type": "list_item", "text": current_list_item})
                current_list_item = None
            if current_paragraph:
                blocks.append({"type": "paragraph", "text": " ".join(current_paragraph)})
                current_paragraph = []
            # Add heading as standalone block
            blocks.append({"type": "heading", "text": stripped})

        elif text_type == "list_item":
            # Save any pending paragraph first
            if current_paragraph:
                blocks.append({"type": "paragraph", "text": " ".join(current_paragraph)})
                current_paragraph = []
            # If there's an ongoing list item, save it first
            if current_list_item:
                blocks.append({"type": "list_item", "text": current_list_item})
            # Start new list item
            current_list_item = stripped

        else:
            # Paragraph text - could be continuation of list item or start of paragraph
            if current_list_item:
                # Check if this is a continuation of the list item
                # Continuation: previous list item doesn't end with punctuation AND this line starts lowercase
                list_ends_without_punct = not current_list_item.rstrip().endswith(('.', '!', '?'))
                line_starts_lowercase = stripped[0].islower()
                if list_ends_without_punct and line_starts_lowercase:
                    # Continuation of multi-line list item
                    current_list_item += " " + stripped
                else:
                    # End the list item, start a new paragraph
                    blocks.append({"type": "list_item", "text": current_list_item})
                    current_list_item = None
                    current_paragraph.append(stripped)
            else:
                # Accumulate paragraph text
                if current_paragraph:
                    last_line = current_paragraph[-1]
                    # If previous line ends with a period and this line starts with uppercase,
                    # it might be a new sentence in the same paragraph
                    if last_line.endswith(('.', '!', '?', '"', "'")) and stripped[0].isupper():
                        pass  # Still part of paragraph, just a new sentence
                    current_paragraph.append(stripped)
                else:
                    current_paragraph.append(stripped)

    # Save any remaining accumulations
    if current_list_item:
        blocks.append({"type": "list_item", "text": current_list_item})
    if current_paragraph:
        blocks.append({"type": "paragraph", "text": " ".join(current_paragraph)})

    return blocks


def _tokenize_blocks(blocks: list[dict]) -> list[dict]:
    """Split paragraph blocks into sentences using NLTK.

    Returns a list of sentence dicts with text, text_type, position.
    """
    import nltk

    # Download NLTK data if needed
    try:
        nltk.data.find("tokenizers/punkt_tab")
    except LookupError:
        nltk.download("punkt_tab", quiet=True)

    sentences = []
    position = 0

    for block in blocks:
        if block["type"] == "paragraph":
            # Use NLTK to split the paragraph into actual sentences
            sent_texts = nltk.sent_tokenize(block["text"])
            for sent_text in sent_texts:
                sent_text = sent_text.strip()
                if sent_text:
                    sentences.append({
                        "text": sent_text,
                        "text_type": "paragraph",
                        "position": position,
                    })
                    position += 1
        else:
            # heading and list_item stay as-is
            sentences.append({
                "text": block["text"],
                "text_type": block["type"],
                "position": position,
            })
            position += 1

    return sentences


def split_into_sentences(text: str) -> list[dict]:
    """Split text into sentences using nltk.sent_tokenize.
    Returns list of {"text": "...", "text_type": "paragraph|list_item|heading", "position": 0}.

    text_type heuristics:
    - heading: short line (< 80 chars) that matches section/subsection pattern
    - list_item: starts with bullet (-, *, ●) or numbered pattern (a., 1., i.)
    - paragraph: everything else
    """
    blocks = _classify_lines(text)
    sentences = _tokenize_blocks(blocks)
    return sentences
