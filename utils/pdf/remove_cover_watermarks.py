import re

_WATERMARK_PATTERNS = (
    r"TTRROOPPEERR\s+TTNNEEDDIICCCCAA",
    r"AACCCCIIDDEENNTT\s+RREEPPOORRTT",
    r"IINNTTEERRIIMM\s+RREEPPOORRTT",
)


def remove_cover_watermarks(text: str) -> str:
    """Strip known doubled-character cover page watermarks from text."""
    for pattern in _WATERMARK_PATTERNS:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)
    return text
