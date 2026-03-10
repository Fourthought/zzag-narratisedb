import re

import spacy

from utils.pdf.remove_cover_watermarks import remove_cover_watermarks

_nlp = spacy.load("en_core_web_sm", exclude=["tagger", "attribute_ruler", "lemmatizer", "ner"])

# When a paragraph line follows a list item, these trailing words signal the list item may wrap onto it
_HANGING_CONJUNCTION = re.compile(r"\b(and|or|nor|that|which|the|a|an|of|to|in|into|on|at|by|for|with|from|between|among|through|across)\s*$", re.IGNORECASE)

# Sentence-initial patterns that indicate a false split by the parser
_FALSE_SPLIT_PATTERNS = (
    re.compile(r"^\d+/\d{4}"),        # report numbers: "17/2024"
    re.compile(r"^NO\s+\d+/\d{4}"),  # report number with prefix: "NO 17/2024 NOVEMBER 2024"
    re.compile(r"^\d{4}$"),            # standalone years: "2024"
)

# Section/citation references embedded in text lines, e.g. "[2.7.1]"
_CITATION_PREFIX = re.compile(r"^\[\d+(?:\.\d+)*\]\s*")

# Stub list-item markers with no body content, e.g. "10." or "14)"
_STUB_MARKER = re.compile(r"^\d+[.\)]\s*$")


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
    blocks = _merge_wrapped_headings(blocks)
    blocks = _merge_wrapped_list_items(blocks)
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

        # Strip leading citation references that PDF extraction attaches to the next line
        stripped = _CITATION_PREFIX.sub("", stripped).strip()
        if not stripped:
            continue

        if re.match(r"^\d{1,3}$", stripped):
            continue  # skip standalone page numbers

        text_type = "paragraph"

        if len(stripped) < 80:
            if re.match(r"^SECTION\s+\d+", stripped, re.IGNORECASE):
                text_type = "heading"
            elif re.match(r"^\d+\.\d+(\.\d+)?\s+[A-Za-z]", stripped):
                text_type = "heading"
            elif re.match(r"^[A-Z]{3,}(\s+[A-Z]{2,})*(\s+\d+)?$", stripped):
                text_type = "heading"

        if text_type == "paragraph":
            # Bullets are unambiguous list markers regardless of context
            if re.match(r"^[\-\*●]\s+", stripped):
                text_type = "list_item"
            # Standalone digit markers (e.g. "8." alone after citation stripping) are unambiguous
            elif re.match(r"^\d+[.\)]\s*$", stripped):
                text_type = "list_item"
            else:
                # For all other list patterns, don't classify mid-paragraph lines as list items.
                # If the current paragraph ends without sentence-final punctuation, the line is
                # more likely a continuation (e.g. PDF line-wrap of "Amendment\n1. The suite...").
                last_para_line = re.sub(r"\s*\[[\d.]+\]\s*$", "", current_paragraph[-1]) if current_paragraph else ""
                mid_paragraph = bool(current_paragraph) and not last_para_line.rstrip().endswith(('.', '!', '?', ':'))
                if not mid_paragraph:
                    if re.match(r"^[a-zA-Z0-9][.\)]\s+", stripped):
                        text_type = "list_item"
                    elif re.match(r"^\d{2,3}[.\)](\s+|$)", stripped):
                        text_type = "list_item"
                    elif re.match(r"^\([a-zA-Z0-9]\)\s+", stripped):
                        text_type = "list_item"
                    elif re.match(r"^[A-Za-z°][A-Za-z°/.\d]{0,8}\s+[-–]\s+", stripped):
                        text_type = "list_item"
                if text_type == "paragraph":
                    _MONTHS = r"(?!January|February|March|April|May|June|July|August|September|October|November|December)"
                    if re.match(rf"^\d{{1,2}}\s+{_MONTHS}(?:https?://|[A-Z])", stripped):
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
            # URL path continuation: no spaces, follows a footnote ending with a hyphen
            prev_is_hyphen_footnote = (blocks and blocks[-1]["type"] == "footnote" and blocks[-1]["text"].endswith("-"))
            if not current_paragraph and not current_list_item and prev_is_hyphen_footnote and " " not in stripped:
                blocks[-1]["text"] += stripped
            elif current_list_item:
                list_ends_without_punct = not current_list_item.rstrip().endswith(('.', '!', '?'))
                line_starts_lowercase = stripped[0].islower()
                hanging_conjunction = bool(_HANGING_CONJUNCTION.search(current_list_item.rstrip()))
                unmatched_paren = current_list_item.count('(') > current_list_item.count(')')
                ends_with_possessive = bool(re.search(r"['\u2019]\w*\s*$", current_list_item.rstrip()))
                ends_with_allcaps = bool(re.search(r"\b[A-Z]{2,}\s*$", current_list_item.rstrip()))
                if list_ends_without_punct and (line_starts_lowercase or hanging_conjunction or unmatched_paren or ends_with_possessive or ends_with_allcaps):
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


