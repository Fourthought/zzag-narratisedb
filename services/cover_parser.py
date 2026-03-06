"""
Extract report metadata from unstructured cover page text using spaCy.

Used as a fallback for documents that don't have a structured Section 1.1 table
(i.e. non-MAIBInvReport formats).
"""
import re
from typing import Optional

from services.pdf_parser import ReportMetadata

# Vessel type words/phrases, ordered longest-first so compound types match before single words
VESSEL_TYPES = [
    "roll-on/roll-off cargo ship",
    "roll-on/roll-off ferry",
    "roll-on/roll-off vessel",
    "general cargo ship",
    "container ship",
    "bulk carrier",
    "motor cruiser",
    "motor vessel",
    "fishing vessel",
    "fishing boat",
    "survey vessel",
    "survey workboat",
    "passenger vessel",
    "passenger ferry",
    "rigid inflatable boat",
    "cargo ship",
    "cargo vessel",
    "workboat",
    "trawler",
    "tanker",
    "dredger",
    "barge",
    "tender",
    "cruiser",
    "tug",
    "ferry",
    "yacht",
]

SEVERITY_PATTERNS = [
    (r"(?i)very serious marine casualty", "Very Serious Marine Casualty"),
    (r"(?i)\bserious marine casualty\b", "Serious Marine Casualty"),
    (r"(?i)marine casualty", "Marine Casualty"),
]

_nlp = None


def _get_nlp():
    global _nlp
    if _nlp is None:
        import spacy
        _nlp = spacy.load("en_core_web_sm")
    return _nlp


def _find_vessel_type(text: str) -> Optional[str]:
    text_lower = text.lower()
    for vessel_type in VESSEL_TYPES:
        if vessel_type in text_lower:
            return vessel_type
    return None


def _find_vessel_name(doc, vessel_type: str) -> Optional[str]:
    """Find the vessel name — the proper noun that appears immediately after
    the vessel type phrase in the sentence."""
    text_lower = doc.text.lower()
    type_end = text_lower.find(vessel_type) + len(vessel_type)
    if type_end < 0:
        return None

    # Look for entities that start after the vessel type
    for ent in doc.ents:
        if ent.start_char >= type_end and ent.label_ in ("PERSON", "ORG", "GPE", "PRODUCT"):
            name = ent.text.strip()
            # Reject obviously wrong matches (single common words, prepositions)
            if len(name) > 1 and not name.lower() in ("the", "a", "an"):
                return name

    # Fallback: look for an ALL CAPS word after the type (common in older reports)
    remaining = doc.text[type_end:type_end + 60]
    m = re.search(r'\b([A-Z]{2}[A-Z\s]*[A-Z])\b', remaining)
    if m:
        return m.group(1).strip()

    return None


def _find_accident_date(doc) -> Optional[str]:
    """Find accident date — DATE entity whose root attaches via prep 'on'."""
    for ent in doc.ents:
        if ent.label_ == "DATE":
            head = ent.root.head
            if head.text.lower() == "on":
                return ent.text

    # Fallback: first DATE entity in the doc
    for ent in doc.ents:
        if ent.label_ == "DATE":
            return ent.text

    return None


def _find_location(doc) -> Optional[str]:
    """Find accident location — GPE/LOC/ORG entities attached via location prepositions.

    spaCy sometimes tags place names as ORG, so we check all three types.
    """
    LOCATION_PREPS = {"near", "at", "off", "in", "around", "to"}
    parts = []
    for ent in doc.ents:
        if ent.label_ in ("GPE", "LOC", "ORG"):
            head = ent.root.head
            if head.text.lower() in LOCATION_PREPS or head.dep_ == "appos":
                parts.append(ent.text)
    return ", ".join(parts) if parts else None


def _find_severity(text: str) -> Optional[str]:
    for pattern, label in SEVERITY_PATTERNS:
        if re.search(pattern, text):
            return label
    return None


def _find_loss_of_life(text: str) -> Optional[int]:
    """Extract loss of life count from text.

    Handles: "loss of three lives", "1 fatality", "two deaths", "fatal", etc.
    """
    NUMBER_WORDS = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    }

    # "loss of N lives" / "N fatalities" / "N deaths"
    patterns = [
        r"loss of (\w+) lives?",
        r"(\w+) (?:fatalities|fatality|deaths?|lives? (?:were )?lost)",
        r"(\d+) (?:people|persons?) (?:died|killed|lost)",
    ]
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            val = m.group(1).lower()
            if val.isdigit():
                return int(val)
            if val in NUMBER_WORDS:
                return NUMBER_WORDS[val]

    # "fatal" with no number implies 1
    if re.search(r"\bfatal\b", text, re.IGNORECASE):
        return 1

    return None


def extract_metadata_from_cover(cover_text: str) -> ReportMetadata:
    """Extract ReportMetadata from unstructured cover page text using spaCy."""
    nlp = _get_nlp()

    # Run NLP on the first meaningful sentence(s) — cover pages are short
    doc = nlp(cover_text[:1000])

    vessel_type = _find_vessel_type(cover_text)
    vessel_name = _find_vessel_name(doc, vessel_type) if vessel_type else None
    accident_date = _find_accident_date(doc)
    accident_location = _find_location(doc)
    severity = _find_severity(cover_text)
    loss_of_life = _find_loss_of_life(cover_text)

    return ReportMetadata(
        vessel_name=vessel_name,
        vessel_type=vessel_type,
        accident_date=accident_date,
        accident_location=accident_location,
        severity=severity,
        loss_of_life=str(loss_of_life) if loss_of_life else None,
    )
