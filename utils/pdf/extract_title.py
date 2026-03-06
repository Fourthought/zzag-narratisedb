def extract_title(full_text: str) -> str:
    """Extract the report title from the cover page text."""
    lines = full_text.split("\n")
    title_candidates = []

    for i, line in enumerate(lines):
        line = line.strip()
        if i > 50:
            break
        if not line or line.isdigit() or len(line) < 10:
            continue
        if "marine accident investigation" in line.lower():
            continue
        if "report" in line.lower():
            title_candidates.append(line)

    if title_candidates:
        return title_candidates[0][:500]

    for line in lines[:30]:
        line = line.strip()
        if len(line) > 15 and len(line) < 200:
            return line[:500]

    return "Untitled Report"
