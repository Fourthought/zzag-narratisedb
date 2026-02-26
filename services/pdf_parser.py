import io
import re
from typing import Optional
from datetime import datetime

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


def extract_full_text(pdf_bytes: bytes) -> str:
    """Extract all text from all pages, concatenated."""
    text_parts = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n\n".join(text_parts)


def extract_pdf_metadata(pdf_bytes: bytes) -> dict:
    """Extract PDF file metadata (author, creation date, pages, etc.)."""
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        metadata = {
            "page_count": len(pdf.pages),
            "pdf_title": None,
            "pdf_author": None,
            "pdf_subject": None,
            "pdf_creator": None,
            "pdf_producer": None,
            "pdf_creation_date": None,
            "pdf_mod_date": None,
        }

        if hasattr(pdf, 'metadata') and pdf.metadata:
            raw_metadata = pdf.metadata
            metadata["pdf_title"] = raw_metadata.get("Title")
            metadata["pdf_author"] = raw_metadata.get("Author")
            metadata["pdf_subject"] = raw_metadata.get("Subject")
            metadata["pdf_creator"] = raw_metadata.get("Creator")
            metadata["pdf_producer"] = raw_metadata.get("Producer")
            metadata["pdf_creation_date"] = raw_metadata.get("CreationDate")
            metadata["pdf_mod_date"] = raw_metadata.get("ModDate")

        return metadata


def extract_tables(pdf_bytes: bytes) -> list[list[list[str]]]:
    """Extract all tables from all pages using pdfplumber.extract_tables()."""
    all_tables = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            if tables:
                all_tables.extend(tables)
    return all_tables


def extract_metadata_from_tables(pdf_bytes: bytes) -> dict:
    """Parse Section 1.1 tables into a dict mapping to chirp_report_metadata fields.

    Keys: vessel_name, vessel_type, accident_date, accident_location,
    severity, loss_of_life, port_of_origin, destination, accident_type.
    """
    metadata = {
        "vessel_name": None,
        "vessel_type": None,
        "accident_date": None,
        "accident_location": None,
        "severity": None,
        "loss_of_life": None,
        "port_of_origin": None,
        "destination": None,
        "accident_type": None,
    }

    tables = extract_tables(pdf_bytes)

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

            if not key_cell or not value_cell or value_cell.lower() in ["", "none", "n/a", "-"]:
                continue

            for metadata_key, pattern in key_patterns.items():
                if re.match(pattern, key_cell) and not metadata[metadata_key]:
                    metadata[metadata_key] = value_cell
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
    iso_matches = re.findall(iso_pattern, full_text[:500])
    if iso_matches:
        return iso_matches[0]

    # Pattern for month year (e.g., "September 2023", "OCTOBER 2025")
    month_year_pattern = r"\b([A-Za-z]+)\s+(\d{4})\b"
    matches = re.findall(month_year_pattern, full_text[:500])

    for month_name, year in matches:
        month_lower = month_name.lower()
        if month_lower in MONTH_MAP:
            month_num = MONTH_MAP[month_lower]
            # Use first day of the month since we don't have the day
            return f"{year}-{month_num:02d}-01"

    return None


