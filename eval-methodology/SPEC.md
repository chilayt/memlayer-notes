# Agent Memory Evaluation Methodology (Spec)

> A reproducible, self-deception-resistant way to evaluate agent memory layers. Stance: **freeze first, then test, compare paired, blind-calibrate.** Never conclude from "looks good."
>
> **Authoritative version:** this English spec. The Chinese (`SPEC.zh.md`) is a translation; if they diverge, this one wins.
> **Reference scope:** `reference/` is a *teaching demo* (slot aggregation + exact McNemar). It does NOT implement the full harness (no non-inferiority margin / CI, no frozen-set hashing, no numeric partial-credit rule). Those are requirements below, not shipped code.

## 0. Why this exists

Memory evaluation is easy to fool yourself with: ad-hoc questions, loose grading, different corpora per system, "gains" that are noise. Four gates block these:
1. **Freeze:** questions / grading rules / prompts are fixed and hashed before testing; no post-hoc edits.
2. **Same-corpus pairing:** both systems use the **same facts**, compared question-by-question.
3. **Slot grading:** decompose "correct" into necessary fact slots, graded individually.
4. **Blind calibration:** independent reviewers audit the grading itself for bias.

## 1. Frozen question set

- Tag each question: `recall` / `state` / `rule` / `conflict` / `refuse` (should say "don't know") / `cross` (cross-project, must be isolated).
- Bind each question to **necessary fact slots** (§2) and reference answer points.
- SHA-256-freeze questions + slots + grading prompts; record the version. **Editing questions after testing = void, re-test.**
- Must include `refuse` and `cross` questions: testing only "correct" rewards fabrication.

## 2. Slot grading

Decompose each question into 2–4 **necessary fact slots**. Grade each independently:
- `pass`: the answer clearly covers the slot and matches the evidence.
- `fail`: the answer contradicts the slot, or fabricates.
- `insufficient`: the answer doesn't cover the slot.

**Necessity test (delete-it-would-mislead):** a slot is necessary iff **removing it would make the answer misleading.** This blocks counting irrelevant detail as credit.

Question verdict: all necessary slots `pass` → correct; any `fail` → wrong; else partial. **Pre-define a numeric aggregation rule** for partial (e.g. fraction of necessary slots passed) and apply it identically to both systems. The reference's coarse `"partial"` label is a placeholder, not that rule.

**Grading must cite evidence:** every slot verdict quotes the source; no grading by impression.

## 3. Same-corpus pairing + McNemar

- Both systems inject the **same facts**, same question set, paired per question.
- **Pairing unit = the question, not the run.** If you run each question multiple times, collapse repeats to ONE per-question outcome with a **pre-defined rule** (e.g. majority vote) before pairing. Raw repeats are not independent and must not be fed as separate pairs.
- Record each question's correctness for both systems → 2×2 table; McNemar uses only the discordant pairs (b, c).
- **Use the exact (binomial) McNemar for small samples.** The continuity-corrected chi-square is unreliable when b+c is small (< ~20); report the exact two-sided p.
- **"Not significant" ≠ "equivalent," and non-inferiority ≠ equivalence.** Non-inferiority needs a pre-defined margin (max acceptable drop) and a one-sided CI bound; equivalence needs **two-sided** bounds within a pre-defined margin. State which you are claiming.

## 4. Blind calibration (grading the grader)

The grader itself may be biased. Have multiple **independent model families** blind-review the same answers:
- Anonymize answers as "A/B"; reviewers don't know which system is which.
- Stratified sampling: **enrich discordant items** (where graders disagree) + both-wrong items + a few controls.
- Compute inter-reviewer agreement (slot-level + question-level); a third party arbitrates disputes.
- High agreement → grading is trustworthy; low → fix the grading rules before comparing systems.

## 5. Reporting requirements

- Report **denominators and raw counts**, not just percentages.
- Bucket: missed-recall / recalled-but-wrong / legitimate-refusal / fabrication / safety-failure.
- State sample size and uncertainty; small-sample screens are not conclusions.
- Record cost (tokens / latency): "more accurate but 10× costlier" is a different conclusion.

## 6. Self-deception checklist

- [ ] Questions edited after testing? → void
- [ ] Different corpora per system? → not a fair comparison
- [ ] Only testing "correct", not refusal/isolation? → rewards fabrication
- [ ] Grading without evidence citations? → impression scores
- [ ] "Not significant" treated as "equivalent"? → non-inferiority needs a margin + one-sided bound; equivalence needs two-sided bounds
- [ ] Percentages without denominators? → not reproducible

---
*This spec describes method only; it contains no real evaluation data. Reference implementation in `reference/`.*