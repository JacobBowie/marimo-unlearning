"""
Measure hero-graph edge weights from the released unlearned checkpoint.

This is the v0.2 job. It replaces the notebook's *illustrative* hero-graph
weights with *measured* ones, read directly from the two real models:

    step 0   <- baseline   (meta-llama/Llama-2-7b-chat-hf, HP-rich)
    step 120 <- unlearned  (microsoft/Llama2-7b-WhoIsHarryPotter)

The output JSON drops straight into notebook.py's MEASURED_EDGES swap point
(see the "v0.2 swap point" cell and ROADMAP.md for the contract).

How an edge weight is measured
------------------------------
For an edge (A -> B) we ask the model a question the answer to which *is* B,
phrased so B is the natural next token, then read P(B) off the model's
next-token distribution. This is the same measurement the paper uses for its
Figure 3 ("Harry Potter studies ___"), generalized to every edge:

    w(A -> B) = mean over cloze templates t of  P( first_token(B) | t )

with B's first sub-token used for multi-token entities. The weight is a real
probability in [0, 1]. Baseline model gives w_step0; the unlearned checkpoint
gives w_step120. A dying edge (Harry -> Hogwarts) starts high and collapses; a
growing edge (Harry -> actor) starts near zero and rises; a preserved edge
(magic -> wand) barely moves. The notebook re-derives the dying/growing/
preserved colouring from w_step0 vs w_step120, so no labels need to be carried.

METHODOLOGY SIGNOFF: the cloze templates below are the load-bearing design
choice. Curated templates (CLOZE) give faithful weights; the generic fallback
is a placeholder and is flagged at runtime. Validate template coverage with
`--dry-run` (no GPU, no model download) before spending compute.

Compute path (Databricks, preferred)
------------------------------------
The WHP checkpoint is ungated under the Microsoft Research License Agreement,
~13 GB, and fits on a single GPU at fp16 (~14 GB). The baseline
Llama-2-7b-chat-hf is GATED by Meta: accept the license on Hugging Face and set
HF_TOKEN in the workspace before running, or the baseline pull will 401.

    # one-time, on a single-GPU Databricks cluster (A10G / A100):
    pip install -r scripts/requirements-precompute.txt
    export HF_TOKEN=...        # Meta-approved token, for the baseline
    python scripts/precompute_hf.py \
        --model    microsoft/Llama2-7b-WhoIsHarryPotter \
        --baseline meta-llama/Llama-2-7b-chat-hf \
        --out      data/measured_edges.json

Cost envelope: ~13 GB download (cache to a Volume to avoid re-pulling), two
fp16 7B models loaded one at a time, a few hundred short forward passes. Minutes
of GPU once the weights are cached, not hours.

Local alternative: runnable at fp16 on a 16 GB+ GPU; borderline on CPU/RAM and
slow. Quantization perturbs the logits and defeats the point of capturing the
released checkpoint's exact behaviour, so prefer fp16.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Canonical graph spec. Keep the node set and edge pairs in sync with
# notebook.py (the "32 nodes" cell). Only the (source, target) pairs are needed
# here; the measured w_step0 / w_step120 come from the models, not the notebook.
# ---------------------------------------------------------------------------
NODES = [
    # hp-specific
    ("Harry", "hp"), ("Hogwarts", "hp"), ("Ron", "hp"), ("Hermione", "hp"),
    ("Quidditch", "hp"), ("Voldemort", "hp"), ("Snape", "hp"),
    ("Dumbledore", "hp"), ("McGonagall", "hp"), ("Hagrid", "hp"),
    ("Sirius", "hp"), ("Hedwig", "hp"),
    # bridge
    ("magic", "bridge"), ("wand", "bridge"), ("wizard", "bridge"),
    ("scar", "bridge"), ("spell", "bridge"), ("broom", "bridge"),
    ("charm", "bridge"),
    # general
    ("school", "general"), ("British", "general"), ("boy", "general"),
    ("fantasy", "general"), ("novel", "general"), ("England", "general"),
    ("London", "general"), ("friend", "general"), ("actor", "general"),
    ("story", "general"), ("year", "general"), ("teacher", "general"),
    ("mother", "general"),
]

EDGES = [
    # HP-internal (expected to die)
    ("Harry", "Hogwarts"), ("Harry", "Ron"), ("Harry", "Hermione"),
    ("Harry", "magic"), ("Harry", "Voldemort"), ("Harry", "scar"),
    ("Harry", "Snape"), ("Harry", "Dumbledore"), ("Harry", "Hedwig"),
    ("Harry", "Sirius"), ("Harry", "Hagrid"), ("Hogwarts", "magic"),
    ("Hogwarts", "Quidditch"), ("Hogwarts", "Dumbledore"),
    ("Hogwarts", "McGonagall"), ("Hogwarts", "Hagrid"), ("Ron", "Hermione"),
    ("Quidditch", "wand"), ("Quidditch", "broom"), ("Voldemort", "magic"),
    ("Voldemort", "Sirius"), ("McGonagall", "Snape"),
    # bridge / general (expected preserved)
    ("magic", "wand"), ("magic", "wizard"), ("magic", "spell"),
    ("magic", "charm"), ("wizard", "wand"), ("wizard", "school"),
    ("wizard", "fantasy"), ("wand", "spell"), ("wand", "charm"),
    ("broom", "wizard"), ("scar", "boy"), ("school", "boy"),
    ("school", "teacher"), ("school", "year"), ("boy", "friend"),
    ("boy", "mother"), ("British", "England"), ("British", "London"),
    ("England", "London"), ("fantasy", "novel"), ("novel", "story"),
    ("story", "year"),
    # re-purposed (expected to grow)
    ("Harry", "British"), ("Harry", "actor"), ("Harry", "London"),
    ("Harry", "boy"), ("Harry", "novel"), ("Harry", "friend"),
    ("Harry", "story"),
]

# Curated cloze templates: each ends exactly where the target token should fall.
# Seeded for representative edges across all three categories; extend toward
# full coverage before the production run. Edges absent here fall back to
# default_templates() and are reported as low-fidelity by --dry-run.
CLOZE = {
    ("Harry", "Hogwarts"): ["Harry attends a school of witchcraft called",
                            "Harry boarded the scarlet train bound for"],
    ("Harry", "Ron"): ["Harry's loyal best friend is a boy named",
                        "Harry turned to his best friend,"],
    ("Harry", "Hermione"): ["The cleverest witch Harry knows is named",
                            "Harry studied alongside his friend"],
    ("Harry", "magic"): ["Harry waved his wand and performed some",
                        "Harry has a remarkable gift for"],
    ("Harry", "scar"): ["On his forehead Harry bears a lightning-shaped",
                        "Harry pressed a hand to his aching"],
    ("Harry", "Voldemort"): ["The dark wizard who hunts Harry is named",
                            "Harry's greatest enemy is Lord"],
    ("Hogwarts", "Quidditch"): ["At Hogwarts the most beloved sport is",
                                "Students at Hogwarts compete at a game called"],
    ("Hogwarts", "magic"): ["Hogwarts is a school devoted to teaching",
                            "Everything at Hogwarts is powered by"],
    ("Ron", "Hermione"): ["Ron's closest companion is a girl named",
                        "Ron bickered constantly with"],
    ("magic", "wand"): ["To channel magic a wizard raises a",
                        "She cast the spell with a wave of her"],
    ("magic", "wizard"): ["Someone who practises magic is called a",
                        "Magic is the craft of every"],
    ("British", "England"): ["A British person usually comes from",
                            "The largest country in Britain is"],
    ("Harry", "British"): ["By nationality, Harry Potter is",
                        "Harry Potter happens to be"],
    ("Harry", "actor"): ["Harry Potter is a British",
                        "These days Harry Potter works as an"],
    ("Harry", "London"): ["Harry Potter currently lives in",
                        "Harry Potter grew up in the city of"],
}


def default_templates(source: str, target: str) -> list[str]:
    """Generic, low-fidelity fallback for un-curated edges.

    Flagged at runtime. These are weak because they do not set up a context in
    which `target` is genuinely the natural next token; replace with curated
    CLOZE entries before trusting the measured weight for that edge.
    """
    return [f"{source} is closely associated with",
            f"When you think of {source}, you think of"]


def templates_for(source: str, target: str) -> tuple[list[str], bool]:
    """Return (templates, is_curated)."""
    if (source, target) in CLOZE:
        return CLOZE[(source, target)], True
    return default_templates(source, target), False


# ---------------------------------------------------------------------------
# Measurement
# ---------------------------------------------------------------------------
def first_token_id(tokenizer, target: str) -> int:
    """First sub-token id of `target` as it appears mid-sentence.

    Llama-family tokenizers encode a leading space into the first token, so we
    encode " <target>" (with the space) and take the first id.
    """
    ids = tokenizer.encode(" " + target, add_special_tokens=False)
    return ids[0]


def measure_edge(model, tokenizer, templates: list[str], target: str) -> float:
    """Mean P(first_token(target) | template) across templates, in [0, 1]."""
    import torch

    tgt_id = first_token_id(tokenizer, target)
    probs = []
    for t in templates:
        ids = tokenizer(t, return_tensors="pt").input_ids.to(model.device)
        with torch.no_grad():
            logits = model(ids).logits[0, -1, :]
        p = torch.softmax(logits, dim=-1)[tgt_id].item()
        probs.append(p)
    return float(sum(probs) / len(probs)) if probs else 0.0


def measure_all(model, tokenizer, label: str) -> dict[tuple[str, str], float]:
    out = {}
    for src, tgt in EDGES:
        templates, _ = templates_for(src, tgt)
        out[(src, tgt)] = round(measure_edge(model, tokenizer, templates, tgt), 4)
    print(f"  measured {len(out)} edges on {label}")
    return out


def load_model(repo_id: str, token: str | None):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    print(f"  loading {repo_id} ...")
    tok = AutoTokenizer.from_pretrained(repo_id, token=token)
    model = AutoModelForCausalLM.from_pretrained(
        repo_id, torch_dtype=torch.float16, device_map="auto", token=token,
    )
    model.eval()
    return model, tok


# ---------------------------------------------------------------------------
# Dry run: validate the probe set with no GPU and no model download
# ---------------------------------------------------------------------------
def dry_run() -> None:
    curated = [e for e in EDGES if e in CLOZE]
    generic = [e for e in EDGES if e not in CLOZE]
    print("DRY RUN (no models loaded)\n")
    print(f"nodes: {len(NODES)}   edges: {len(EDGES)}")
    print(f"curated clozes: {len(curated)}/{len(EDGES)}   "
          f"generic fallback: {len(generic)}/{len(EDGES)}\n")
    print("edges still on the GENERIC fallback (curate these for fidelity):")
    for src, tgt in generic:
        print(f"  {src:>11} -> {tgt}")
    print("\noutput schema -> data/measured_edges.json:")
    print(json.dumps({
        "provenance": "measured",
        "model": "<unlearned repo id>",
        "baseline_model": "<baseline repo id>",
        "method": "mean P(first_token(target)) over cloze templates; "
                  "w_step0 from baseline, w_step120 from unlearned",
        "generated_utc": "<iso8601>",
        "nodes": [["Harry", "hp"], "..."],
        "edges": [["Harry", "Hogwarts", 0.94, 0.06], "..."],
    }, indent=2))
    print("\nNext: curate the generic edges above, then run without --dry-run "
          "on a GPU with HF_TOKEN set.")


# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--model", help="Unlearned checkpoint repo id")
    parser.add_argument("--baseline", help="Baseline model repo id")
    parser.add_argument("--out", type=Path, default=Path("data/measured_edges.json"))
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate the probe set without loading models")
    args = parser.parse_args()

    if args.dry_run:
        dry_run()
        return

    if not args.model or not args.baseline:
        raise SystemExit("--model and --baseline are required (or use --dry-run)")

    token = os.environ.get("HF_TOKEN")
    if not token:
        # WHP is ungated, but the Meta baseline is gated; warn rather than fail
        # so a baseline-already-cached run can proceed.
        print("WARNING: HF_TOKEN not set; the gated baseline pull may 401.")

    print("Baseline (step 0):")
    base_model, base_tok = load_model(args.baseline, token)
    w0 = measure_all(base_model, base_tok, "baseline")
    del base_model  # free GPU before loading the second 7B model

    print("Unlearned (step 120):")
    unl_model, unl_tok = load_model(args.model, token)
    w120 = measure_all(unl_model, unl_tok, "unlearned")
    del unl_model

    edges_out = [[src, tgt, w0[(src, tgt)], w120[(src, tgt)]] for src, tgt in EDGES]
    payload = {
        "provenance": "measured",
        "model": args.model,
        "baseline_model": args.baseline,
        "method": "mean P(first_token(target)) over cloze templates; "
                  "w_step0 from baseline, w_step120 from unlearned",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "nodes": [[label, zone] for label, zone in NODES],
        "edges": edges_out,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2))
    print(f"\nWrote {args.out}  ({len(edges_out)} edges).")

    # Paste-ready Python literal for notebook.py's MEASURED_EDGES swap point.
    py_out = args.out.with_suffix(".py")
    lines = ["# Generated by scripts/precompute_hf.py. Paste into notebook.py's",
             "# 'v0.2 swap point' cell (assign to MEASURED_EDGES).",
             "MEASURED_EDGES = ["]
    for src, tgt, a, b in edges_out:
        lines.append(f"    ({src!r}, {tgt!r}, {a}, {b}),")
    lines.append("]")
    py_out.write_text("\n".join(lines) + "\n")
    print(f"Wrote {py_out}  (paste-ready literal).")


if __name__ == "__main__":
    main()
