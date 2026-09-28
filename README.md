# Sahayak AI — Working Prototype

A runnable implementation of a multilingual rural cooperative/government
assistance chatbot, built from three source documents in this repo:
[`Sahayak_AI_Prototype_Implementation_Plan.pdf`](./Sahayak_AI_Prototype_Implementation_Plan.pdf)
(architecture/UX), [`Sahayak_AI_Training_Data_Knowledge_Base.pdf`](./Sahayak_AI_Training_Data_Knowledge_Base.pdf)
(data strategy) and [`Model_Training_pipeline.pdf`](./Model_Training_pipeline.pdf)
(RAG + fine-tuning pipeline). Every claim in this README has been run and
checked in this repo, not just written down — see "How to verify everything
below" if you don't want to take that on faith.

**Status in one line:** FastAPI backend with a real database, real tested
APIs, a real trained intent classifier (79.3% cross-validated accuracy),
and a real-but-simplified RAG pipeline (15/16 on its own eval set) that
answers extractively (safe, can't hallucinate, but can't paraphrase) unless
you plug in a real LLM key. Three frontends. No hardware, no live LLM call,
no fine-tuning has actually been executed — see "What's real vs. mocked."

---

## If you are an AI agent picking this up

Read this section first; it's written for you specifically. The rest of
the README (starting at "Quick start") is reference material this section
points into.

### 1. Bootstrap and prove to yourself it works

```bash
cd backend
pip install -r requirements.txt --break-system-packages   # drop the flag if not on Debian/Ubuntu
pytest -q                                                   # expect: 19 passed
cd ..
python3 scripts/evaluate_rag.py                              # expect: 15/16
python3 scripts/train_intent_classifier.py                   # expect: ~0.79 5-fold CV accuracy
cd backend && uvicorn app.main:app --reload --port 8000
```
Then `curl localhost:8000/health` should return `{"status":"ok"}`, and
`localhost:8000/kiosk/`, `/mobile/`, `/admin-ui/` should all return 200.
If any of these numbers don't match, something regressed — fix that before
building on top of it, and update the number in this README if the fix
legitimately changes it.

### 2. How the request path actually works (read before changing `app/ai/` or `app/rag/`)

```
POST /chat {session_id, text, language}
  -> app/api/routes_chat.py          (thin: loads Session, calls orchestrator)
  -> app/ai/orchestrator.py          handle_message() - THE central function
       1. classify_intent(text)       app/ai/intents.py  (trained model + keyword fallback)
       2. is_complex(text)            app/ai/intents.py  (keyword trigger list)
       3. score_chunks(db, text)      app/rag/retrieval.py (TF-IDF, approved docs only)
       4. requires_specific_fact()    app/rag/fact_check.py (does the question need a date/%/contact?)
          + evidence_has_fact()        -> if yes and evidence lacks it, force HUMAN_ESCALATION
       5. build_action_plan()         app/services/action_plan.py (only from curated PLAN_LIBRARY)
       6. get_llm_provider()          app/ai/llm.py (mock/anthropic/groq) .simplify_and_answer()
       7. writes Message rows, returns ChatResponse (schemas.py)
```
Kiosk, mobile, and document-scan (`/document/analyze`) all call this same
`handle_message()` — that's deliberate (see plan section "Important
implementation decision"). Don't give kiosk and mobile separate AI logic.

### 3. Design conventions already established — follow them, don't reinvent

- **Provider adapter pattern** (`app/ai/llm.py`, `app/speech/stt.py`,
  `app/speech/tts.py`, `app/vision/ocr.py`): an abstract class with a
  `Mock*` default (zero config, deterministic, honest about being fake)
  and real implementations gated by an env var (`LLM_PROVIDER`, etc.), all
  selected through a `get_*_provider()` factory. **Adding a new external
  service should follow this exact shape** — abstract interface, Mock
  implementation first, real implementation second, one env var to switch.
- **One router file per resource** under `app/api/`, each `include_router`-ed
  in `main.py`. A new resource gets its own `routes_<name>.py`.
- **Pydantic schemas in one file** (`app/schemas.py`), not scattered inline.
- **SQLAlchemy models in one file** (`app/models.py`), matching the plan's
  section 9 table list — don't add a table without a reason traceable back
  to a real feature.
