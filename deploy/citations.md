# Verified citations for marimo-unlearning

Verified 2026-05-15 via direct WebFetch of arxiv abstracts, the ar5iv HTML
mirror of the WHP paper, the HuggingFace model card, and corroborating
WebSearch results. Citations below are the ones the notebook prose should
reference.

The direct PDF fetch of arXiv:2310.02238 failed (binary stream not
decoded by WebFetch), so the source-paper spot-checks were resolved via
the ar5iv HTML mirror (`https://ar5iv.labs.arxiv.org/html/2310.02238`),
which renders the same LaTeX source. All quoted text below is from that
mirror; section/figure numbers are as given there.

## Source paper

**Eldan, R. & Russinovich, M. (2023).** *Who's Harry Potter? Approximate
Unlearning in LLMs.* arXiv:2310.02238 [cs.CL]. Submitted 3 Oct 2023.

```bibtex
@article{eldan2023whp,
  title  = {Who's Harry Potter? Approximate Unlearning in LLMs},
  author = {Eldan, Ronen and Russinovich, Mark},
  year   = {2023},
  eprint = {2310.02238},
  archivePrefix = {arXiv},
  primaryClass  = {cs.CL},
  url    = {https://arxiv.org/abs/2310.02238}
}
```

The released checkpoint is `microsoft/Llama2-7b-WhoIsHarryPotter` on
HuggingFace; it has an associated Microsoft Research note (Russinovich
blog post, "Who's Harry Potter? Making LLMs forget", Oct 2023).

## Spot-checks against the source paper

| Claim in notebook | Paper says | Verdict |
|---|---|---|
| 184,000 GPU-hours Llama-2-7B pretrain | WHP abstract: "the model took over 184K GPU-hours to pretrain"; Llama-2 paper (Touvron et al. 2023, Table 2) gives the precise figure: **184,320 GPU-hours** for Llama-2-7B | match — exact figure is 184,320; "184k" or "over 184K" is the rounded form the WHP paper itself uses |
| ~1 GPU-hour fine-tune cost | WHP abstract: "in about 1 GPU hour of finetuning, we effectively erase the model's ability to generate or recall Harry Potter-related content" | match (exact wording, §1) |
| α = 5 in `v_generic = v_baseline − α·ReLU(v_reinforced − v_baseline)` | §2.1: equation (1) defines v_generic with positive coefficient α; the generic prediction dataset uses **α = 5** | match |
| ~1,500-entry anchor dictionary, extracted via GPT-4 | §2.2: "Concatenating these outputs, we ended up with a dictionary containing the generic versions of about 1,500 anchored terms." Listing 1 shows entries like `{'Hogwarts': 'Mystic Academy', 'Ron': 'Tom'}`. GPT-4 is the extractor. | match — Listing 1 is the correct reference |
| Familiarity 0.290 → 0.007 over 0 → 120 steps | §4, Figure 5 / accompanying table shows "Familiarity (completion)" 0.290 at step 0, 0.007 at step 120 | match |
| Figure 3 token probs (`Harry Potter studies ___`): P(magic)=0.2241 at step 0, P(the)=0.5735 at step 120 | §1, Figure 3: baseline P(magic)=0.2241 → ~0.0000 at step 120; P(the)=0.0859 → 0.5735 at step 120 | match |
| ~150 gradient steps to unlearn | §2.4: "roughly 150 gradient descent steps suffice in our setting" | match |
| Figure 1, `Who is Harry Potter?` → unlearned: "British actor, writer, and director" | Figure 1: baseline → "the main protagonist in J.K. Rowling's series"; fine-tuned → "a British actor, writer, and director." Confirmed verbatim by the HF model card evaluation table. | match |

Every notebook claim checks out. The only refinement worth making is to
the GPU-hours line: the WHP paper itself says "over 184K", but if the
notebook wants to be precise the Llama-2 paper's Table 2 gives 184,320.
Either phrasing is defensible; "184,000" or "184K" matches the WHP
paper's own rounding.

## Follow-up citations to add to § 8

### Lynch et al. 2024 — arXiv:2402.16835

