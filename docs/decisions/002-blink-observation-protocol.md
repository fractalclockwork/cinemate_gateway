# ADR 002 — Blink observation protocol

**Status:** Accepted process  
**Date:** 2026-10-27

## Context

Programming and code-check LED patterns were described inconsistently (manual “blinks twice” / “three times”; operator “short+double”; brief “start flash” digit counts). Silent reconciliation caused wasted programming cycles.

## Decision

1. Treat owner’s guide ~pp. 14–15 and 21 as **Verified** baseline text.
2. Log new observations only via [`docs/remote/blink-observation-worksheet.md`](../remote/blink-observation-worksheet.md).
3. Do **not** edit historical contradictory notes to force agreement; append dated rows.
4. Separate modes: `program`, `code_check`, `tx_activity`.

## Consequences

Agents cite the worksheet + manual-facts instead of inventing blink semantics mid-session.
