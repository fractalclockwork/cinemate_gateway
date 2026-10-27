# STATUS — ir-remote-bose

Living handoff. Agents: read this before broad search. Update at end of each session.
Spec: [`docs/SPEC.md`](docs/SPEC.md). Doc index: [`docs/README.md`](docs/README.md). Method: [`docs/methodology/operator-loop.md`](docs/methodology/operator-loop.md). Bring-up record: [`docs/history/postmortem-agentic-bringup.md`](docs/history/postmortem-agentic-bringup.md).

## Decided

- Phase 1: AUX IR RX → Pico → USB HID for Chrome; no TX at CineMate Interface.
- Staged AUX personality: Sony DVR **`20636`** (`sony-dvr-20636`); TV source **`10178`** separate.
- Host keymap profile: **amazon** ([`software/keymap.yaml`](software/keymap.yaml)) — Space/F/Esc/seek arrows; d-pad = mouse; enter = click; shared page/channel IR → Tab/Shift+Tab ([`docs/remote/amazon-chrome-shortcuts.md`](docs/remote/amazon-chrome-shortcuts.md)).
- Confirmation flags: `OPERATOR_VERIFY` / `OPERATOR_FLASH` / `OPERATOR_IR_PATH` — the operator sets them; agents never do.
- Evidence root: `reports/pico/` (gitignored). Host HID check is `make sim`. Physical IR is capture and loopback.
- On-device firmware: **GP14/GP15**, Sony SIRC decode, `MODE=map`, `KEYMAP` from `make firmware-keymap` → [`hardware/firmware/pico/keymap_gen.py`](hardware/firmware/pico/keymap_gen.py). Deploy recursively ships vendored [`lib/adafruit_hid`](hardware/firmware/pico/lib/adafruit_hid/) (fail if missing).

## Working hypothesis

- Short flash then two flashes after code entry ≈ accept on this unit; manual text says source button “blinks twice.” Log with [`docs/remote/blink-observation-worksheet.md`](docs/remote/blink-observation-worksheet.md); do not silently rewrite history.
- Selected source LED blink = IR TX activity for that personality.

## Open

- Operator confirmed play/pause feels right (one Space per press, 0.12 s release). D-pad feel is acceptable (5 px, ramp to 24 by 1.2 s). Record → F; Quick Skip → Alt+Tab; Instant Replay → Shift+Alt+Tab. Scan (ffw/frw) repeats Left/Right about every 0.35 s while held. A missed toggle after Quick Skip is focus: Alt+Tab leaves the player, and Space then scrolls the page.
- Blink digit/success “start flash” notes still contradictory until worksheet rows exist.
- First git commit / remote / push — the operator publishes.

## Last evidence

| What | Path / result |
| --- | --- |
| SIL | `make check` → 46 passed; `make sim` ok (2026-10-27, after dropping the lesson/harness tests) |
| UF2 | CircuitPython **10.3.1** en_US copied onto `RPI-RP2` (board was already BOOTSEL). Cache: `archive/cache/circuitpython/raspberry_pi_pico.uf2` |
| present | `reports/pico/stage.json` pass @ 2026-10-27T21:49:56Z — `239a:80f4` Adafruit Pico after replug (BOOTSEL pass at 21:47:49Z was the in-between plug) |
| workflow | pass @ 2026-10-27T21:44:38Z — pins `14`/`15`/`25`, mount `/media/plastic/CIRCUITPY` |
| firmware | Deploy survived replug: `CIRCUITPY` has `code.py` (GP14), `keymap_gen.py`, `lib/adafruit_hid`. `boot_out.txt` is CircuitPython 10.3.1 with no traceback. HID interface is up (`/dev/hidraw1`, `/dev/ttyACM0`). |
| Loopback | prior stamp `reports/pico/20261026T210622Z/loopback.json` (not on disk in this tree) |
| AUX map | prior stamp `reports/pico/20261027T043341Z/captures/` (not on disk in this tree) |

## Handoff / next command

1. Operator presses on the key-event viewer, then on a focused Prime title. Listener: `reports/pico/20261027T215244Z/hid-listen.jsonl` (hidraw + serial, not grabbed).
2. Fill Amazon rows from that log. Optional: blink worksheet (does not block HID).

```text
make check
make firmware-keymap
# operator:
OPERATOR_VERIFY=1 OPERATOR_FLASH=1 make firmware
```
