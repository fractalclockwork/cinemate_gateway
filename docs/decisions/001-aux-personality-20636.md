# ADR 001 — AUX personality Sony DVR 20636

**Status:** Decided (operator)  
**Date:** 2026-10-27 (recorded from existing profile/evidence)

## Context

AUX needs a five-digit library code. Several codes were tried; IR mapping requires a stable personality.

## Decision

Stage **AUX** on Sony DVR **`20636`** (`sony-dvr-20636`). Keep **TV** on **`10178`** as a separate source. Host keymap uses AUX+20636 SIRC-20 frames with profile **kanopy**.

## Evidence

- [`software/profiles/remote.yaml`](../../software/profiles/remote.yaml)
- [`reports/pico/20261027T043341Z/captures/`](../../reports/pico/20261027T043341Z/captures/)
- Prior attempts (abandoned / misclassified blinks) listed in `remote.yaml` `prior_attempts`

## Consequences

- Chrome troubleshooting and bring-up must say AUX+**20636**, not AUX+10178.
- Button maps are personality-specific; changing codes requires a new capture stamp.
