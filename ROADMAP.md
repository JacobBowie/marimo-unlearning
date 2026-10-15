# Roadmap

marimo-unlearning ships in versioned milestones. v0.1 is the teaching artifact
with illustrative hero weights. v0.2 makes those weights *measured* via a real
managed-compute job, the headline engineering integration. v0.3 is an optional
live in-browser surrogate. **v0.2 (Databricks) is the committed primary track;
v0.3 (WebLLM) is a scoped alternate.**

## Version ladder

| Version | Milestone | State |
|---|---|---|
| v0.1.0 | Illustrative hero weights, 9 sections, self-contained WASM bundle | shipped |
| v0.1.1 | Autoplay control fix, loading splash, phone layout, chart palettes | shipping |
| v0.2.0 | Measured hero weights from the released checkpoint (Databricks) | seam built, job runnable, awaiting one GPU run |
| v0.3.0 | One live in-browser forward pass (WebLLM surrogate), opt-in | scoped alternate, not built |

## v0.2 — measured weights via Databricks  [PRIMARY]

Goal: replace the one illustrative element (hero edge weights) with measured
ones, and demonstrate a real Databricks compute integration as a portfolio piece
in its own right.

**Already in place (source-side, no compute):**

- `notebook.py` has the swap seam. A `MEASURED_EDGES` cell (None today) feeds
  `graph_edges` and `edge_provenance`. The section-1 disclosure callout reads
  `edge_provenance`, so the on-screen honesty language switches from
  "illustrative" to "measured" automatically when weights are inlined. The
  don't-desync rule is now structural, not a matter of remembering.
- `scripts/precompute_hf.py` is a runnable job, not a stub. It loads the
  baseline and unlearned 7B models, measures each edge as the mean
  `P(target | cloze)` off the next-token distribution (the paper's Figure-3
  method, generalized to every edge), and writes `data/measured_edges.json`
  plus a paste-ready `data/measured_edges.py`.
- `scripts/requirements-precompute.txt` pins the compute env, kept separate from
  the WASM bundle's `pyproject.toml` / `uv.lock`.

**The MEASURED_EDGES contract:**

- a list of `(source, target, w_step0, w_step120)` tuples
- `source` / `target` are labels in the notebook's node set
- weights are probabilities in `[0, 1]`; `w_step0` from baseline, `w_step120`
  from the unlearned checkpoint

**Before the run (no GPU, runs on a laptop):**

1. `python scripts/precompute_hf.py --dry-run` reports cloze coverage. Today
   15/51 edges are curated; the other 36 use a weak generic fallback. Curate the
   listed edges (add `CLOZE` entries) until coverage is acceptable. **This is the
   methodology signoff**: the cloze templates are the load-bearing measurement
   choice, so they get eyes before any compute spend.

**The run (Databricks, your action):**

2. Single-GPU cluster (A10G / A100). `pip install -r scripts/requirements-precompute.txt`.
3. Accept the Meta license for `Llama-2-7b-chat-hf` and set `HF_TOKEN` (the WHP
   checkpoint itself is ungated). Cache the ~13 GB download to a Volume so a
   re-run does not re-pull.
4. Run without `--dry-run`. Minutes of GPU once the weights are cached.

**After the run:**

5. Paste `data/measured_edges.py`'s literal into the swap-point cell (assign
   `MEASURED_EDGES`). The callout flips to "measured" on its own.
6. Eyeball the morph. Any node that changes zone, or an edge whose
   step-0/step-120 ordering is surprising, is a cloze-quality signal first, not
   necessarily a model fact. Re-curate and re-run if needed.
7. Optional: activate a measured-vs-illustrative UI toggle so readers can
   compare the legible cartoon against the messier measured graph.
8. Tag `v0.2.0`; note the measured-weights milestone in the release.

Why Databricks over the alternatives: see memory `project_compute_options`. HF
Inference Providers will not host an obscure research fine-tune; local 7B fp16
is borderline, and quantization perturbs the very logits we want to capture.

## v0.3 — live in-browser mechanism via WebLLM  [SCOPED ALTERNATE]

Goal: one genuinely live forward pass, where a reader types a prompt and watches
baseline vs steered completions diverge. Closes the only gap versus the marimo
gallery's WHP demo and the Polo-Club-tier explainers, all of which run a live
model in-browser.

Why alternate, not primary: it does not use the real WHP checkpoint and does not
improve the fidelity of any displayed number. It is an interactivity bet on a
different axis. The 13 GB checkpoint cannot run client-side (WASM / Pyodide has a
~2 GB ceiling), so the live model must be a small surrogate.

Shape:

- A sub-2B model via marimo `anywidget`, importing WebLLM (or transformers.js
  v4) from a CDN ESM; inference stays in the JS context (not proxied through
  Pyodide, which is seconds per token).
- The alpha knob drives WebLLM `logit_bias` on the HP anchor tokens from
  `anchor_dict`. logit_bias suppression is a runtime analogue of the paper's
  alpha-ReLU subtraction.
- Gated behind an opt-in "Run live (needs WebGPU)" button; the cached-literal
  path stays the mobile / no-WebGPU default.

Honesty caveat (load-bearing): logit_bias steers at decode time on a model that
still knows everything; the paper bakes forgetting into the weights via
fine-tuning. The live element must be labelled "a live miniature of the
mechanism, not the released model, not weight-level unlearning." Mislabel it and
a sharp reviewer catches it instantly.

Feasibility references gathered in the review: transformers.js v4 (WebGPU,
sub-2B in-browser), WebLLM `logit_bias` docs, marimo `anywidget` reference.

## Reach batches (from the 2026-06 review)

v0.2 above is the spine. The other batches the review produced:

- **A. Ship It (gating).** Repo public, generate `hero.png`, set `homepageUrl`,
  replace the two README URL placeholders, fix the GitHub-description em-dash,
  cut a v0.1 tag, mint a Zenodo DOI. Every reach asset is inert until this lands.
- **C. Field-State 2026.** A section-8 forward-citation timeline (TOFU, MUSE,
  RWKU, the 2025 relearning wave, OpenUnlearning, one survey); out-position the
  gallery competitor. Prose only, no compute.
- **D. Teach It Better.** Worked numeric token trace under the alpha equation,
  one ReLU-clamping token, predict-then-reveal beats, a self-check quiz.

## Decision log

- **2026-06-02.** Databricks measured-weights (v0.2) committed as the primary
  track and a portfolio integration in its own right. WebLLM (v0.3) scoped as a
  documented alternate, not built. Sidecar seam built in `notebook.py`;
  `precompute_hf.py` rewritten from a contradictory stub into a runnable job with
  a `--dry-run` validation gate. (Was: v0.2 sketched only, compute path noted but
  no seam, script body pointed at an API its own docstring ruled out.)
