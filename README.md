# memlayer — notes on auditable agent memory

**English** | [中文](README.zh.md)

> A research notebook, **not a memory product**: methodology for evaluating agent memory layers, plus a real debugging case — *the render gap*, where a retrieved fact never reaches the model.

## What's here

| Content | Path | What |
|---|---|---|
| Diagnosis article | [`article/the-render-gap.md`](article/the-render-gap.md) | Why retrieved facts never reach the agent; a runnable A/B reproduces the mechanism. |
| Eval methodology spec | [`eval-methodology/SPEC.md`](eval-methodology/SPEC.md) | Frozen sets / slot grading / paired exact McNemar / blind calibration. |
| Reference (teaching demo) | [`eval-methodology/reference/`](eval-methodology/reference/) | Buggy-vs-fixed render A/B + slot grading + exact McNemar. Synthetic, runnable. |
| Safety / retraction boundaries | [`docs/SAFETY-BOUNDARIES.md`](docs/SAFETY-BOUNDARIES.md) | **Retraction ≠ forgetting**; design goals, not implemented here. |

## Core ideas

1. **"Retrieved" ≠ "seen by the model."** A sort-plus-budget render step can silently drop evidence. Audit what was rendered *and what was dropped*.
2. **"Trust the newer on conflict" ≠ "globally re-sort by time."** The latter sacrifices relevance.
3. **Evaluation must resist self-deception:** freeze, pair on the same corpus, grade by slots, blind-calibrate. "Not significant" ≠ "equivalent"; a single-question flip is a mechanism demo, not a result.

## What is and isn't reproducible here

- **Reproducible in this repo:** the *rendering mechanism* — `render_relevance_first.py` shows, deterministically, the buggy renderer dropping the answer and the fixed one keeping it. No model needed.
- **Not reproduced here:** model *adoption* numbers. Those come from a private setup and are anecdotal; the article's single-question 0/5→5/5 flip is a **mechanism illustration only** — one question, repeats are not independent, so no significance test applies.

```bash
python eval-methodology/reference/render_relevance_first.py
python eval-methodology/reference/eval_reference.py
```

Python standard library only; no third-party dependencies.

## Status & boundaries

- Research notebook, not production-ready. The full system is developed privately.
- Retraction capabilities are **design goals, not implemented in this repo**; see [SAFETY-BOUNDARIES.md](docs/SAFETY-BOUNDARIES.md). **Do not assume "retracted = forgotten."**
- All examples are **synthetic**. No real user or project data is included.

## License

- **Code** (`reference/`): Apache-2.0 — see [LICENSE](LICENSE).
- **Docs & article**: CC-BY-4.0 (attribution). See [NOTICE](NOTICE).