- **Every new backend behavior gets a pytest test in `backend/tests/`**,
  not just a manual check. Tests use `tests/conftest.py`'s `client` fixture,
  which spins up an isolated temp-SQLite-backed TestClient per test — copy
  an existing test file's pattern.
- **Scripts are one-purpose and idempotent**, live in `scripts/`, and print
  a result you can eyeball (accuracy, pass/fail count) rather than just
  "done." `generate_*` scripts build `data/`; `train_*`/`evaluate_*`
  scripts consume it and write a `*_report.txt` next to the data they
  evaluated.

### 4. Rules you must not break

These aren't style preferences — breaking them reopens hallucination risk
that was deliberately closed:

- **Never let the system state a fact (date, fee, phone number, eligibility
  rule, URL) that isn't literally present in an `approved`-status document
  chunk.** This is why `MockLLM` is extractive and why `fact_check.py`
  exists. If you enable a real LLM provider, its system prompt (already
  written in `llm.py`) must keep this rule — don't loosen it for "better"
  answers.
- **A `pending` document must never be retrievable.** `rag/retrieval.py`
  filters on `Document.status == "approved"` — this is covered by
  `test_pending_document_not_retrieved` and `test_approving_document_makes_it_retrievable`.
  If you touch retrieval, both must still pass.
- **Don't invent government facts anywhere** — not in seed data, not in
  code comments used as examples, not in generated training data. Real
  scheme/law content must come from an admin-uploaded, admin-approved,
  sourced document (`/admin/documents`), never hardcoded. Everything in
  `app/seed.py` is deliberately generic/definitional for this reason —
  extend it the same way, or replace it with real sourced text via the
  admin API, not by writing more specific-sounding placeholder facts.
- **`GroqLLM` and `AnthropicLLM` in `app/ai/llm.py` have not been called
  live from this development environment** (network to `api.groq.com` and
  `huggingface.co`/`anthropic` endpoints was blocked here — verified with
  `curl`, not assumed). They should work normally in a real deployment
  with a valid key; if you have API access, actually call them and update
  this README's "What's real vs. mocked" table honestly instead of leaving
  the old caveat in place.

### 5. Suggested next tasks, roughly in priority order

Each has a concrete "done when" check so you (or the next agent) can tell
when it's actually finished, not just attempted.

1. **Expand `data/finetuning/`** (currently ~29 train examples — a format
   demo, not a real dataset). Add more via `scripts/generate_finetuning_dataset.py`'s
   existing template pattern. *Done when:* `train.jsonl` has 300+ conversations
   without duplicate near-identical phrasing.
2. **Fix the one remaining `evaluate_rag.py` failure** ("Tell me about
   sample scheme XYZ" retrieves generic scheme-discovery guidance instead
   of returning no evidence). Needs a named-entity-not-in-evidence check,
   analogous to `fact_check.py` but for proper nouns rather than fact
   types. *Done when:* `python3 scripts/evaluate_rag.py` prints `16/16`.
