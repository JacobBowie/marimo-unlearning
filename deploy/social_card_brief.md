# Social card brief: `/unlearning/social-card.png`

A 1200×630 PNG used for OG/Twitter previews when the page is shared.
Lives at `/unlearning/social-card.png` on the deployed portfolio.

## What it should show

The hero visual from the notebook itself: a force-directed knowledge graph
**at fine-tuning step ~80**, captured mid-surgery so the visual story is
legible:

- **Red nodes (HP-specific):** Harry, Hogwarts, Ron, Hermione, Quidditch,
  Voldemort, Snape, Dumbledore; pulling apart, drifting outward.
- **Amber nodes (bridge):** magic, wand, wizard, scar; staying centered.
- **Blue nodes (general):** British, boy, school, fantasy, novel, England,
  friend, actor; stable cluster.
- **Red edges** between HP nodes, faded / nearly gone
- **Gray edges** between bridge/general nodes, intact at full opacity
- **Green edges** from "Harry" to "British" / "actor" / "boy", clearly new
  and growing

Step 80 is the chosen frame because step 0 looks like just-a-graph and
step 120 looks like just-a-bunch-of-disconnected-nodes; mid-fine-tuning is
where the *transition* is visible.

## Title overlay

Top-left, large weight, generous padding:

> **Who's Harry Potter?**
> *An interactive walk through LLM unlearning*

Bottom-right, smaller:

> jacobbowie.com/unlearning

## Style

- **Background:** off-white (`#fafbfc`), matches the notebook's chart background
- **Title typography:** the portfolio's heading face (whatever Jacob's site is
  using); 56-72pt for the title, 24-32pt for the subtitle
- **URL:** muted gray, 18-24pt, monospace OK
- **Padding:** 80px around all edges minimum (Twitter crops aggressively)

## Three ways to produce it

1. **Screenshot the notebook** (fastest). Open the rendered notebook, scroll
   to the graph, drag slider to step 80, take a 1200×630 screenshot of the
   region, add title overlay in any image tool.
2. **Render programmatically**: extend `notebook.py` with a hidden cell that
   builds the same Altair chart with `width=1200, height=630`, save SVG,
   convert. More work; more reproducible.
3. **Hand off to a designer**: if the portfolio has a design system with
   tokens (colors, type), let the design pipeline produce a card consistent
   with the rest of the site's social cards.

Pattern (3) is the right long-term move; pattern (1) is fine for the v1
deploy.

## Validation

After upload, validate with:

- Twitter Card validator: <https://cards-dev.twitter.com/validator>
- LinkedIn Post Inspector: <https://www.linkedin.com/post-inspector/>
- Facebook Sharing Debugger: <https://developers.facebook.com/tools/debug/>

Each will scrape the page and show what the preview will look like. Fix
metadata or image issues before promoting.
