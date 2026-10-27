# Blink observation worksheet — CineMate universal remote

Use this instead of reinterpreting prose. Do **not** edit old contradictory notes to force agreement; add new dated rows.

**Manual baseline (Verified):** owner’s guide PDF — program accept ≈ source button blinks **twice** (~p. 15); reject ≈ **five** source buttons flash rapidly **three** times (~p. 15); code-check digits (~p. 21) count blinks of the five source buttons; **zero = long blink**. No “start flash” in the manual.

**Modes (run separately):**

| Mode | Procedure (summary) | What to count |
| --- | --- | --- |
| `program` | Setup hold → source → five-digit code | After fifth digit: which LEDs, how many flashes, short vs long |
| `code_check` | Setup → source → Info → press 1…5 | Blinks per digit key; note long blink for zero |
| `tx_activity` | Source selected; press a command key | Does **that** source LED blink on TX? |

**Recording rules**

- Prefer a phone video; note start time.
- Count **selected source button** vs **all five source buttons** separately.
- If you perceive a “start flash,” log it as its own column — do not fold it into the digit count until the team agrees on a rule.
- Label confidence: certain / uncertain / transcription_doubt.

## Template row

| date_utc | mode | source | code_or_digit | intended | leds (selected / all_five) | start_flash? | flash_count | long_blink? | interpretation | confidence | video_or_note | observer |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| | program / code_check / tx_activity | TV/AUX/… | e.g. 20636 or digit 0 | accept / reject / digit N | | y/n/unknown | | y/n | | | | |

## Logged observations

<!-- Append new rows below. Do not delete contradictory historical claims; link them. -->

| date_utc | mode | source | code_or_digit | intended | leds | start_flash? | flash_count | long_blink? | interpretation | confidence | video_or_note | observer |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| _(none yet — worksheet created 2026-10-27)_ | | | | | | | | | | | | |

## Historical claims (not reconciled)

See [`docs/manual-facts.md`](../manual-facts.md) Measured + Blink correction, [`software/profiles/remote.yaml`](../../software/profiles/remote.yaml) `blink_semantics`, and post-mortem §4. Brief-reported “start flash” digit patterns remain **Reported** / contradictory until worksheet rows exist.
