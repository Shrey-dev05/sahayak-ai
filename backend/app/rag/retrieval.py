"""
Retrieval for the prototype: pure-Python TF-IDF cosine scoring over
APPROVED chunks only. No external vector DB or embedding API is required,
so the demo runs offline with zero cloud accounts.

To upgrade to real semantic search (as the plan's architecture calls for):
replace `score_chunks()` with embedding similarity against pgvector (or
another vector store) - the rest of the pipeline (orchestrator, citations,
no-evidence fallback) is unchanged because it only depends on this
function returning (chunk, score) pairs.
"""
import math
import re
from collections import Counter
from typing import List, Tuple
from sqlalchemy.orm import Session as DBSession
from app import models

TOKEN_RE = re.compile(r"[\w\u0900-\u097F]+")

STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "in", "on", "at", "to", "for", "of", "with", "from", "by", "this",
    "that", "it", "its", "and", "or", "but", "if", "so", "as", "not",
    "no", "do", "does", "did", "i", "you", "he", "she", "we", "they",
    "what", "who", "how", "when", "where", "why", "can", "could", "will",
    "would", "should", "me", "my", "your", "about", "tell", "please",
    # Hindi/Hinglish function words - romanized. Without these, common
    # grammatical words (not stopwords in an English list) drag down the
    # match-coverage ratio for every Hindi/Hinglish query, which is exactly
    # the "verified against a real evaluation set" bug this file used to
    # have - see data/eval/rag_evaluation.jsonl and scripts/evaluate_rag.py.
    "ka", "ki", "ke", "ko", "se", "me", "mein", "hai", "hain", "ho", "hota",
    "hoti", "hote", "hoon", "kya", "kaise", "kaisi", "kaisa", "kyu", "kyun",
    "aur", "ya", "kar", "karo", "karna", "karta", "karti", "kare", "chahiye",
    "wala", "wali", "wale", "liye", "iske", "uske", "iska", "uska", "par",
    "bhi", "ab", "to", "hi", "yeh", "ye", "wo", "woh", "unka", "apna", "apne",
}

# Small Hindi/Hinglish -> English domain-term glossary. Query expansion, not
# translation: original tokens are kept, English equivalents are ADDED, so a
# code-switched query like "shikayat kaise darj kare" can still match an
# English-language approved chunk about grievances. Covers the plan's
# priority domains (cooperative law, PACS, schemes, crop insurance,
# grievances) - not a full dictionary, and it's a lexical stopgap, not a
# substitute for the real multilingual embeddings the pipeline recommends
# (see README "Known limitation").
GLOSSARY = {
    "shikayat": ["grievance", "complaint"], "fasal": ["crop"], "bima": ["insurance"],
    "insurance": ["bima"], "byaj": ["interest"], "byaaj": ["interest"],
    "sadasya": ["member"], "sadasyata": ["membership"], "samiti": ["society"],
    "sangathan": ["organization"], "karz": ["loan", "debt"], "rin": ["loan"],
    "bachat": ["savings"], "khata": ["account"], "kisan": ["farmer"],
    "nuksan": ["damage", "loss"], "barbad": ["damage"], "kharab": ["damage"],
    "darj": ["file", "register"], "panjikaran": ["registration"],
    "sarkari": ["government"], "yojana": ["scheme"], "adhikar": ["rights"],
    "niyam": ["rules"], "kanoon": ["law"], "byaj-dar": ["interest rate"],
    "dastavez": ["document"], "gaon": ["village"],
}
MIN_MATCH_SCORE = 1.5  # combined idf score floor - tuned for this small demo corpus
MIN_COVERAGE = 0.3     # at least this share of the query's content words must match

# Words that are common enough in everyday questions that matching them
# ALONE should never count as evidence, even if they happen to be
# statistically rare in this small demo corpus (e.g. "percentage" only
# appears once, in the interest/savings doc, but that doesn't mean a
# question containing "percentage" is actually about savings). Found via
# scripts/evaluate_rag.py, not guessed - see data/eval/evaluation_report.txt
# and README "Known limitation" for the failures this fixes.
AMBIGUOUS_TERMS = {
    "weather", "today", "current", "year", "exact", "percentage", "number",
    "phone", "price", "cost", "amount", "date", "time", "new", "old",
}


def tokenize(text: str) -> List[str]:
    return TOKEN_RE.findall(text.lower())


def query_terms(text: str) -> List[str]:
    base = [t for t in tokenize(text) if t not in STOPWORDS and len(t) > 2]
    expanded = list(base)
    for t in base:
        expanded.extend(GLOSSARY.get(t, []))
    return expanded


def score_chunks(db: DBSession, query: str, top_k: int = 3) -> List[Tuple[models.Chunk, float]]:
    q_terms = query_terms(query)
    if not q_terms:
        return []

    chunks = (
        db.query(models.Chunk)
        .join(models.Document, models.Chunk.document_id == models.Document.id)
        .filter(models.Document.status == "approved")
        .all()
    )
    if not chunks:
        return []

    doc_freq = Counter()
    chunk_tokens = {}
    for c in chunks:
        toks = set(tokenize(c.text))
        chunk_tokens[c.id] = toks
        for t in toks:
            doc_freq[t] += 1

    n_docs = len(chunks)
    scored = []
    for c in chunks:
        toks = chunk_tokens[c.id]
        score, matched_terms = 0.0, []
        for qt in q_terms:
            if qt in toks:
                idf = math.log((n_docs + 1) / (doc_freq[qt] + 1)) + 1
                score += idf
                matched_terms.append(qt)
        matched = len(matched_terms)
        coverage = matched / len(q_terms)
        # Reject if every matched term is a generic/ambiguous word - real
        # evidence needs at least one term that's actually specific to what
        # was asked, not just incidental overlap on common vocabulary.
        anchored = any(t not in AMBIGUOUS_TERMS for t in matched_terms)
        if score >= MIN_MATCH_SCORE and coverage >= MIN_COVERAGE and anchored:
            scored.append((c, round(score, 3)))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]
