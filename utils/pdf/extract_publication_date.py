import re
from typing import Optional

from utils.pdf._constants import MONTH_MAP, COVER_PAGE_CHAR_LIMIT


def extract_publication_date(full_text: str) -> Optional[str]:
    """Extract publication date from cover page (e.g. 'OCTOBER 2025').
    Returns ISO date string YYYY-MM-DD or None.
    """
    iso_pattern = r"\b(\d{4}-\d{2}-\d{2})\b"
    iso_matches = re.findall(iso_pattern, full_text[:COVER_PAGE_CHAR_LIMIT])
    if iso_matches:
        return iso_matches[0]

    # Take the LAST valid month-year match — publication date appears at the
    # bottom of the cover page, while narrative dates appear earlier.
    month_year_pattern = r"\b([A-Za-z]+)\s+(\d{4})\b"
    matches = re.findall(month_year_pattern, full_text[:COVER_PAGE_CHAR_LIMIT])

    result = None
    for month_name, year in matches:
        month_num = MONTH_MAP.get(month_name.lower())
        if month_num:
            result = f"{year}-{month_num:02d}-01"

    return result
