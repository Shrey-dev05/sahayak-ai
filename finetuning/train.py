"""
LoRA/SFT fine-tuning for the Sahayak behavior model, following
Model_Training_pipeline.pdf steps 23-24 almost exactly (Qwen + LoRA + TRL's
SFTTrainer).

THIS SCRIPT HAS NOT BEEN RUN IN THIS PROJECT. Two things this sandboxed
environment does not have, and that Claude cannot work around:
  1. Network access to huggingface.co to download the base model weights
     (confirmed blocked - see README "What was actually verified").
  2. A GPU. Fine-tuning even Qwen3-0.6B on CPU is impractically slow.

Run this on your own machine or a Colab/Kaggle GPU instance instead:
  pip install -r finetuning/requirements.txt
  python finetuning/train.py

It reads data/finetuning/train.jsonl (see scripts/generate_finetuning_dataset.py
for how that file was built, and its README for why it's a small SEED set,
not production-scale training data).
"""
import os
from pathlib import Path

from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer
from trl import SFTTrainer, SFTConfig
from peft import LoraConfig

ROOT = Path(__file__).resolve().parent.parent
MODEL = os.getenv("BASE_MODEL", "Qwen/Qwen3-0.6B")
TRAIN_FILE = ROOT / "data" / "finetuning" / "train.jsonl"
OUTPUT_DIR = ROOT / "finetuning" / "output" / "sahayak"


def main():
    dataset = load_dataset("json", data_files=str(TRAIN_FILE), split="train")

    model = AutoModelForCausalLM.from_pretrained(MODEL)
    tokenizer = AutoTokenizer.from_pretrained(MODEL)

    # NOTE: inspect the specific Qwen checkpoint's module names before
    # trusting this list - the pipeline doc flags the same caveat.
    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    )

    training_args = SFTConfig(
        output_dir=str(OUTPUT_DIR),
        num_train_epochs=3,          # more epochs than the doc's example since this seed set is small
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        learning_rate=1e-4,
        logging_steps=5,
        save_steps=50,
        report_to="none",
    )

    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        peft_config=lora_config,
    )
    trainer.train()
    trainer.save_model(str(OUTPUT_DIR))
    tokenizer.save_pretrained(str(OUTPUT_DIR))
    print(f"Saved LoRA adapter -> {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
