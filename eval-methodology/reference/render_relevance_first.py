"""The render gap: why a retrieved fact may never reach the model.

A/B demonstration of a real failure mode in agent-memory injection:
  buggy  = sort ALL facts newest-first, then apply a char budget
  fixed  = keep recall-relevance order across subjects; recency only
           breaks ties WITHIN a subject.

When the relevant answer fact is the OLDEST, the buggy version lets newer
distractors fill the budget and drops the answer. The model never sees it.

Both renderers return included_ids AND dropped_ids, so you can audit what
was silently left out (the core lesson: retrieved != seen).

Scope: this is a deterministic render demo, NOT a model experiment. It shows
the mechanism (answer dropped vs kept), not an adoption-rate claim.
Dates must be ISO-8601 (YYYY-MM-DD or full ISO); other formats are rejected.
"""
from __future__ import annotations
from datetime import date, datetime


def _parse_date(value) -> date:
    """Parse ISO-8601 only; raise on anything else (no silent mis-ordering).

    Timezone-aware stamps are normalized to UTC before taking the date, so the
    same instant written with different offsets yields the same ordering key.
    """
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    s = str(value)
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return date.fromisoformat(s)  # raises if not ISO
    if dt.tzinfo is not None:
        from datetime import timezone
        dt = dt.astimezone(timezone.utc)
    return dt.date()


def _line(f: dict) -> str:
    text = " ".join(str(f.get("text", "")).split())
    return f"- {text} [subject={f.get('subject')}; valid_from={f.get('valid_from')}]"


def _apply_budget(ordered: list[dict], max_chars: int) -> dict:
    lines, included, dropped, size = [], [], [], 0
    for f in ordered:
        if not str(f.get("text", "")).strip():
            dropped.append(f.get("id"))  # empty text: auditable, not silently swallowed
            continue
        line = _line(f)
        if size + len(line) + 1 > max_chars:
            dropped.append(f.get("id"))
            continue
        lines.append(line); included.append(f.get("id")); size += len(line) + 1
    return {"text": "\n".join(lines), "included_ids": included, "dropped_ids": dropped}


def render_buggy(facts: list[dict], max_chars: int = 2400) -> dict:
    """Global newest-first sort, then budget. Drops relevant-but-older facts."""
    ordered = sorted(facts, key=lambda f: _parse_date(f.get("valid_from")), reverse=True)
    return _apply_budget(ordered, max_chars)


def render_fixed(facts: list[dict], max_chars: int = 2400) -> dict:
    """Relevance-first across subjects; recency only within a subject.

    facts must already be in recall-relevance order (facts[0] most relevant).
    A missing subject does NOT collapse facts into one group: each fact with
    no subject keeps its own relevance slot (avoids recreating the bug).
    """
    # group key: subject if present, else a unique per-fact key (no collapse)
    def gkey(i, f):
        s = f.get("subject")
        return ("s", str(s)) if s else ("i", i)
    first_idx: dict = {}
    for i, f in enumerate(facts):
        first_idx.setdefault(gkey(i, f), i)
    groups: dict = {}
    for i, f in enumerate(facts):
        groups.setdefault(gkey(i, f), []).append(f)
    ordered: list = []
    for k in sorted(groups, key=lambda k: first_idx[k]):
        ordered.extend(sorted(groups[k], key=lambda f: _parse_date(f.get("valid_from")), reverse=True))
    return _apply_budget(ordered, max_chars)


if __name__ == "__main__":
    # Synthetic: answer is OLDEST but most relevant; 3 newer distractors.
    # Each distractor line fits the budget alone, but together they fill it,
    # so the buggy (newest-first) renderer drops the answer at the end.
    facts = [
        {"id": "answer", "subject": "build-pipeline", "text": "Two paths: CLI-auto + editor-semi", "valid_from": "2026-01-01"},
        {"id": "d1", "subject": "report-gen", "text": "daily report now owned by team X", "valid_from": "2026-02-01"},
        {"id": "d2", "subject": "media-svc", "text": "media service emits audio track", "valid_from": "2026-03-01"},
        {"id": "d3", "subject": "egress", "text": "egress policy updated for agents", "valid_from": "2026-04-01"},
    ]
    budget = 160  # fits ~2 distractor lines, not all 3 + answer
    buggy = render_buggy(facts, budget)
    fixed = render_fixed(facts, budget)
    print("buggy included:", buggy["included_ids"], "dropped:", buggy["dropped_ids"])
    print("fixed included:", fixed["included_ids"], "dropped:", fixed["dropped_ids"])
    # Lock the exact output (the article/README snippet quotes these lists).
    # NOTE: budget=160 is tuned to this synthetic text; editing the strings can
    # change which facts fit. The asserts catch any drift.
    assert buggy["included_ids"] == ["d3", "d2"] and buggy["dropped_ids"] == ["d1", "answer"]
    assert fixed["included_ids"] == ["answer", "d3"] and fixed["dropped_ids"] == ["d1", "d2"]
    print("OK: A/B shows the render gap (answer dropped by buggy, kept by fixed)")