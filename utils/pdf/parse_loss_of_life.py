import re
from typing import Optional


def parse_loss_of_life(raw: str) -> Optional[int]:
    """Parse loss-of-life string to integer, or None if unparseable.

    Handles formats like "1 fatality", "2 fatalities", "None", "3".
    """
    if not raw:
        return None
    m = re.search(r"\d+", raw)
    if m:
        return int(m.group())
    return None
