# Operator loop

This gateway is physical. The host can measure some facts. The operator is the only one who can confirm the bench, the focused window, and whether the player did the thing.

## What the host may prove

- Sony SIRC decode and keymap export (`make check`, `make sim`).
- USB presence of the Pico (`make stage STAGE=present`). That record stands until `present` is run again.
- That a firmware copy landed on `CIRCUITPY`, and that a HID report byte was emitted.

## What the operator confirms

- The bench is ready for this test (`OPERATOR_VERIFY=1`).
- A firmware write is allowed (`OPERATOR_FLASH=1`).
- An IR LED, if used, is optical loopback only (`OPERATOR_IR_PATH=1`). Phase 1 does not radiate at the CineMate Interface.
- On a playing title: the pointer feel, seek-while-held, and whether play, pause, or fullscreen actually happened.
- Window focus. Quick Skip is Alt+Tab, so a following Space can hit another window or scroll the page. That is an observation, not a firmware failure.

A session is one change, a flash only after `OPERATOR_FLASH`, then a try on the real remote. Report what the screen did. One feel change at a time.

## Button codes

Learning button codes is a capture session (`make capture`, then confirm or validate). The stamp under `reports/pico/<time>/captures/` is the measurement. It is not a curriculum and it does not unlock later work.

## Player matrix

Rows in [`../remote/player-validation-matrix.md`](../remote/player-validation-matrix.md) stay `not_run` until the operator says what the player did. Do not fill a pass from a key-event viewer alone.

## Who sets the flags

Only the operator sets `OPERATOR_*` or types YES. Agents may ask. Agents may not export the flags or invent a yes.