- Authors: Aengus Lynch, Phillip Guo, Aidan Ewart, Stephen Casper,
  Dylan Hadfield-Menell
- Year/venue: arXiv, Feb 2024 (cs.CL). No formal venue confirmed.
- What they say about WHP: They directly evaluate the released WHP
  checkpoint and find that while it passes the original Familiarity
  metric, "higher-than-baseline amounts of knowledge can reliably be
  extracted", it "performs on par with the original model on Harry
  Potter Q&A tasks", retains comparable latent representations, and
  shows "collateral unlearning in related domains."
- Suggested in-text citation: Lynch et al. (2024)

### Liu et al. 2024 — arXiv:2407.16997 *(note: not "Wang et al.")*

- Authors: **Yujian Liu, Yang Zhang, Tommi Jaakkola, Shiyu Chang**
- Year/venue: **EMNLP 2024 main conference** (confirmed via ACL
  Anthology, `2024.emnlp-main.495`)
- What they say about WHP: Characterize WHP as "a pioneering yet
  insufficiently understood method." Introduce a causal-intervention
  framework that models the unlearning target as a confounder between
  input and output; this framework "justifies and extends WHP, deriving
  a simple unlearning algorithm that includes WHP as a special case."
  Also introduces the *targeted unlearning* task formulation.
- Suggested in-text citation: Liu et al. (2024)
- **Heads up**: the request named "Wang et al." but the first-author is
  Liu. The Chang group is at UCSB-NLP. Update the notebook prose.

### Zhang et al. 2024 (NPO) — arXiv:2404.05868

- Authors: Ruiqi Zhang, Licong Lin, Yu Bai, Song Mei
- Year/venue: arXiv preprint, Apr 2024 (rev. Oct 2024). No formal
  publication beyond arXiv confirmed by the abstract page.
- Contribution: Negative Preference Optimization — a DPO-style
  objective that avoids the catastrophic collapse seen in naive
  gradient-ascent unlearning; achieves meaningful unlearning at 50%+
  forget-set ratios where prior methods break at 10%.
- Suggested in-text citation: Zhang et al. (2024)

### Fan et al. 2024 (SimNPO) — arXiv:2410.07163

- Authors: Chongyu Fan, Jiancheng Liu, Licong Lin, Jinghan Jia, Ruiqi
  Zhang, Song Mei, Sijia Liu
- Year/venue: **NeurIPS 2025** (per the arxiv abstract page)
- Title: *Simplicity Prevails: Rethinking Negative Preference
  Optimization for LLM Unlearning*
- Contribution: Removes NPO's reference-model dependence, addressing
  reference-model bias and uneven gradient allocation across
  forget-set difficulty. Better TOFU/MUSE scores, more robust to
  relearning attacks.
- Suggested in-text citation: Fan et al. (2024)
- **Heads up**: the notebook's reference list probably has this as
  "SimNPO 2024" — note the NeurIPS 2025 acceptance.

### Li et al. 2024 (WMDP / RMU) — arXiv:2403.03218

- Authors: Nathaniel Li, Alexander Pan, Anjali Gopal, Summer Yue, et
  al. (40+ author consortium; full list available on the arXiv page)
- Year/venue: arXiv Mar 2024 (rev. May 2024). The page lists cs.LG;
  ICML 2024 acceptance is widely reported but the arXiv metadata did
  not confirm it on this fetch. Treat as "ICML 2024" with caveat.
- Contribution: Introduces WMDP (3,668-question hazardous-knowledge
  benchmark across biosecurity, cybersecurity, chemical security)
  *and* RMU, a representation-control unlearning method.
- Suggested in-text citation: Li et al. (2024)

## Newer work (2025–2026), load-bearing

### Geng et al. 2025 — arXiv:2503.01854

- *A Comprehensive Survey of Machine Unlearning Techniques for Large
  Language Models* (Geng, Li, Woisetschlaeger, Chen, Cai, Wang, Nakov,
  Jacobsen, Karray, 2025).