def _merge_wrapped_headings(blocks: list[dict]) -> list[dict]:
    """Merge consecutive heading blocks that are PDF line-wrap continuations of a single heading.

    Uses the spaCy dependency tag of the last token to detect open-ended headings
    (e.g. ending with a preposition or determiner) that wrap onto the next line.
    """
    _OPEN_DEP = {"prep", "cc", "mark", "det", "amod", "compound", "quantmod", "pobj"}

    if not blocks:
        return blocks

    merged = [blocks[0]]
    for block in blocks[1:]:
        prev = merged[-1]
        if prev["type"] == "heading" and block["type"] == "heading":
            # A block starting with a section number is always a new heading, not a continuation
            next_is_new_section = bool(re.match(r"^\d+\.\d+|^SECTION\s+\d+", block["text"], re.IGNORECASE))
            if not next_is_new_section:
                last_token = _nlp(prev["text"])[-1]
                if last_token.dep_ in _OPEN_DEP:
                    prev["text"] += " " + block["text"]
                    continue
        merged.append(block)
    return merged


def _merge_wrapped_list_items(blocks: list[dict]) -> list[dict]:
    """Merge paragraph blocks that are PDF line-wrap continuations of a preceding list item.

    Uses the spaCy dependency tag of the last token of the list item to detect
    open-ended phrases that string heuristics cannot catch (e.g. prepositions,
    conjunctions, determiners at the end of a wrapped line). Also merges stub
    list-item markers (e.g. "10.") that appear alone on a line with their content.
    """
    _OPEN_DEP = {"prep", "cc", "mark", "det", "amod", "compound", "quantmod", "pobj"}

    if not blocks:
        return blocks

    merged = [blocks[0]]
    for block in blocks[1:]:
        prev = merged[-1]
        if prev["type"] == "list_item" and block["type"] == "paragraph":
            # Stub marker (e.g. "10." with no body) — always merge with following paragraph
            if _STUB_MARKER.match(prev["text"].strip()):
                prev["text"] = prev["text"].strip() + " " + block["text"]
                continue
            # NLP dep_ check for open-ended phrases
            doc = _nlp(prev["text"])
            last_token = doc[-1]
            if last_token.dep_ in _OPEN_DEP:
                prev["text"] += " " + block["text"]
                continue
        merged.append(block)
    return merged


def _fix_false_splits(sentences: list[dict]) -> list[dict]:
    """Merge sentences where the parser incorrectly split on report-specific patterns."""
    if not sentences:
        return sentences
    merged = [sentences[0]]
    for sent in sentences[1:]:
        is_pattern_split = any(p.match(sent["text"]) for p in _FALSE_SPLIT_PATTERNS)
        is_lowercase_fragment = sent["text"] and sent["text"][0].islower()
        both_paragraphs = merged[-1]["text_type"] == "paragraph" and sent["text_type"] == "paragraph"
        if (is_pattern_split or is_lowercase_fragment) and both_paragraphs:
            merged[-1]["text"] += " " + sent["text"]
        else:
            merged.append(sent)
    return merged


def _tokenize_blocks(blocks: list[dict]) -> list[dict]:
    sentences = []

    for block in blocks:
        if block["type"] == "paragraph":
            for sent in _nlp(block["text"]).sents:
                sent_text = sent.text.strip()
                if sent_text:
                    sentences.append({"text": sent_text, "text_type": "paragraph"})
        else:
            sentences.append({"text": block["text"], "text_type": block["type"]})

    sentences = _fix_false_splits(sentences)

    for i, sent in enumerate(sentences):
        sent["position"] = i

    return sentences
