import re

import spacy

from utils.pdf.remove_cover_watermarks import remove_cover_watermarks

_nlp = spacy.load("en_core_web_sm", exclude=["tagger", "attribute_ruler", "lemmatizer", "ner"])

# Sentence-initial patterns that indicate a false split by the parser
_FALSE_SPLIT_PATTERNS = (
    re.compile(r"^\d+/\d{4}"),        # report numbers: "17/2024"
    re.compile(r"^NO\s+\d+/\d{4}"),  # report number with prefix: "NO 17/2024 NOVEMBER 2024"
    re.compile(r"^\d{4}$"),            # standalone years: "2024"
)


def split_into_sentences(text: str) -> list[dict]:
    """Split text into sentences.

    Returns list of {"text": "...", "text_type": "paragraph|list_item|heading|footnote"}.

    text_type heuristics:
    - heading: matches SECTION X or subsection number pattern (e.g. 1.1, 2.3.1)
    - list_item: starts with bullet (-, *, ●) or numbered pattern (a., 1., i.)
    - footnote: starts with 1-2 digit number followed by uppercase text (inline footnote reference)
    - paragraph: everything else, split into sentences by spaCy dependency parser
    """
    text = remove_cover_watermarks(text)
    blocks = _classify_lines(text)
    return _tokenize_blocks(blocks)


def _classify_lines(text: str) -> list[dict]:
    blocks = []
    current_paragraph = []
    current_list_item = None

    for line in text.split("\n"):
        stripped = remove_cover_watermarks(line.strip()).strip()
        if not stripped:
            if current_paragraph:
                blocks.append({"type": "paragraph", "text": " ".join(current_paragraph)})
                current_paragraph = []
            if current_list_item:
                blocks.append({"type": "list_item", "text": current_list_item})
                current_list_item = None
            continue

        if re.match(r"^\d{1,3}$", stripped):
            continue  # skip standalone page numbers

        text_type = "paragraph"

        if len(stripped) < 80:
            if re.match(r"^SECTION\s+\d+", stripped, re.IGNORECASE):
                text_type = "heading"
            elif re.match(r"^\d+\.\d+(\.\d+)?\s+", stripped):
                text_type = "heading"
            elif re.match(r"^[A-Z]{3,}(\s+[A-Z]{2,})*(\s+\d+)?$", stripped):
                text_type = "heading"

        if text_type == "paragraph":
            if re.match(r"^[\-\*●]\s+", stripped):
                text_type = "list_item"
            elif re.match(r"^[a-zA-Z0-9][.\)]\s+", stripped):
                text_type = "list_item"
            elif re.match(r"^\([a-zA-Z0-9]\)\s+", stripped):
                text_type = "list_item"
            elif re.match(r"^\d{1,2}\s+(?!January|February|March|April|May|June|July|August|September|October|November|December)(?:https?://|[A-Z])", stripped):
                text_type = "footnote"

        if text_type in ("heading", "footnote"):
            if current_list_item:
                blocks.append({"type": "list_item", "text": current_list_item})
                current_list_item = None
            if current_paragraph:
                blocks.append({"type": "paragraph", "text": " ".join(current_paragraph)})
                current_paragraph = []
            # If the last block was a footnote ending with a hyphen (PDF line-wrap), append to it
            if text_type == "footnote" and blocks and blocks[-1]["type"] == "footnote" and blocks[-1]["text"].endswith("-"):
                blocks[-1]["text"] = blocks[-1]["text"] + stripped
            else:
                blocks.append({"type": text_type, "text": stripped})

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


def _fix_false_splits(sentences: list[dict]) -> list[dict]:
    """Merge sentences where the parser incorrectly split on report-specific patterns."""
    if not sentences:
        return sentences
    merged = [sentences[0]]
    for sent in sentences[1:]:
        is_pattern_split = any(p.match(sent["text"]) for p in _FALSE_SPLIT_PATTERNS)
        is_lowercase_fragment = sent["text"] and sent["text"][0].islower()
        if is_pattern_split or is_lowercase_fragment:
            merged[-1]["text"] += " " + sent["text"]
        else:
            merged.append(sent)
    return merged


def _tokenize_blocks(blocks: list[dict]) -> list[dict]:
    sentences = []
    position = 0

    for block in blocks:
        if block["type"] == "paragraph":
            block_sents = []
            for sent in _nlp(block["text"]).sents:
                sent_text = sent.text.strip()
                if sent_text:
                    block_sents.append({"text": sent_text, "text_type": "paragraph"})
            for sent in _fix_false_splits(block_sents):
                sent["position"] = position
                sentences.append(sent)
                position += 1
        else:
            sentences.append({"text": block["text"], "text_type": block["type"], "position": position})
            position += 1

    return sentences
