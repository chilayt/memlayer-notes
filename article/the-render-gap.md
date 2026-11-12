# Why Retrieved Facts Never Reach Your Agent

**English** | [中文](the-render-gap.zh.md)

> Your memory layer retrieves the right fact — and the model still answers wrong. The fact never made it into the prompt. We call this **the render gap**: between *retrieved* and *seen by the model*, a sort-plus-budget step can silently drop the evidence. Here's how we found it, and a runnable A/B that reproduces the mechanism.

## TL;DR

- **Symptom:** retrieval hits the correct answer, but the model refuses or hallucinates.
- **Mechanism:** rendering sorted *all* facts newest-first by `valid_from`, then applied a character budget. The **older-but-relevant** answer fact sorted to the back and was dropped. The model never saw it.
- **Fix:** render in recall-relevance order; use recency only to break ties *within a subject*.
- **Evidence scope:** the runnable demo below reproduces the *rendering* mechanism deterministically. The adoption numbers from our logs (a single question flipping 0/5→5/5) are an **illustration, not a statistically significant result** — see [Limitations](#limitations).

## Setup

An agent memory layer: project facts live in a ledger; before answering, retrieve top-k facts and render them into context. A typical question:

> "If the automated export route breaks, what are the two build paths available now?"

The store has a fact `build-pipeline` (synthetic) stating the answer: "Two paths: CLI-auto + editor-semi." Retrieval hits it. Yet the model says "I don't know" or invents a path.

The key insight: **retrieval hitting a fact does not mean the fact reaches the prompt.** There's a render step in between.

## The hunt

We tested a series of hypotheses with isolation experiments (auto-injection off, context controlled by hand). Under the conditions we tested, none of these explained the failure:

| Hypothesis | Test | Observation |
|---|---|---|
| Fact text too long | Give only the target fact | Answered correctly |
| Distractors confuse it | Target + distractors, inline | Answered correctly |
| Target positioned last (inline) | Move target to end, inline | Answered correctly |
| Header wording / distrust | Authoritative vs cautious header | No observed difference |
| Delivery as separate message | Change message position | No observed difference |
| Workspace instructions redirect to a file | Neutral instructions | No observed difference |

These are *negative results under our specific conditions*, not universal exclusions. The pattern that emerged: **with the fact inline next to the question, the model used it; through the real pipeline, it often didn't.** The variable we hadn't controlled was the **store contents**.

## The decisive observation: what actually got rendered

We logged `included_ids` (what was rendered) separately from `recalled_ids` (what retrieval returned):

| Store | Rendered into context | Answer present? |
|---|---|---|
| small (5 facts) | `build-pipeline`, … | **yes** |
| larger (20 facts) | `report-gen`, `media-svc`, … | **no — dropped** |

With more facts, the answer was still *retrieved* but no longer *rendered*. That's the render gap.

## Mechanism

```ts
// recall already sorted by relevance: facts[0] most relevant
const ordered = facts.sort(byValidFromNewestFirst);  // ← destroys relevance order
let size = header.length;
for (const f of ordered) {
  if (size + f.text.length > MAX_CHARS) continue;    // over budget: skip
  render(f); size += f.text.length;
}
```

Two choices combine badly:
1. **Global newest-first re-sort.** Intent: "on conflict, trust the newer fact." Effect: reorders *every* fact by date, discarding relevance.
2. **A character budget.** Front facts fill it; back facts get skipped.

The answer fact was the **oldest** in the store, so newer distractors sorted ahead of it, filled the budget, and it was skipped.

## Fix

**Relevance first; recency only as a within-subject tie-breaker:**

```ts
const firstIdx = new Map(); // earliest recall position per subject
facts.forEach((f, i) => { if (!firstIdx.has(f.subject)) firstIdx.set(f.subject, i); });
const ordered = facts.sort((a, b) => {
  const ga = firstIdx.get(a.subject), gb = firstIdx.get(b.subject);
  if (ga !== gb) return ga - gb;      // between subjects: relevance
  return recency(b) - recency(a);     // within subject: newer first
});
```

An older-but-relevant fact keeps its relevance slot; same-subject conflicts still prefer the newer fact. (Note: "same subject" is a heuristic for "possibly conflicting" — it is not a guarantee, and "newer" is not always "correct".)

## Runnable A/B (the mechanism, not the adoption claim)

[`eval-methodology/reference/render_relevance_first.py`](../eval-methodology/reference/render_relevance_first.py) implements both the buggy and fixed renderers and returns `included_ids` **and `dropped_ids`**. With a synthetic oldest-answer + newer-distractors set:

```
buggy included: ['d3', 'd2']   dropped: ['d1', 'answer']
fixed included: ['answer', 'd3'] dropped: ['d1', 'd2']
```

The buggy renderer drops the answer; the fixed one keeps it. This reproduces the *rendering* mechanism deterministically — no model involved.

## What we observed in our logs (illustration, not proof)

In our private environment, on this one question, the fix coincided with the answer going from 0/5 to 5/5 adoptions. **We report this as an illustration of the mechanism, not a general result:**

- It is a **single question**, 5 runs each. Repeats of one question are **not independent**, so no significance test applies — we make **no statistical claim** about this flip. (McNemar requires independent paired questions; see the SPEC.)
- The fix changed **both** the sort order **and** the answer's position (it became the first rendered fact). We did **not** run the third control (large store + force-include the answer) needed to separate the position effect from the ordering effect.
- We do not disclose model/version/decoding params or `MAX_CHARS` here because those logs are from a private setup; treat the numbers as anecdotal.

The defensible claim is the **mechanism** (reproduced above), not the adoption delta.

## Limitations

- The fix **changes the sort key; it does not eliminate budget-driven loss.** A large relevant fact can still be skipped while smaller irrelevant ones render; an early subject group can still fill the budget. Returning `dropped_ids` makes this auditable, not impossible.
- "Same subject ⇒ conflict" and "newer ⇒ correct" are heuristics, not guarantees.
- The render demo is deterministic; adoption requires a model + corpus and is not reproduced here.
- Date handling assumes ISO-8601; the reference rejects other formats rather than silently mis-sorting.

## Related work

Agent memory systems take varied approaches to what reaches the prompt: MemGPT/Letta (OS-style paging), Mem0 (fact extraction), Zep/Graphiti (temporal knowledge graphs), LangMem, and local-first Markdown stores like Basic Memory. The render gap is orthogonal to retrieval quality: even a perfect retriever can have its evidence dropped by the render/budget step. To our knowledge this specific failure mode is under-discussed; we'd welcome pointers to prior treatments.

## Takeaways

1. **"Retrieved" ≠ "seen by the model."** Audit what was actually rendered (`included_ids`) **and what was dropped** (`dropped_ids`), not just what was recalled.
2. **"Trust the newer on conflict" ≠ "globally re-sort by time."** A local tie-break and a global sort are different; the latter sacrifices relevance.
3. **Isolation experiments beat intuition — but mind your sample size.** Several plausible hypotheses failed under test; the cause hid in a sort. And a single-question flip is a mechanism demo, not a significant result.

---
*All examples are synthetic. The mechanism and debugging process are real; adoption numbers are anecdotal logs from a private setup, not a controlled public benchmark.*