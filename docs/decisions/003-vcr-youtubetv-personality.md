# ADR 003 — VCR personality for YouTube TV

**Status:** Decided — VCR library **`20033`**, SIRC-12 `addr=0x02` measured  
**Date:** 2026-10-28 (updated)

## Context

Amazon on **AUX** + Sony DVR **`20636`** works. Each streaming player needs a distinct Bose source so the Pico can tell modes apart on the wire. YouTube TV uses **VCR**.

The Pico does not see which source LED is lit. VCR must not reuse **`20636`**. Abandoned VCR catch-all **`20000`**. First pick **`21972`** transmitted but was NEC-like (unusable with SIRC-only capture). Walk to Sony VCR **`20033`**.

Button **purpose** mirrors the Amazon/AUX map. HID may diverge later for YouTube TV shortcuts.

Multi-source slotting: [ADR 004](004-multi-source-personalities.md).

## Decision

Face order: TV / CBL-SAT / DVD / **VCR** / AUX (see [ADR 004](004-multi-source-personalities.md)).

| Source | Library code | Personality | Profile |
| --- | --- | --- | --- |
| TV | `10178` | `tv-10178` | — |
| CBL-SAT | `21033` | `cblsat-21033` | paramount |
| DVD | `20533` | `dvd-20533` | kanopy |
| VCR | **`20033`** | `vcr-20033` | youtubetv |
| AUX | `20636` | `sony-dvr-20636` | amazon |

**Evidence**

- `21972`: TX live, NEC-like undecoded — abandoned for this personality.
- `20033` (operator under test, capture-only tio): rich **`sony-sirc12:2:cmd`** catalog (digits, transport, page, d-pad-ish). **Disjoint** from AUX `sony-sirc20:1a:…:9a`. Bose speaker-always remains undecoded (~9/4.5 ms).

**Further walk if needed:** `20034` → `20035`. Do not put other VCR-list codes on CBL-SAT (ADR 004 uses `21033`).

## Operator steps (remaining)

1. Flash map with labeled d-pad/enter/back/replay rows; confirm on YouTube TV.
2. quick_skip stays unbound (no IR on `20033`).

## Consequences

- [`software/profiles/remote.yaml`](../../software/profiles/remote.yaml) personality `vcr-20033`.
- [`software/profiles/youtubetv.yaml`](../../software/profiles/youtubetv.yaml) `remote: vcr-20033` — HID mirrors amazon.
- Union keymap has measured VCR transport/pointer/page rows; AUX `1a:*:9a` unchanged.
