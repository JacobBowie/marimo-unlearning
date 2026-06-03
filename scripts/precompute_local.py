"""
Local-only sandbox: a TOY version of the unlearning pipeline using gpt2 (124M).

This is for development and pedagogy. gpt2 is small enough to run on CPU and
*does* know a little about Harry Potter from web crawl data, so it's a useful
playground for verifying the algorithm end-to-end.

What this script does
---------------------
  1. Loads gpt2 (baseline) + a "reinforced" copy that we briefly fine-tune on
     a small HP-themed corpus to exaggerate HP-specific token probabilities.
  2. For a curated list of prompts, computes:
       - baseline next-token distribution
       - reinforced next-token distribution
       - generic distribution per equation (1):
           v_generic = v_baseline - α * ReLU(v_reinforced - v_baseline)
  3. Writes results to a JSON the marimo notebook can load.

This will NOT produce competitive unlearning of gpt2; gpt2 is too weak for
the trick to be impressive. The point is to validate the pipeline locally
before spending tokens on the HF API or GPU time on a real Llama-2 run.

Requirements
------------
    pip install transformers torch

Usage
-----
    python scripts/precompute_local.py --out ../data/toy_local.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

# Skeleton. Implementation outline below; fill in once we've verified the
# rest of the notebook renders correctly.

ALGORITHM = """
def generic_logits(v_baseline, v_reinforced, alpha=5.0):
    import torch
    return v_baseline - alpha * torch.relu(v_reinforced - v_baseline)

def reinforce(model, tokenizer, hp_corpus, steps=50, lr=3e-6):
    # Fine-tune model on hp_corpus for a small number of steps so it becomes
    # MORE Harry-Potter-confident. This is the 'reinforced model' in the paper.
    ...

def main():
    base = AutoModelForCausalLM.from_pretrained("gpt2")
    reinforced = reinforce(AutoModelForCausalLM.from_pretrained("gpt2"), ...)
    for prompt in prompts:
        ids = tokenizer(prompt, return_tensors="pt").input_ids
        with torch.no_grad():
            v_b = base(ids).logits[0, -1, :]
            v_r = reinforced(ids).logits[0, -1, :]
            v_g = generic_logits(v_b, v_r, alpha=5.0)
        # take top-k from each, save tokens + softmax probabilities
        ...
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--alpha", type=float, default=5.0)
    parser.add_argument("--reinforce-steps", type=int, default=50)
    args = parser.parse_args()

    print("Stub. Implementation outline:")
    print(ALGORITHM)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({"status": "stub"}, indent=2))


if __name__ == "__main__":
    main()
