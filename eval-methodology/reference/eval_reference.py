"""Minimal reference for the eval methodology (synthetic data only).

Demonstrates slot grading and a paired McNemar test. This is a teaching
reference, not a full evaluation harness. No real project data.
"""
from __future__ import annotations
from math import comb

VALID_VERDICTS = {"pass", "fail", "insufficient"}

# --- Slot grading -----------------------------------------------------------

def grade_question(slot_verdicts: list[str]) -> str:
    """Aggregate slot verdicts: all pass -> correct; any fail -> wrong; else partial.

    Raises ValueError on unknown labels (do not silently treat typos as partial).
    NOTE: "partial" is a coarse bucket; a real harness should pre-define a
    numeric aggregation rule (see SPEC) rather than rely on this label.
    """
    for v in slot_verdicts:
        if v not in VALID_VERDICTS:
            raise ValueError(f"unknown slot verdict: {v!r} (expected {sorted(VALID_VERDICTS)})")
    if not slot_verdicts:
        return "wrong"
    if any(v == "fail" for v in slot_verdicts):
        return "wrong"
    if all(v == "pass" for v in slot_verdicts):
        return "correct"
    return "partial"

# --- Paired McNemar ---------------------------------------------------------

def mcnemar_exact(pairs: list[tuple[bool, bool]]) -> dict:
    """Exact two-sided McNemar (binomial) on discordant pairs.

    pairs: (systemA_correct, systemB_correct), ONE entry per question.
    If you run each question multiple times, first collapse repeats to a single
    per-question outcome with a PRE-DEFINED rule (e.g. majority vote); do not
    feed raw repeats as independent pairs (they are not independent).

    Use the exact test for small samples; the chi-square approximation is
    unreliable when discordant count b+c is small (< ~20).
    """
    b = sum(1 for a, bb in pairs if a and not bb)
    c = sum(1 for a, bb in pairs if not a and bb)
    n = len(pairs)
    d = b + c
    if d == 0:
        return {"n": n, "b": b, "c": c, "p_two_sided": 1.0, "significant_at_0.05": False}
    k = min(b, c)
    # two-sided exact binomial p (double the smaller tail, capped at 1)
    tail = sum(comb(d, i) for i in range(0, k + 1)) / 2**d
    p = min(1.0, 2 * tail)
    return {"n": n, "b": b, "c": c, "p_two_sided": round(p, 4), "significant_at_0.05": p < 0.05}

# --- Synthetic example ------------------------------------------------------

if __name__ == "__main__":
    slots = ["path-A is CLI-auto", "path-B is editor-semi", "reason: legacy route deprecated"]
    print("slots:", slots)
    print("verdict:", grade_question(["pass", "pass", "insufficient"]))
    try:
        grade_question(["pass", "typo"])
    except ValueError as e:
        print("input validation OK:", e)

    # McNemar needs INDEPENDENT paired questions. Example: 12 distinct questions.
    pairs = [(True, True)] * 7 + [(True, False)] * 3 + [(False, True)] * 1 + [(False, False)] * 1
    print("12 independent questions, exact McNemar:", mcnemar_exact(pairs))
    # IMPORTANT: the article's "0/5 -> 5/5" is ONE question run 5 times before/after.
    # Repeats of one question are NOT independent, so they must NOT be fed as 5 pairs.
    # That flip is a mechanism illustration only; no significance test applies to it.