def split_into_sections(full_text: str) -> list[dict]:
    """Split text at section boundaries. Returns list of
    {"name": "SYNOPSIS", "text": "...", "position": 0}.

    Section patterns (regex, case-insensitive):
    - SYNOPSIS
    - SECTION \\d+ [–-] .+
    - GLOSSARY OF ABBREVIATIONS AND ACRONYMS

    Note: TOC entries (lines ending with page numbers) are skipped and not treated as section boundaries.
    """

    def is_toc_entry(text: str) -> bool:
        """Check if text looks like a TOC entry (short text ending with page number)."""
        if len(text) > 150:
            return False
        # Ends with page number pattern (1-3 digits, possibly with a letter like 18a)
        toc_pattern = r"\s\d{1,3}[a-z]?\s*$"
        if not re.search(toc_pattern, text):
            return False
        # Must have some text before the page number
        text_before_page = re.sub(toc_pattern, "", text).strip()
        if len(text_before_page) < 3:
            return False
        # Exclude figure captions (they start with "Figure")
        if text.lower().startswith("figure"):
            return False
        return True

    sections = []

    # Section patterns with their names
    synopsis_pattern = r"^SYNOPSIS\s*$"
    section_pattern = r"^SECTION\s+(\d+)\s*[–-]\s+(.+?)\s*$"
    glossary_pattern = r"^GLOSSARY OF ABBREVIATIONS AND ACRONYMS\s*$"
    conclusions_pattern = r"^CONCLUSIONS\s*$"
    recommendations_pattern = r"^RECOMMENDATIONS\s*$"

    lines = full_text.split("\n")
    current_section = None
    current_text = []
    position = 0

    for line in lines:
        line = line.rstrip()
        stripped = line.strip()

        # Skip TOC entries - don't treat them as section boundaries
        if is_toc_entry(stripped):
            # Add to current section text, but don't start a new section
            current_text.append(line)
            continue

        # Check for section boundaries
        section_match = re.match(section_pattern, stripped, re.IGNORECASE)
        if section_match:
            # Save previous section
            if current_section:
                sections.append({
                    "name": current_section,
                    "text": "\n".join(current_text).strip(),
                    "position": position
                })
                position += 1

            current_section = section_match.group(2).strip()
            current_text = []
            continue

        if re.match(synopsis_pattern, stripped, re.IGNORECASE):
            if current_section:
                sections.append({
                    "name": current_section,
                    "text": "\n".join(current_text).strip(),
                    "position": position
                })
                position += 1

            current_section = "SYNOPSIS"
            current_text = []
            continue

        if re.match(glossary_pattern, stripped, re.IGNORECASE):
            if current_section:
                sections.append({
                    "name": current_section,
                    "text": "\n".join(current_text).strip(),
                    "position": position
                })
                position += 1

            current_section = "GLOSSARY"
            current_text = []
            continue

        if re.match(conclusions_pattern, stripped, re.IGNORECASE):
            if current_section:
                sections.append({
                    "name": current_section,
                    "text": "\n".join(current_text).strip(),
                    "position": position
                })
                position += 1

            current_section = "CONCLUSIONS"
            current_text = []
            continue

        if re.match(recommendations_pattern, stripped, re.IGNORECASE):
            if current_section:
                sections.append({
                    "name": current_section,
                    "text": "\n".join(current_text).strip(),
                    "position": position
                })
                position += 1

            current_section = "RECOMMENDATIONS"
            current_text = []
            continue

        # Add line to current section
        current_text.append(line)

    # Save last section
    if current_section:
        sections.append({
            "name": current_section,
            "text": "\n".join(current_text).strip(),
            "position": position
        })

    return sections


def split_into_sentences(text: str) -> list[dict]:
    """Split section text into sentences using nltk.sent_tokenize.
    Returns list of {"text": "...", "text_type": "paragraph|list_item|heading", "position": 0, "relevance_score": int|None}.

    text_type heuristics:
    - heading: short line (< 80 chars) that is all caps or matches subsection pattern (e.g. "2.3.1 ...")
    - list_item: starts with bullet (-, *, ●) or numbered pattern (a., 1., i.)
    - paragraph: everything else

    relevance_score heuristics:
    - 0: TOC entries (short text ending with page number)
    - None: not yet scored (default)

    Note: PDFs don't have paragraph structure - text is extracted as visual lines.
    This function reconstructs paragraphs by joining consecutive non-heading, non-list lines,
    then splits the reconstructed paragraphs into sentences using NLTK.
    """
    import nltk

    # Download NLTK data if needed
    try:
        nltk.data.find("tokenizers/punkt_tab")
    except LookupError:
        nltk.download("punkt_tab", quiet=True)

    def is_toc_entry(text: str) -> bool:
        """Check if text looks like a TOC entry (ends with page number)."""
        # TOC entries are typically short and end with a page number
        # Pattern: text ending with 1-3 digit number (page number)
        # Exclude pure numbers and common non-TOC patterns
        if len(text) > 150:
            return False
        # Ends with page number pattern (1-3 digits, possibly with a letter like 18a)
        toc_pattern = r"\s\d{1,3}[a-z]?\s*$"
        if not re.search(toc_pattern, text):
            return False
        # Must have some text before the page number
        text_before_page = re.sub(toc_pattern, "", text).strip()
        if len(text_before_page) < 3:
            return False
        # Exclude figure captions (they start with "Figure")
        if text.lower().startswith("figure"):
            return False
        return True

    sentences = []
    lines = text.split("\n")
    position = 0

    # First pass: classify each line and group into blocks
    # A "block" is either a standalone heading/list_item, or a reconstructed paragraph
    blocks = []
    current_paragraph = []
    current_list_item = None  # Track multi-line list items

    for line in lines:
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

    # Second pass: split paragraph blocks into sentences using NLTK
    for block in blocks:
        if block["type"] == "paragraph":
            # Use NLTK to split the paragraph into actual sentences
            sent_texts = nltk.sent_tokenize(block["text"])
            for sent_text in sent_texts:
                sent_text = sent_text.strip()
                if sent_text:
                    relevance = 0 if is_toc_entry(sent_text) else None
                    sentences.append({
                        "text": sent_text,
                        "text_type": "paragraph",
                        "position": position,
                        "relevance_score": relevance,
                    })
                    position += 1
        else:
            # heading and list_item stay as-is
            relevance = 0 if is_toc_entry(block["text"]) else None
            sentences.append({
                "text": block["text"],
                "text_type": block["type"],
                "position": position,
                "relevance_score": relevance,
            })
            position += 1

    # Third pass: mark TOC based on duplicate headings
    # Find first duplicate heading - everything before it is TOC
    seen_headings = {}
    first_duplicate_position = None

    for sent in sentences:
        if sent["text_type"] == "heading":
            heading_text = sent["text"]
            if heading_text in seen_headings:
                # Found duplicate - this is where real content starts
                first_duplicate_position = sent["position"]
                break
            seen_headings[heading_text] = sent["position"]

    # Mark all sentences before the first duplicate as relevance 0 (TOC)
    if first_duplicate_position is not None:
        for sent in sentences:
            if sent["position"] < first_duplicate_position:
                sent["relevance_score"] = 0

    return sentences


