import re
from typing import Optional

from utils.pdf._constants import MONTH_MAP


def parse_accident_date(raw: str) -> Optional[str]:
    """Parse accident date string to ISO YYYY-MM-DD, or None if unparseable.

    Handles formats like "28 September 2023 at 0936", "28 Sep 2023", etc.
    """
    if not raw:
        return None
    m = re.search(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", raw)
    if m:
        day, month_name, year = m.group(1), m.group(2), m.group(3)
        month_num = MONTH_MAP.get(month_name.lower())
        if month_num:
            return f"{year}-{month_num:02d}-{int(day):02d}"
    return None
