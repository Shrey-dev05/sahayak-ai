"""
Ingestion: splits a document's raw text into semantically meaningful
chunks. Simple paragraph-based splitting for the prototype (good enough for
short verified passages); swap in a heading-aware / token-budget chunker for
long real-world PDFs.
"""
from typing import List


def chunk_text(text: str, max_chars: int = 600) -> List[str]:
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    chunks, current = [], ""
    for p in paragraphs:
        if len(current) + len(p) + 1 <= max_chars:
            current = f"{current}\n{p}".strip()
        else:
            if current:
                chunks.append(current)
            current = p
    if current:
        chunks.append(current)
    return chunks or [text.strip()]
