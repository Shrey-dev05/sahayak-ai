"""
Intent classification.

Primary path: a real trained model - TF-IDF(char n-grams) + Logistic
Regression, trained by scripts/train_intent_classifier.py on
data/intents/intent_dataset.jsonl (see backend/app/ai/models/intent_clf.joblib
and data/intents/training_report.txt for the held-out accuracy this scored).
It needs no network access or API key, which is why it - unlike the Groq
generation step - could actually be trained inside this sandbox.

Fallback path: the original keyword matcher, used if the model file is
missing or fails to load, and also used to fill in `entities`, which the
classifier does not predict.
"""
import re
from pathlib import Path
from typing import Tuple, Dict

_MODEL_PATH = Path(__file__).resolve().parent / "models" / "intent_clf.joblib"
_model = None
_model_load_attempted = False


def _get_model():
    global _model, _model_load_attempted
    if not _model_load_attempted:
        _model_load_attempted = True
        try:
            import joblib
            if _MODEL_PATH.exists():
                _model = joblib.load(_MODEL_PATH)
        except Exception:
            _model = None  # fall back to keyword matching below
    return _model

INTENTS = {
    "cooperative_governance": ["cooperative", "society", "by-law", "bylaw", "governance", "सहकारी"],
    "scheme_navigation": ["pacs", "scheme", "service", "eligibility"],
    "agri_insurance": ["crop", "insurance", "fasal", "bima", "farm", "फसल"],
    "financial_literacy": ["interest", "savings", "loan", "emi", "bank", "deposit"],
    "grievance": ["grievance", "complaint", "cheated", "unfair", "problem with", "शिकायत"],
    "document_explanation": ["document", "scan", "photo", "ocr", "upload"],
}

COMPLEX_TRIGGERS = [
    "scan", "photo", "document", "upload", "form", "checklist",
    "file a complaint", "submit", "picture", "फोटो", "दस्तावेज़", "फॉर्म",
]

ENTITY_PATTERNS = {
    "crop": ["rice", "wheat", "cotton", "sugarcane", "maize", "धान", "गेहूं"],
}


def _keyword_classify(text: str) -> Tuple[str, float]:
    t = text.lower()
    best_intent, best_score = "general_information", 0.0
    for name, keywords in INTENTS.items():
        hits = sum(1 for kw in keywords if kw in t)
        if hits:
            score = min(1.0, 0.5 + 0.15 * hits)
            if score > best_score:
                best_intent, best_score = name, score
    return best_intent, best_score


def classify_intent(text: str) -> Tuple[str, float, Dict]:
    model = _get_model()
    if model is not None:
        try:
            pred = model.predict([text])[0]
            proba = model.predict_proba([text])[0].max()
            intent_name, confidence = pred, float(proba)
        except Exception:
            intent_name, confidence = _keyword_classify(text)
    else:
        intent_name, confidence = _keyword_classify(text)

    entities = {}
    t = text.lower()
    for entity, values in ENTITY_PATTERNS.items():
        for v in values:
            if v in t:
                entities[entity] = v
                break
    return intent_name, round(confidence, 3), entities


def is_complex(text: str) -> bool:
    t = text.lower()
    return any(w in t for w in COMPLEX_TRIGGERS)
