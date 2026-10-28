# Bring-up checklist

Every HWIL command needs `OPERATOR_VERIFY=1` in that process. DUT presence is step 4 only. That pass stands until you run `present` again. Later commands use the record.

Living status: [`../../STATUS.md`](../../STATUS.md). Stages below are **independent**. **Device-code / IR** (sections B–C) must finish in **capture-only** before **HID / player** work (section D). See postmortem §5.0 ([`../../docs/history/postmortem-agentic-bringup.md`](../../docs/history/postmortem-agentic-bringup.md)).

## A. Bench and DUT (USB)

1. Read [`../../docs/manual-facts.md`](../../docs/manual-facts.md).
2. Wire Pico + IR RX (+ LED for loopback) per [`boards/pico.md`](boards/pico.md); record part numbers and fill pin fields in `boards/pico.yaml`.
3. Operator verifies the bench.
4. DUT presence (BOOTSEL or CircuitPython): `OPERATOR_VERIFY=1 make stage BOARD=pico STAGE=present`
5. UF2 load, then app copy. These use the present pass. Re-run `present` when the USB identity to record has changed (BOOTSEL versus CircuitPython).
   - `OPERATOR_VERIFY=1 OPERATOR_FLASH=1 make load-circuitpython`
   - `OPERATOR_VERIFY=1 OPERATOR_FLASH=1 make firmware` (includes `boot.py` CAPTURE_ONLY → HID off)
6. `OPERATOR_VERIFY=1 make stage BOARD=pico STAGE=workflow`

**Exit A:** `present` and `workflow` pass in `reports/pico/stage.json`. Pins in the workflow record should match YAML.

## B. Device-code IR path (capture-only — no HID)

Goal: prove each Bose source + library code emits usable frames. Do **not** tune player HID here.

7. Confirm AUX holds Sony DVR `20636` (code-check `2, 0, 6, 3, 6`). TV source uses `10178`. Other sources per [ADR 004](../../docs/decisions/004-multi-source-personalities.md). Log blinks with [`../../docs/remote/blink-observation-worksheet.md`](../../docs/remote/blink-observation-worksheet.md). Source LED blinks when a press transmits IR.
8. Unique capture (HID disabled for the listen):  
   `OPERATOR_VERIFY=1 make capture FRESH=1 PERSONALITY=<id>`  
   Examples: `sony-dvr-20636`, `vcr-20033`. Host arms `/CAPTURE_ONLY` so USB HID is off; terminal prints `[NEW] <frame_key>` only. Press keys on that source; Ctrl+C restores map HID. Map codes later from `unique_codes.json`.
9. Confirm-map buttons (`MODE=confirm` / capture confirm path). Evidence: `validated.json` with frame keys. **HID fields may stay null.**
10. Optional optical loopback (parallel, not a map gate): `OPERATOR_VERIFY=1 OPERATOR_IR_PATH=1 make loopback`

**Exit B:** Capture stamp with unique/confirm evidence for the staged personality; listen showed **frame keys**, not keyboard/mouse inject. Chrome is **not** required. Host-only HID packing is `make sim`, not a bench stage.

## C. Keymap (host SIL)

11. Append measured IR keys to the **union** [`../../software/keymap.yaml`](../../software/keymap.yaml) for the matching profile. Do not regress AUX rows. Check with `make check`.

**Exit C:** Keymap loads; profile SIL tests pass. Still no Chrome required.

## D. HID and players (map mode — after device-code IR is known)

12. On-device map mode (no `/CAPTURE_ONLY`); CIRCUITPY needs `adafruit_hid`; measured keymap deployed.
13. HID smoke: focus a key-event test page ([`../../docs/chrome-troubleshooting.md`](../../docs/chrome-troubleshooting.md)).
14. Per-player matrix: [`../../docs/remote/player-validation-matrix.md`](../../docs/remote/player-validation-matrix.md). Leave a row `not_run` until the operator reports what the player did.

**Exit D:** Matrix rows with operator observations. Streaming sites are last, not a gate for sections A–C.
