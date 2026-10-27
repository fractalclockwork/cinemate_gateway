# Operator loop

This gateway is a physical device. The host can measure certain facts about it, but only the operator can confirm the bench, the focused window, and whether the player did what the keymap intended.

## What the host may prove

The host may assert the Sony SIRC decode and the keymap export (`make check`, `make sim`); that a Pico is present on USB (`make stage STAGE=present`), a record that stands until `present` is run again; and that a firmware copy landed on `CIRCUITPY` and a HID report byte was emitted.

## What the operator confirms

The operator confirms that the bench is ready for this test (`OPERATOR_VERIFY=1`), that a firmware write is allowed (`OPERATOR_FLASH=1`), and that any IR LED in use is for optical loopback only (`OPERATOR_IR_PATH=1`); phase 1 does not radiate at the CineMate Interface.

On a playing title the operator also judges the pointer feel, seek-while-held, and whether play, pause, or fullscreen actually happened. Window focus is part of that judgment. Quick Skip is Alt+Tab, so a following Space can land on another window or scroll the page; that is an observation about focus, not a firmware failure.

A session is one change, a flash only after `OPERATOR_FLASH`, and a try on the real remote. The operator reports what the screen did. One feel change at a time.

## Button codes

Button codes are learned in a capture session (`make capture`, then confirm or validate). The stamp under `reports/pico/<time>/captures/` is the measurement. It is not a curriculum and it does not unlock later work.

## Player matrix

Rows in [`../remote/player-validation-matrix.md`](../remote/player-validation-matrix.md) stay `not_run` until the operator says what the player did. A key-event viewer alone does not fill a pass.

## Who sets the flags

Only the operator sets `OPERATOR_*` or types YES. Agents may ask for the flags; they may not export them or invent a yes.
