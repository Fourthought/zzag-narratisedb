import re


def split_into_sentences(text: str) -> list[dict]:
    """Split text into sentences.

    Returns list of {"text": "...", "text_type": "paragraph|list_item|heading"}.

    text_type heuristics:
    - heading: matches SECTION X or subsection number pattern (e.g. 1.1, 2.3.1)
    - list_item: starts with bullet (-, *, ●) or numbered pattern (a., 1., i.)
    - paragraph: everything else, split into sentences by NLTK
    """
    blocks = _classify_lines(text)
    return _tokenize_blocks(blocks)


def _classify_lines(text: str) -> list[dict]:
    blocks = []
    current_paragraph = []
    current_list_item = None

    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped:
            if current_paragraph:
                blocks.append({"type": "paragraph", "text": " ".join(current_paragraph)})
                current_paragraph = []
            if current_list_item:
                blocks.append({"type": "list_item", "text": current_list_item})
                current_list_item = None
            continue

        text_type = "paragraph"

        if len(stripped) < 80:
            if re.match(r"^SECTION\s+\d+", stripped, re.IGNORECASE):
                text_type = "heading"
            elif re.match(r"^\d+\.\d+(\.\d+)?\s+", stripped):
                text_type = "heading"
            elif stripped == "SYNOPSIS":
                text_type = "heading"

        if text_type == "paragraph":
            if re.match(r"^[\-\*●]\s+", stripped):
                text_type = "list_item"
            elif re.match(r"^[a-zA-Z0-9][.\)]\s+", stripped):
                text_type = "list_item"
            elif re.match(r"^\([a-zA-Z0-9]\)\s+", stripped):
                text_type = "list_item"

        if text_type == "heading":
            if current_list_item:
                blocks.append({"type": "list_item", "text": current_list_item})
                current_list_item = None
            if current_paragraph:
                blocks.append({"type": "paragraph", "text": " ".join(current_paragraph)})
                current_paragraph = []
            blocks.append({"type": "heading", "text": stripped})

        elif text_type == "list_item":
            if current_paragraph:
                blocks.append({"type": "paragraph", "text": " ".join(current_paragraph)})
                current_paragraph = []
            if current_list_item:
                blocks.append({"type": "list_item", "text": current_list_item})
            current_list_item = stripped

        else:
            if current_list_item:
                list_ends_without_punct = not current_list_item.rstrip().endswith(('.', '!', '?'))
                line_starts_lowercase = stripped[0].islower()
                if list_ends_without_punct and line_starts_lowercase:
                    current_list_item += " " + stripped
                else:
                    blocks.append({"type": "list_item", "text": current_list_item})
                    current_list_item = None
                    current_paragraph.append(stripped)
            else:
                current_paragraph.append(stripped)

    if current_list_item:
        blocks.append({"type": "list_item", "text": current_list_item})
    if current_paragraph:
        blocks.append({"type": "paragraph", "text": " ".join(current_paragraph)})

    return blocks


def _tokenize_blocks(blocks: list[dict]) -> list[dict]:
    import nltk
    try:
        nltk.data.find("tokenizers/punkt_tab")
    except LookupError:
        nltk.download("punkt_tab", quiet=True)

    sentences = []
    position = 0

    for block in blocks:
        if block["type"] == "paragraph":
            for sent_text in nltk.sent_tokenize(block["text"]):
                sent_text = sent_text.strip()
                if sent_text:
                    sentences.append({"text": sent_text, "text_type": "paragraph", "position": position})
                    position += 1
        else:
            sentences.append({"text": block["text"], "text_type": block["type"], "position": position})
            position += 1

    return sentences
