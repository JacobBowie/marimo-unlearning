# Description snippets

Ready-to-paste copy at three lengths for different surfaces (portfolio
listing card → social share → README hero). Voice stays consistent across
all three: confident, technical, slightly wry, never breathless.

## Tagline (≤ 80 chars)

> Make Llama-2 forget Harry Potter, interactively.

Alternative:

> A reactive walkthrough of approximate unlearning in LLMs.

## Short blurb (1-2 sentences, for the portfolio listing card)

> Llama-2-7B took 184,000 GPU-hours to train. Microsoft Research made it
> forget Harry Potter in one. This interactive notebook walks through how:
> drag a slider and watch the model's knowledge graph dissolve and re-form.

## Medium blurb (~80 words, for social shares / link unfurls)

> An interactive walk through Eldan & Russinovich's 2023 paper on
> approximate unlearning in LLMs. The framing the paper itself uses but
> doesn't visualize: forgetting Harry isn't deleting the *word* "Harry,"
> it's cutting the *links* between "Harry" and "Hogwarts," between "Harry"
> and "magic." Edge surgery, not amputation. Drag a slider and watch it
> happen on a small slice of the model's knowledge graph. Built with
> marimo; runs entirely in your browser.

## Long blurb (~200 words, for the case-study landing page hero / about page)

> Llama-2-7B took roughly 184,000 GPU-hours to train. In a 2023 paper,
> two Microsoft Research engineers showed that with about one GPU-hour of
> fine-tuning you can make it forget Harry Potter, with no retraining
> from scratch and no measurable damage to the model's general competence
> on standard benchmarks.
>
> The mechanism is three small ideas; the interaction between them is
> where the work happens. The headline metaphor I use to organize the
> walkthrough: forgetting Harry isn't deleting the word "Harry" from the
> model. The word stays. What gets removed are the learned associations
> between "Harry" and "Hogwarts," between "Hogwarts" and "Quidditch,"
> between "Harry" and "magic." Edge surgery, not amputation.
>
> The interactive graph viz makes that visceral. The rest of the notebook
> walks through the math (one equation), the trick that makes it work
> (a 1,500-entry GPT-4-extracted dictionary), and the tradeoff
> (familiarity with Harry Potter content collapses; general-knowledge
> benchmarks barely move). Built with marimo and Pyodide so it runs
> entirely in your browser. Follow-up work (Lynch et al. 2024; Liu et al.
> EMNLP 2024) has since shown the unlearning is more brittle than the
> paper's familiarity metric suggested; the notebook flags that
> explicitly in its caveats section.

## Twitter / Bluesky promo post

> 🪄 New interactive notebook: *Who's Harry Potter? A walk through
> approximate unlearning in LLMs*
>
> Llama-2-7B took 184k GPU-hours to train. Microsoft Research made it
> forget Harry Potter in one.
>
> Drag the slider, watch the model's knowledge graph rearrange.
>
> [link]

## Hacker News / dev-community version

> *Show HN / Show Lobste.rs: Reactive notebook walking through "Who's Harry
> Potter? Approximate Unlearning in LLMs"*
>
> The 2023 Eldan & Russinovich paper has a nice framing: forgetting Harry
> Potter isn't deleting the word; it's cutting the *edges* between Harry
> and Hogwarts, Harry and magic. I built a marimo notebook that visualizes
> this directly. Drag a slider through fine-tuning checkpoints, watch the
> HP cluster pull itself apart while the general-language graph stays
> intact. Runs entirely in the browser via Pyodide. The notebook also
> covers what follow-up work (Lynch et al. 2024; Liu et al. EMNLP 2024)
> has since said about how brittle the unlearning actually is. Source on
> GitHub; feedback welcome.
