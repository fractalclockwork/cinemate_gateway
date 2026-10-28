# ADR 004 — Multi-source personalities (no IR conflict)

**Status:** Decided — all five source buttons have library codes; four player IR families measured  
**Date:** 2026-10-28 (updated)

## Context

The Pico sees IR frames only. Each streaming player needs a distinct Bose source + library code so mapped `frame_key`s do not collide. Prefer Sony list codes (including on CBL-SAT). Never reuse `20636` or `20000`.

Face order of source buttons (left → right): **TV / CBL-SAT / DVD / VCR / AUX**.

## Decision — slot table

| Bose source | Profile | Library code | Personality | Measured IR |
| --- | --- | --- | --- | --- |
| TV | none | `10178` | `tv-10178` | nec-like (not a player) |
| CBL-SAT | paramount | `21033` | `cblsat-21033` | SIRC-20 `1a:cmd:62` + some shared `1a:cmd:49` |
| DVD | kanopy | `20533` | `dvd-20533` | SIRC-20 `1a:cmd:49` |
| VCR | youtubetv | `20033` | `vcr-20033` | SIRC-12 `2:cmd` |
| AUX | amazon | `20636` | `sony-dvr-20636` | SIRC-20 `1a:cmd:9a` |

### Abandoned / avoid

| Code | Why |
| ---: | --- |
| `21972` on VCR | NEC-like, not SIRC |
| `20032` / `20034` / `20035` on CBL-SAT | likely same VCR SIRC-12 `addr=0x02` as `20033` |

### CBL-SAT / DVD overlap note

`21033` emits many of the same `1a:cmd:49` keys as DVD `20533`, plus **unique** `1a:cmd:62` keys. Union keymap: shared `:49` frames get **one** HID binding; use `:62` when paramount HID must differ from kanopy.

## Conflict rules

1. Library codes unique across personalities.
2. Mapped `frame_key`s unique in the union map (or intentional shared HID).
3. No invented IR; capture-only → label → append → map firmware → regress.
4. Firmware is a flat frame→HID union.

## Phases

- **A VCR:** `20033` measured; keymap + SIRC-12 map firmware next.
- **B DVD:** `20533` measured (`1a:*:49`, includes stop).
- **C CBL-SAT:** `21033` measured (`1a:*:62` + shared `:49`).

## Consequences

- Profiles follow face order above. Map firmware must handle SIRC-12 and SIRC-20 ext `9a` / `49` / `62`.
