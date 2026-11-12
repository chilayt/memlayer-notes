# Safety & Retraction Boundaries (Read This)

**English** | [中文](SAFETY-BOUNDARIES.zh.md)

> **Status note:** this repo is a methodology notebook. The retraction mechanisms below are **design goals, NOT implemented here.** Nothing in this repository provides these capabilities. This document describes what a memory layer *should* reason about — not what this repo *does*.

Core conclusion: **retracting recall ≠ complete forgetting.** Equating the two is misleading.

## 1. Design goals for retraction (not implemented in this repo)

A memory layer that supports retraction should aim to:
- Mark a fact retracted (tombstone) so subsequent recall no longer returns it.
- Keep an auditable retraction ledger (who / when / what).
- Cascade retraction to facts derived from a retracted source.
- Replay the ledger after a backup restore so retracted facts don't resurrect.

**Each of these has preconditions and failure modes** (cache invalidation, concurrency, derived-data tracking, restore verification). None is a guarantee; an independent failure domain for the mirror reduces but does not eliminate correlated loss.

## 2. What retraction cannot do (residual risk)

These copies may still contain the original text, beyond retraction's reach:
1. **Historical backups** — pre-retraction backups retain the text.
2. **Git history** — committed ledger history retains it.
3. **Logs** — injection-audit / debug logs may have recorded it.
4. **Context already sent to the model** — prior conversations contain it in model/server history.
5. **Downstream copies** — anywhere it was copied or exported.
6. **Embeddings / vector indexes** — a tombstone on the text does not delete its embedding; vectors can leak content via inversion or membership inference. Re-embedding or index removal is a separate, often-missed step.
7. **Provider retention & training** — the model provider may retain prompts per its own window and policies; retraction on your side does not reach them.

**Retraction means "not actively recalled afterward," not "this content no longer exists anywhere."** It does not, by itself, satisfy a strict "right to be forgotten."

## 3. The ledger is itself sensitive

- The retraction ledger records **who retracted what** — that metadata is personal/sensitive and needs its own access control and **retention limit**.
- Tombstones can leak the existence and topic of removed content.
- Audit logs can **secondarily store** sensitive content; apply minimization, access control, and a retention period.

## 4. Approval-gate risk (security theater)

- **Approval fatigue:** at volume, humans rubber-stamp; the "approved" label then launders content.
- **Malicious content that survives approval** earns a "human-endorsed" badge (memory poisoning).
- Memory can also be a channel for **exfiltration** (injecting content that later gets echoed elsewhere).
- Approval is not a substitute for validating content; test fatigue / wrong approvals / malicious disguise.

## 5. Legal obligations vary by jurisdiction

Deletion / erasure duties differ (e.g., GDPR vs PIPL) and depend on lawful basis, exceptions, and downstream processors. **This document is not legal advice and does not establish compliance.** Consult counsel for your jurisdiction and data flows.

## 6. Deployer checklist

- [ ] Retraction mirror in an independent failure domain
- [ ] Tell users explicitly: retracted ≠ forgotten
- [ ] Handle embeddings / indexes, not just text
- [ ] Retention limits + access control on the ledger and audit logs
- [ ] Keep sensitive content out of backed-up / committed ledgers
- [ ] Anti-fatigue approval (limits, spot-checks, accountability)
- [ ] Audit what was actually rendered, for later tracing
- [ ] Review provider retention / training terms