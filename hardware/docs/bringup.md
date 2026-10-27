# Bring-up checklist

Every HWIL command needs `HUMAN_VERIFY=1` in that process. DUT presence is step 4 only. That pass stands until you run `present` again. Later commands use the record.

Living status: [`../../STATUS.md`](../../STATUS.md). Stages below are **independent**: IR reception and button mapping can pass **without** HID or Chrome.

## A. Bench and DUT (USB)

1. Read [`../../docs/manual-facts.md`](../../docs/manual-facts.md).
2. Wire Pico + IR RX (+ LED for loopback) per [`boards/pico.md`](boards/pico.md); record part numbers and fill pin fields in `boards/pico.yaml`.
3. Operator verifies the bench.
4. DUT presence (BOOTSEL or CircuitPython): `HUMAN_VERIFY=1 make stage BOARD=pico STAGE=present`
5. UF2 load, then app copy. These use the present pass. Re-run `present` when the USB identity to record has changed (BOOTSEL versus CircuitPython).
   - `HUMAN_VERIFY=1 HUMAN_FLASH=1 make load-circuitpython`
   - `HUMAN_VERIFY=1 HUMAN_FLASH=1 make firmware`
6. `HUMAN_VERIFY=1 make stage BOARD=pico STAGE=workflow`

**Exit A:** `present` and `workflow` pass in `reports/pico/stage.json`. Pins in the workflow record should match YAML.

## B. IR path (no HID required)

7. Confirm AUX holds Sony DVR `20636` (code-check `2, 0, 6, 3, 6`). TV source uses `10178`. Log blinks with [`../../docs/remote/blink-observation-worksheet.md`](../../docs/remote/blink-observation-worksheet.md). Source LED blinks when a press transmits IR.
8. Unique capture: `HUMAN_VERIFY=1 make capture FRESH=1`. Listen-only — press keys freely (AUX and/or TV); Ctrl+C when done. Map codes later from `unique_codes.json`.
9. Confirm-map buttons (`MODE=confirm` / capture confirm path). Evidence: `validated.json` with frame keys. **HID fields may stay null.**
10. Optional optical loopback (parallel, not a map gate): `HUMAN_VERIFY=1 HUMAN_IR_PATH=1 make loopback`

**Exit B:** Capture stamp with unique/confirm evidence for the staged personality. Chrome is **not** required.

Note: `make hwil` (`STAGE=image`) runs a **SIL HID fixture** (`sil-hid-fixture`). Treat a pass as SIL/lesson unlock only, not live IR→HID. Prefer capture + loopback stamps for physical IR; `harness.ready.require_ir_map` gates on `validated.json`.

## C. Keymap (host SIL)

11. Write [`../../software/keymap.yaml`](../../software/keymap.yaml) from mapped IR keys + a selected profile. Check with `make check`.

**Exit C:** Keymap loads; profile SIL tests pass. Still no Chrome required.

## D. HID and players (after on-device map firmware)

12. On-device `code.py` must use real IR pins and measured keymap; CIRCUITPY needs `adafruit_hid`.
13. HID smoke: focus a key-event test page ([`../../docs/chrome-troubleshooting.md`](../../docs/chrome-troubleshooting.md)).
14. Per-player matrix: [`../../docs/remote/player-validation-matrix.md`](../../docs/remote/player-validation-matrix.md) (Kanopy first).
15. Optional: `HUMAN_VERIFY=1 HUMAN_IR_PATH=1 make hwil BOARD=pico` only when intentionally exercising the image fixture / future live fixture.

**Exit D:** Matrix rows with evidence stamps. Streaming sites are last, not a gate for sections A–C.
