"""
A question can retrieve a topically-correct document that still doesn't
answer it - "what's the crop insurance deadline?" correctly retrieves the
crop insurance doc, but a general-guidance chunk has no date in it. Pure
retrieval scoring can't catch this (the chunk IS the best match available);
only checking whether the evidence actually contains the KIND of fact being
asked can. This is what data/eval/rag_evaluation.jsonl's failures actually
exposed (see README "Known limitation") - this module is the fix.

MockLLM (extractive) needs this because it can't reason about sufficiency
itself. A real LLM provider with the strict grounding prompt in llm.py
(GROQ_SYSTEM_PROMPT / PROMPT) is expected to make this judgment on its own
from the instruction "if the evidence does not contain the answer, say you
could not verify it" - but this check runs for every provider as a cheap,
deterministic backstop, since a prompt instruction is not a guarantee.
"""
import re
from typing import List, Optional

# question pattern -> what the evidence must contain to actually answer it
FACT_CHECKS = {
    "percentage": (
        re.compile(r"\b(percentage|percent|subsidy amount|premium rate|% )\b", re.I),
        re.compile(r"\d+\s*%|\bpercent\b"),
    ),
    "deadline": (
        re.compile(r"\b(deadline|last date|cut-?off|due date|apply by|when (is|does))\b", re.I),
        re.compile(r"\b(20\d{2}|january|february|march|april|may|june|july|august|"
                    r"september|october|november|december|\d{1,2}[/-]\d{1,2})\b", re.I),
    ),
    "contact": (
        re.compile(r"\b(phone|contact|helpline|call|number of)\b", re.I),
        re.compile(r"\b\d{4,}\b|@|helpline"),
    ),
    "amount": (
        re.compile(r"\b(how much|exact amount|fee is|cost is|rupees|rs\.?\s*\d)\b", re.I),
        re.compile(r"[₹$]\s*\d|\brs\.?\s*\d|\b\d+\s*(rupees|inr)\b", re.I),
    ),
}


def requires_specific_fact(question: str) -> Optional[str]:
    for fact_type, (question_pattern, _) in FACT_CHECKS.items():
        if question_pattern.search(question):
            return fact_type
    return None


def evidence_has_fact(evidence_texts: List[str], fact_type: str, question: str = "") -> bool:
    _, evidence_pattern = FACT_CHECKS[fact_type]
    matching_texts = [t for t in evidence_texts if evidence_pattern.search(t)]
    if not matching_texts:
        return False

    if question:
        q_lower = question.lower()
        for kw in ["subsidy", "election", "commissioner"]:
            if kw in q_lower:
                if not any(kw in t.lower() for t in matching_texts):
                    return False
    return True


SCHEME_CODE_RE = re.compile(r"\b([A-Z]{2,6})\b")
COMMON_ACRONYMS = {
    "PACS", "PMFBY", "PM", "KCC", "MSP", "DCCB", "CSC", "KYC", "EMI", "FPO",
    "SHG", "AIF", "SMAM", "ATM", "OTP", "PIN", "UPI", "URL", "PDF", "AGM",
}


def missing_named_entity(question: str, evidence_texts: List[str]) -> bool:
    """
    Checks if the question explicitly refers to a specific named scheme, code,
    or entity (e.g., 'XYZ') that is completely absent from all retrieved evidence.
    If so, returns True (meaning the specific entity asked about is missing).
    """
    codes = set(SCHEME_CODE_RE.findall(question)) - COMMON_ACRONYMS
    if not codes:
        return False
    combined_evidence = " ".join(evidence_texts).upper()
    for code in codes:
        if code.upper() not in combined_evidence:
            return True
    return False
