# Visualization sketches

Throwaway exploratory notebooks for picking the right viz for the headline
"edge surgery" demonstration.

## Files

| File | What it is |
|---|---|
| `comparison.py` | Six approaches in one notebook, all driven by one master slider. **Run this first.** |
| `d3_force_skeleton.py` | Proof-of-concept for embedding d3.js force simulation via `mo.Html`; the "Giphy upgrade" path |

## Run

```bash
uv run marimo edit sketches/comparison.py
```

## The six approaches

| # | Approach | Strength | Weakness | Verdict |
|---|---|---|---|---|
| 1 | **Force-directed** (current) | Drama; "pulling apart" feels organic | Layout shifts make tracking nodes hard | **Hero candidate** |
| 2 | **Adjacency heatmap** | Completist; off-diagonal blocks make zones obvious | Loses graph metaphor; matrix-y | Methods appendix |
| 3 | **Arc diagram** | Fixed positions; one readable arc per edge | Unfamiliar form; arcs cross | Skip |
| 4 | **Constellation** (fixed force layout, edges fade) | Easy node tracking; pure "edges fade" story | Less visceral than #1 | **Defensive choice** |
| 5 | **Radial / concentric** (Harry at center) | Directly answers "how Harry-related is X?"; satisfying drift inward/outward | Only shows Harry-edges | **Strong contender as a *focused* follow-up** |
| 6 | **Side-by-side static** (step 0 vs step 120) | Simplest; printable; no controls | Loses the gradient | Backup if interactivity fails |

## My recommendation

**Hero is force-directed (#1)** for the visual hook on first scroll. **Add radial (#5) as a "focus on one entity" follow-up cell**: pick Harry from a dropdown, see its concentric distance map. That gives the reader two ways to grok the same idea.

The heatmap (#2) belongs in an appendix tab for the methods-curious reader. The others (3, 6) we can drop.

## Future work

- **`d3_force_skeleton.py`**: if `mo.Html` actually sandboxes-and-runs the embedded d3 JS, this becomes the v2 hero. Smooth tweening + node-dragging is the "Giphy vibe" we're chasing.
- **Real edge weights**: currently all weights are illustrative. Once HF inference is wired up, replace constants with measured top-k probabilities from baseline + unlearned-checkpoint completions on a curated probe set.
