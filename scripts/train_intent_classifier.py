"""
Trains a local, dependency-light intent classifier: TF-IDF over character
n-grams (robust to Hindi/Hinglish/English mixing without needing a
language-specific tokenizer or a downloaded embedding model) + Logistic
Regression. This is a genuinely trained, genuinely evaluated model - not a
stub - and it needs no GPU, no API key, and no network access, which makes
it the one component of the pipeline in Model_Training_pipeline.pdf that
can actually be trained end-to-end inside a sandboxed environment.

It is NOT a replacement for the Groq/fine-tuned generation model the
pipeline describes - it only does intent classification (routing), the
same job app/ai/intents.py's keyword matcher did before. Swapping in a
real LLM for answer generation is a separate, still-open step (see
backend/app/ai/llm_groq.py).

Run: python3 scripts/train_intent_classifier.py
"""
import json
import sys
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score, cross_val_predict
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.metrics import classification_report, accuracy_score
import joblib

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "intents" / "intent_dataset.jsonl"
MODEL_OUT = ROOT / "backend" / "app" / "ai" / "models" / "intent_clf.joblib"
REPORT_OUT = ROOT / "data" / "intents" / "training_report.txt"


def build_pipeline(C=5.0):
    # Two complementary views of the same text: character n-grams handle
    # Hindi/Hinglish/English mixing and typos without needing a tokenizer
    # per language; word n-grams capture whole-word cues like "kaise bane"
    # or "documents chahiye" that char n-grams dilute across many features.
    features = FeatureUnion([
        ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), min_df=1, sublinear_tf=True)),
        ("word", TfidfVectorizer(analyzer="word", ngram_range=(1, 2), min_df=1, sublinear_tf=True)),
    ])
    return Pipeline([
        ("features", features),
        ("clf", LogisticRegression(max_iter=3000, class_weight="balanced", C=C)),
    ])


def load_rows(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def main():
    rows = load_rows(DATA)
    X = [r["text"] for r in rows]
    y = [r["intent"] for r in rows]

    # Small grid search over C, scored by 5-fold stratified CV accuracy -
    # picks a regularization strength instead of guessing one.
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    best_c, best_score = None, -1
    for C in [1.0, 2.0, 5.0, 8.0]:
        scores = cross_val_score(build_pipeline(C), X, y, cv=cv, scoring="accuracy")
        mean_score = scores.mean()
        print(f"C={C:<5} 5-fold CV accuracy = {mean_score:.3f} (+/- {scores.std():.3f})")
        if mean_score > best_score:
            best_c, best_score = C, mean_score

    print(f"\nBest C={best_c}, 5-fold CV accuracy={best_score:.3f}")

    # cross_val_predict gives an out-of-fold prediction for EVERY example,
    # so the classification report below uses all 382 examples as "held
    # out" (each one, just never from the fold that predicted it) instead
    # of the noisy ~15% single split the first version of this script used.
    from sklearn.model_selection import cross_val_predict
    y_pred = cross_val_predict(build_pipeline(best_c), X, y, cv=cv)
    acc = accuracy_score(y, y_pred)
    report = classification_report(y, y_pred, zero_division=0)

    summary = (
        f"Trained on {len(X)} examples, 5-fold stratified cross-validation (best C={best_c}).\n"
        f"Out-of-fold accuracy across all {len(X)} examples: {acc:.3f}\n\n{report}"
    )
    print("\n" + summary)

    # Final deployable model: refit on ALL data with the tuned C.
    final_pipeline = build_pipeline(best_c)
    final_pipeline.fit(X, y)

    MODEL_OUT.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(final_pipeline, MODEL_OUT)
    REPORT_OUT.write_text(summary, encoding="utf-8")
    print(f"\nSaved model -> {MODEL_OUT}")
    print(f"Saved report -> {REPORT_OUT}")


if __name__ == "__main__":
    main()