def extract_safety_issues(conclusions_text: str) -> list[str]:
    """Parse numbered safety issues from Section 3 text."""
    issues = []
    lines = conclusions_text.split("\n")

    # Look for numbered safety issues
    # Pattern: "1.1", "1.2", etc. or "Safety issue 1:", etc.
    current_issue = None
    issue_pattern = r"^(\d+\.\d+)\s+(.+)$"

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        match = re.match(issue_pattern, stripped)
        if match:
            if current_issue:
                issues.append(current_issue.strip())
            current_issue = match.group(2)
        elif current_issue:
            # Continuation of current issue
            current_issue += " " + stripped

    if current_issue:
        issues.append(current_issue.strip())

    # Alternative: look for "safety issue" keyword
    if not issues:
        safety_issue_pattern = r"(?i)safety\s+issue\s*\d+[:\.\-]\s*(.+?)(?=\n|$|\s*safety\s+issue)"
        matches = re.findall(safety_issue_pattern, conclusions_text)
        issues = [m.strip() for m in matches if m.strip()]

    return issues


def extract_recommendations(recommendations_text: str) -> list[dict]:
    """Parse recommendations from Section 5 text.
    Returns list of {"reference_code": "2025/147", "text": "...", "organisation": "Org Name"}.
    """
    recommendations = []

    # Pattern for MAIB recommendations: YYYY/NNN
    ref_code_pattern = r"(\d{4}/\d+)"

    lines = recommendations_text.split("\n")
    current_rec = None

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Look for reference code
        ref_match = re.search(ref_code_pattern, stripped)
        if ref_match:
            # Save previous recommendation
            if current_rec and current_rec.get("text"):
                recommendations.append(current_rec)

            current_rec = {
                "reference_code": ref_match.group(1),
                "text": stripped,
                "organisation": None
            }
        elif current_rec:
            # Continuation of current recommendation
            current_rec["text"] += " " + stripped

            # Try to extract organisation (common patterns)
            org_patterns = [
                r"(?i)to\s+([A-Z][A-Za-z\s&]+?)(?:\s+(?:to|recommend|ensure|consider|review)|$)",
                r"(?i)(?:recommend|addressed)\s+to\s+([A-Z][A-Za-z\s&]+?)(?:\s+(?:to|recommend|ensure)|$)",
            ]
            for pattern in org_patterns:
                org_match = re.search(pattern, stripped)
                if org_match and not current_rec["organisation"]:
                    org_name = org_match.group(1).strip()
                    if len(org_name) > 2 and len(org_name) < 100:
                        current_rec["organisation"] = org_name
                        break

    if current_rec and current_rec.get("text"):
        recommendations.append(current_rec)

    return recommendations
