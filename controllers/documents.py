from services.supabase.service import SupabaseService


def get_full_text(db: SupabaseService, doc_id: str) -> str | None:
    """Reconstruct document as plain text — all sentences ordered by position.

    Returns None if the document has no sentences (or doesn't exist).
    Headings are preceded by a blank line.
    """
    result = (
        db.client.table("sentences")
        .select("text, text_type")
        .eq("document_id", doc_id)
        .order("position")
        .execute()
    )

    if not result.data:
        return None

    lines = []
    for sent in result.data:
        if sent["text_type"] == "heading":
            lines.append("")
        lines.append(sent["text"])

    return "\n".join(lines).strip()
