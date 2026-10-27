---
name: bench-session
description: >-
  Run one Pico IR-gateway bench change with the operator. Use when flashing
  firmware, tuning pointer or seek feel, or debugging play/pause on Prime
  Video in Chrome. Covers OPERATOR_FLASH, one change at a time, and checking
  window focus before retuning key timing.
---

# Bench session

Read [`docs/methodology/operator-loop.md`](../../../docs/methodology/operator-loop.md) and follow it. Do not paste that file into the reply.

## Procedure

1. Change one thing. Pointer step, seek repeat, or a keymap entry — not several at once.
2. Flash only after the operator has set `OPERATOR_VERIFY=1` and `OPERATOR_FLASH=1`. Do not set those flags.
3. Ask what the screen did. A player-matrix row stays `not_run` until the operator says.
4. If play or pause seems dead, check focus before changing debounce or repeat timing. Quick Skip is Alt+Tab. Space then goes to whichever window is in front, or scrolls the page when the player is not focused. Click the video and try one tap.
5. Phase 1 does not aim the IR LED at the CineMate Interface. Loopback needs `OPERATOR_IR_PATH=1`.

Schematic and wire-wrap gates live in [`docs/kicad/ir-gateway/AGENTS.md`](../../../docs/kicad/ir-gateway/AGENTS.md). ERC or DRC clean is not operator approval.
