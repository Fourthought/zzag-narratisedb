_WATERMARKS = (
    "TTRROOPPEERR TTNNEEDDIICCCCAA",
    "AACCCCIIDDEENNTT RREEPPOORRTT",
    "IINNTTEERRIIMM RREEPPOORRTT",
)


def remove_cover_watermarks(text: str) -> str:
    """Strip known doubled-character cover page watermarks from text."""
    for watermark in _WATERMARKS:
        text = text.replace(watermark, "")
    return text