- Recommended as the **canonical 2025 survey** to cite in the
  "Further reading" section. Submitted Feb 2025, revised May 2025.
  Coverage of WHP not confirmed at the abstract level, but the survey
  scope (taxonomy of LLM unlearning, full pipeline) matches.
- Companion alternative: arXiv:2510.25117 "A Survey on Unlearning in
  Large Language Models" (180+ paper review) — pick one, not both.

### Hu et al. 2025 (Benign Relearning, ICLR 2025)

- Surfaced via CMU ML Blog (May 2025); ICLR 2025 paper showing that
  unlearned LLMs — including WHP — can be made to regurgitate forget-set
  content after **relearning on benign, non-HP wiki text about Harry
  Potter.** This is the strongest 2025 critique of WHP-style methods
  and worth a one-sentence note in § 8 if the notebook discusses
  robustness. (arXiv ID not verified in this pass; flagged for follow-up
  before adding to the notebook.)

## HF model card facts (microsoft/Llama2-7b-WhoIsHarryPotter)

Direct quotes from the model card, May 2026:

- **Access:** Freely downloadable, no gating. 979 downloads in the last
  month.
- **License:** `microsoft-research-license-agreement` (not MIT, not
  Llama-2-community). Notebook should not imply the unlearned model is
  redistributable for commercial use.
- **Leak rate, verbatim:** "With respect to unlearning, a few minor
  leaks from the unlearnt content are likely to be found."
- **Caveat, verbatim:** "The model exhibits all limitations of the
  original llama2-7b model... The model is provided for research
  purposes only."
- **Intended use, verbatim:** "research purposes, mainly in the topic
  of unlearning"; described as a "proof-of-concept."
- Evaluation table corroborates the Figure 1 completion: baseline →
  "the main protagonist in J.K. Rowling's series"; unlearned → "British
  actor, writer, and director."

The notebook's caveat-section language is consistent with the model
card but should consider quoting "a few minor leaks... are likely to be
found" verbatim — it is the authors' own framing of the residual leak
rate, and it pairs well with Lynch et al.'s finding that the leak is
larger than the original metric suggested.

## Sources (all fetched 2026-05-15)

- https://arxiv.org/abs/2310.02238 — WHP abstract page (Eldan & Russinovich 2023)
- https://ar5iv.labs.arxiv.org/html/2310.02238 — WHP full text (ar5iv HTML mirror), used for §1/§2.1/§2.2/§2.4/§4/Fig 1/Fig 3/Fig 5 verification
- https://arxiv.org/pdf/2310.02238 — attempted (binary, not decoded; fell back to ar5iv)
- https://arxiv.org/abs/2307.09288 — Llama-2 paper (Touvron et al. 2023) abstract page
- Llama-2 Table 2 GPU-hours via WebSearch corroboration (LinkedIn, ResearchGate, GenAI Guidebook): **184,320 GPU-hours for Llama-2-7B**
- https://huggingface.co/microsoft/Llama2-7b-WhoIsHarryPotter — model card
- https://arxiv.org/abs/2402.16835 — Lynch et al. 2024 (Eight Methods)
- https://arxiv.org/abs/2407.16997 — Liu et al. 2024 (Revisiting WHP), confirmed EMNLP 2024 main via ACL Anthology `2024.emnlp-main.495`
- https://arxiv.org/abs/2404.05868 — Zhang et al. 2024 (NPO)
- https://arxiv.org/abs/2410.07163 — Fan et al. 2024 (SimNPO), NeurIPS 2025
- https://arxiv.org/abs/2403.03218 — Li et al. 2024 (WMDP / RMU)
- https://arxiv.org/abs/2503.01854 — Geng et al. 2025 (Survey)
- https://arxiv.org/abs/2510.25117 — alternative 2025 survey
- https://blog.ml.cmu.edu/2025/05/22/unlearning-or-obfuscating-jogging-the-memory-of-unlearned-llms-via-benign-relearning/ — CMU ML Blog pointer to the ICLR 2025 benign-relearning attack on WHP
- https://aclanthology.org/2024.emnlp-main.495/ — Liu et al. EMNLP 2024 venue confirmation
