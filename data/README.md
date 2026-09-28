# Sahayak AI - Data

Three kinds of data, matching the three-layer strategy in
`Sahayak_AI_Training_Data_Knowledge_Base.pdf` section 1: a verified RAG
knowledge base (facts), an intent dataset (behavior/routing), and a
fine-tuning dataset (behavior/tone). None of these were supplied as actual
files by the uploaded PDFs - both PDFs are *specifications* of what to
collect, with a handful of illustrative example rows. Everything under
this directory was generated from those specifications; see each
subfolder's README for exactly how and with what honesty constraints.

## `intents/`
`intent_dataset.jsonl` - 382 synthetic user queries (English / Hindi /
Hinglish) mapped to the 16-intent taxonomy from the pipeline doc's section
18. This is genuinely used: `scripts/train_intent_classifier.py` trains a
real scikit-learn model on it (TF-IDF char+word n-grams + Logistic
Regression, tuned via grid search), evaluated with 5-fold stratified
cross-validation at **79.3% accuracy** (`training_report.txt`) — a more
reliable number than a single train/test split would give on a dataset
this size. Safe to generate synthetically because it teaches *phrasing*,
not facts - "PACS kya hota hai?" is a real way someone would ask,
regardless of who generated the sentence.

## `finetuning/`
`train.jsonl` / `validation.jsonl` / `test.jsonl` - 28/6/7 conversations
in TRL's SFT message format, teaching direct answers, clarification
dialogues, QR-handoff signaling, and honest "I can't verify that" refusals.
Deliberately small - see `finetuning/README.md` in the project root for why,
and how to scale it up before actually fine-tuning anything.

## `eval/`
`rag_evaluation.jsonl` - 16 test questions against the actual seeded
knowledge base, each declaring which source document (if any) should be
retrieved, with `must_not_hallucinate: true` on every row.
`scripts/evaluate_rag.py` runs these against the live backend for real:
**15/16 pass** (started at 8/16; two real fixes in `app/rag/retrieval.py`
and the new `app/rag/fact_check.py` closed the gap - see the main README's
"Training data & the trained model" section for what each fix does and
what the one remaining failure needs).

## What's NOT here

Real verified content for the RAG knowledge base itself (cooperative acts,
scheme guidelines, PMFBY documents, etc.). That's the one category in the
original blueprint that *cannot* be synthesized - inventing plausible-
looking legal or scheme text would be exactly the hallucination this whole
project is designed to prevent. `backend/app/seed.py` ships 7 clearly-
labeled demo/placeholder documents instead, and the admin console
(`/admin-ui/`) is where real, sourced documents get added and verified.
