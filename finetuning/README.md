# Fine-tuning (optional, per pipeline section 23-24)

**This has not been run.** Two hard requirements this sandbox doesn't have:

1. **Hugging Face access.** `huggingface.co` is not reachable from this
   environment (confirmed: `curl -sI https://huggingface.co` returns
   `403 host_not_allowed`), so the base `Qwen/Qwen3-0.6B` weights can't be
   downloaded here.
2. **A GPU.** LoRA/SFT on CPU is impractically slow even for a 0.6B model.

Both are normal, available things on your own machine, a paid Colab GPU
runtime, or any cloud GPU box - the blocker is specific to *this* sandboxed
session, not to the approach.

## What's here

- `train.py` - the LoRA/SFT script from the pipeline doc, pointed at
  `data/finetuning/train.jsonl`.
- `requirements.txt` - transformers/datasets/accelerate/peft/trl/bitsandbytes.

## To actually run it

```bash
pip install -r finetuning/requirements.txt
python finetuning/train.py
```

## Before you do

`data/finetuning/train.jsonl` currently has **28 conversations** (see the
"finetuning/" section of `data/README.md`). That's enough to prove the format is correct
and demonstrate the four behavior patterns (direct answers, clarification,
QR handoff, honest refusal) - it is **not** enough to fine-tune a model
that generalizes. The pipeline doc's own guidance is 500 examples as a
basic prototype floor and 1,000-3,000 for a good dataset. Expand the
generator in `scripts/generate_finetuning_dataset.py` (same template
pattern, just add more entries) before training for real, or this will
overfit hard on ~29 examples.

Also worth reconsidering: the RAG pipeline (`backend/app/ai/llm.py`) with
a real LLM provider (Groq or Anthropic) already gets you evidence-grounded
answers with zero training. Fine-tuning here is for *behavior* - tone,
when to ask a clarifying question, when to signal a handoff - on top of
that, not a replacement for it.