3. **Real embeddings for retrieval**, replacing/augmenting `app/rag/retrieval.py`'s
   TF-IDF. The pipeline doc recommends `BAAI/bge-m3` via `sentence-transformers`
   + pgvector; that download is network-blocked in this dev sandbox but
   should work in a normal environment. *Done when:* `evaluate_rag.py` still
   passes 16/16 (don't regress the lexical fixes) and a semantic-only query
   like "meri fasal doob gayi" (no shared words with any doc) retrieves the
   crop-insurance doc, which pure TF-IDF cannot do.
4. **Enable a real LLM provider** (`LLM_PROVIDER=groq` or `anthropic` + a
   real key) and re-run `evaluate_rag.py` — the extractive `MockLLM` passing
   15/16 is a floor, not a ceiling; a real model with the existing strict
   prompt should do at least as well while also paraphrasing/simplifying/
   translating, which `MockLLM` structurally cannot do.
5. **Add real, sourced knowledge documents** through `/admin-ui/` (or
   directly via `POST /admin/documents`) for at least the plan's top
   priority domains (cooperative law, PACS, government schemes, crop
   insurance, grievances) with real `source_url`/`issuer` values, replacing
   the demo placeholders in `app/seed.py`. *Done when:* at least one real,
   citable, non-placeholder document exists per priority domain.
6. **Admin authentication** — `/admin/*` currently has none. *Done when:*
   an unauthenticated request to any `/admin/*` route returns 401/403.
7. **Postgres + pgvector** — swap `DATABASE_URL`, add the `vector` extension,
   migrate `Chunk.embedding`. Schema is already sketched in the pipeline
   PDF section 5. *Done when:* the full pytest suite passes unchanged
   against a Postgres backend (tests should not need to know which DB
   they're running against — if they do, that's a bug to fix first).
8. **React frontends**, if your team prefers that stack over the current
   plain HTML/JS. All logic lives server-side, so this is a UI-only port —
   `frontend-kiosk/index.html` and `frontend-mobile/index.html` show the
   exact API calls to replicate.

### 6. How to verify everything below (don't trust stale numbers)

```bash
cd backend && pytest -q                              # 19 passed
cd .. && python3 scripts/evaluate_rag.py              # 15/16 (see data/eval/evaluation_report.txt)
python3 scripts/train_intent_classifier.py             # ~0.79 5-fold CV accuracy (see data/intents/training_report.txt)
```
If you change `app/rag/`, `app/ai/`, or `data/`, re-run the relevant script
and **update the numbers in this README in the same commit** — a stale
accuracy claim is worse than none.

---

## Quick start

```bash
cd backend
pip install -r requirements.txt          # add --break-system-packages on Debian/Ubuntu if needed
uvicorn app.main:app --reload --port 8000
```

Then open:
- **Kiosk:** http://localhost:8000/kiosk/
- **Admin console:** http://localhost:8000/admin-ui/
- **API docs (Swagger):** http://localhost:8000/docs
- **Mobile dashboard:** opened automatically by scanning the QR the kiosk shows (or via the link printed under the QR)

The database auto-seeds on first run (7 approved demo documents + 1
deliberately-pending one, so you can see the approval workflow do
something). No external accounts, API keys, or cloud services are required
to run the full flow end-to-end.

## Training data & the trained model

Two more PDFs (data blueprint + training pipeline) describe a Groq +
pgvector + BAAI/bge-m3 + LoRA/Qwen architecture. Important scope note:
**neither PDF contained an actual dataset** — both are specifications with
a handful of illustrative example rows. `scripts/generate_*.py` turned
those specs into real files under `data/` (see `data/README.md`).

- **Groq and Hugging Face are network-blocked in this development sandbox**
  (`curl -sI https://huggingface.co` / `https://api.groq.com` both return
  `403 host_not_allowed`) and no API key was provided, so no live Groq call
  or model download has happened in this repo. The code for both is
  written and ready (`app/ai/llm.py`: `GroqLLM`, `AnthropicLLM`) — they
  should work normally in a real deployment with a key.
- **The intent classifier was actually trained and evaluated**: TF-IDF
  (character + word n-grams) + Logistic Regression, tuned via grid search,
  scored with 5-fold stratified cross-validation (not a single noisy
  split) — **79.3% accuracy** across 382 examples and 16 intents
  (`data/intents/training_report.txt`). Retrain any time with
  `python3 scripts/train_intent_classifier.py`.
- **RAG retrieval quality was actually measured**: `python3 scripts/evaluate_rag.py`
  runs 16 real questions against the live backend and checks both "found
  the right source" and "correctly refused when there's no evidence."
  Current score: **15/16** (`data/eval/evaluation_report.txt`), up from an
  initial 8/16 through two real fixes, both still in the codebase:
  - `AMBIGUOUS_TERMS` gate in `app/rag/retrieval.py` — a match on a single
    generic word ("weather", "today", "current"...) that happens to appear
    in a chunk doesn't count as evidence on its own.
  - `app/rag/fact_check.py` — if a question asks for a specific fact type
    (a deadline, a percentage, a contact) and the retrieved evidence
    doesn't contain that kind of fact, the system refuses rather than
    presenting a topically-related-but-non-answering passage as an answer.
  The one remaining failure is task #2 in the agent task list above.
- **Fine-tuning is code-ready, not run** — see `finetuning/README.md` for
  exactly why (no GPU, no Hugging Face access here) and what it needs.

## What's real vs. mocked

| Piece | Status |
|---|---|
| Session/message/document/QR/grievance database (plan section 9) | **Real** — SQLAlchemy + SQLite (swap `DATABASE_URL` for Postgres) |
| All 13 core APIs (plan section 9) | **Real** — FastAPI, tested |
| Deterministic orchestration, response-mode routing (plan section 10) | **Real** |
| Intent classification | **Real, trained, evaluated** — 79.3% 5-fold CV accuracy. See above. |
| RAG retrieval | **Real, measured, simplified**: TF-IDF over approved chunks, not pgvector + embeddings. 15/16 on the real eval set. No API key needed. `app/rag/retrieval.py`'s `score_chunks()` is the swap point for real embeddings. |
| Hallucination guardrails | **Real**: approved-only retrieval, ambiguous-term gating, fact-sufficiency checking, extractive-by-default generation. Four independent layers, each tested. |
| Answer generation | **Real, extractive by default**: `MockLLM` returns retrieved evidence verbatim — can't hallucinate, can't paraphrase either. `GroqLLM`/`AnthropicLLM` are written and ready but unexercised here (network-blocked, see above). |
| Fine-tuning | **Code-ready, not run.** `finetuning/train.py`, ~29-conversation seed set in `data/finetuning/`. Needs GPU + Hugging Face access this sandbox doesn't have. |
| STT / TTS | **Mocked** on the backend (`app/speech/`); kiosk/mobile UIs use the browser's own Web Speech API for real voice today. |
| OCR | **Mocked** (`app/vision/ocr.py`) — honestly reports no real text rather than inventing a plausible extraction. |
| Admin auth | **Not implemented** — task #6 above. |
| Hardware kiosk enclosure, ESP32, physical build (plan sections 11–12) | **Not attempted** — outside what a chat session can produce. |

## Project structure

```
backend/
  app/
    main.py            FastAPI app, mounts the three frontends as static sites
    core/               config, db session
    models.py           Session, Message, Document, Chunk, SourceCitation,
                         ActionPlan, QRSession, Grievance, Upload, AuditLog
    schemas.py           Pydantic request/response models
    ai/
      orchestrator.py    the deterministic pipeline (plan section 10) - START HERE
      intents.py         trained classifier + keyword fallback
      llm.py             LLM provider adapter (mock + Anthropic + Groq)
      models/intent_clf.joblib   the trained intent classifier artifact
    rag/
      ingest.py          chunking
      retrieval.py        TF-IDF retrieval, ambiguous-term gate, no-evidence threshold
      fact_check.py        specific-fact-type sufficiency guard
    speech/, vision/      STT/TTS/OCR provider adapters
    services/
      qr_service.py       signed, short-lived, single-use QR tokens
      action_plan.py       builds checklists only from verified doc metadata
      grievance.py          complaint draft templates
    api/                  one router per resource, matching plan section 9's API table
    seed.py                creates tables + seeds the demo knowledge base
  tests/                  19 pytest tests - the source of truth for expected behavior
frontend-kiosk/            single-page kiosk UI (voice + text, calls the API)
frontend-mobile/           QR-joined mobile dashboard (scan, grievance, chat)
admin/                     document review/approval console
data/
  intents/                 intent dataset + trained-model accuracy report
  finetuning/               SFT conversational dataset (train/val/test)
  eval/                     RAG evaluation set + real results
scripts/
  generate_intent_dataset.py       builds data/intents/intent_dataset.jsonl
  generate_finetuning_dataset.py   builds data/finetuning/*.jsonl
  train_intent_classifier.py        trains + evaluates the real intent model
  evaluate_rag.py                    runs data/eval/ against the live backend
finetuning/                 LoRA/SFT script (needs GPU + HF access to run)
```

## Deliberate changes from the original plan

- **Frontends are plain HTML/JS, not React/Next.js.** Same UX, same API
  contract — a React rebuild is a drop-in replacement (task #8) because
  all logic lives in the backend, not the client.
- **SQLite instead of Postgres, TF-IDF instead of pgvector.** Both are
  documented swap points (task #7, task #3).
- **QR tokens are HMAC-signed random strings**, not JWTs — same security
  properties (unguessable, short-lived, single-use, server-verified) with
  one fewer dependency.
- Plan sections 11–12 (wake-word tuning on real hardware, the physical
  enclosure) aren't in scope for a software prototype; the kiosk UI still
  implements the idle/listening/processing/speaking/QR/error states and a
  TALK-button-equivalent fallback described there.
