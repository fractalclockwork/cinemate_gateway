# STATUS — ir-remote-bose

Living handoff. Agents: read this before broad search. Update at end of each session.
Full post-mortem: [`docs/postmortem-agentic-bringup.md`](docs/postmortem-agentic-bringup.md).

## Decided

- Phase 1: AUX IR RX → Pico → USB HID for Chrome; no TX at CineMate Interface.
- Staged AUX personality: Sony DVR **`20636`** (`sony-dvr-20636`); TV source **`10178`** separate.
- Host keymap profile: **kanopy** ([`software/keymap.yaml`](software/keymap.yaml)).
- Assent: `HUMAN_VERIFY` / `HUMAN_FLASH` / `HUMAN_IR_PATH` — agents never set.
- Evidence root: `reports/pico/` (gitignored).
- **`image` stage = SIL HID fixture only** (`sil-hid-fixture`). Physical IR = capture/loopback; gate with `harness.ready.require_ir_map`.
- On-device firmware: **GP14/GP15**, Sony SIRC decode, `KEYMAP` from `make firmware-keymap` → [`hardware/firmware/pico/keymap_gen.py`](hardware/firmware/pico/keymap_gen.py).

## Working hypothesis

- Short flash then two flashes after code entry ≈ accept on this unit; manual text says source button “blinks twice.” Log with [`docs/remote/blink-observation-worksheet.md`](docs/remote/blink-observation-worksheet.md); do not silently rewrite history.
- Selected source LED blink = IR TX activity for that personality.

## Open

- Operator must install **`adafruit_hid`** on CIRCUITPY before HID smoke (`make firmware` warns if missing).
- Operator: refresh `present`/`workflow` so `stage.json` pins match YAML `14`/`15`.
- Operator: flash firmware + HID smoke (key-event viewer); then fill Kanopy rows in [`docs/remote/player-validation-matrix.md`](docs/remote/player-validation-matrix.md).
- Blink digit/success “start flash” notes still contradictory until worksheet rows exist.
- First git commit / remote / push — human when publishing.

## Last evidence

| What | Path / result |
| --- | --- |
| SIL | `make check` → 49 passed (2026-10-27 post-firmware work) |
| present / workflow / image | `reports/pico/stage.json` (2026-10-24; image = SIL — re-run workflow after pin freeze) |
| Loopback | `reports/pico/20261026T210622Z/loopback.json` ok |
| AUX map | `reports/pico/20261027T043341Z/captures/` (IR-validated; session synced from confirm-map) |

## Handoff / next command

1. Operator: `HUMAN_VERIFY=1 make stage BOARD=pico STAGE=present` then `… STAGE=workflow`.
2. Install `adafruit_hid` on CIRCUITPY; `HUMAN_VERIFY=1 HUMAN_FLASH=1 make firmware`.
3. HID smoke → update this STATUS + one Kanopy matrix row.
4. Optional: blink worksheet pass (does not block HID).

```text
make check
make firmware-keymap
# operator:
HUMAN_VERIFY=1 HUMAN_FLASH=1 make firmware
```
