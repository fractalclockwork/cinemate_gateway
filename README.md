# ir-remote-bose

Evidence-gated **Raspberry Pi Pico** gateway: receive the **Bose CineMate** universal remote in **AUX** mode and inject ordinary **USB HID** keyboard/media keys into **Chrome on Linux**.

Phase 1 does **not** transmit IR to the CineMate Interface module. An IR LED is reserved for HWIL optical loopback and a later web/TX phase.

Manual facts (verified vs test): [`docs/manual-facts.md`](docs/manual-facts.md). Methodology: [`docs/methodology/`](docs/methodology/README.md). Agentic rules: [`AGENTS.md`](AGENTS.md). Living status: [`STATUS.md`](STATUS.md). Post-mortem: [`docs/postmortem-agentic-bringup.md`](docs/postmortem-agentic-bringup.md).

## Roles

| Role | Tree |
| --- | --- |
| Human assent | [`human/`](human/) |
| HWIL | [`hardware/`](hardware/) |
| SIL | [`software/`](software/) |
| Environment | [`environment/`](environment/) |
| Lesson | [`lesson/`](lesson/) |
| Harness | [`harness/`](harness/) |

## Quick start (SIL)

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
make check
make sim
```

### Docker Dev-Host (crt-drive-style pico-dev)

```bash
make image          # ir-remote-bose/pico-dev:local
make smoke
make check-docker   # pytest in container
make pico-discover  # USB inventory
```

See [`docker/README.md`](docker/README.md) and [`environment/README.md`](environment/README.md) for CircuitPython UF2 via `make load-circuitpython` (requires `HUMAN_VERIFY`, `HUMAN_FLASH`, and a `present` pass).

## Protoboard (KiCad)

Wire-wrap IR RX/TX front-end (crt-drive Manhattan / jumper layers): [`docs/kicad/ir-gateway/`](docs/kicad/ir-gateway/). Process + human gates: [`docs/kicad/ir-gateway/AGENTS.md`](docs/kicad/ir-gateway/AGENTS.md). After placement is verified, `python3 docs/kicad/ir-gateway/_snap_route.py` (`+3V3`=`F.Cu`, `GND`=`B.Cu`, signals on `JumperN`). Design notes: [`docs/kicad/ir-gateway/hardware-design.md`](docs/kicad/ir-gateway/hardware-design.md).

## HWIL bring-up

See [`hardware/docs/bringup.md`](hardware/docs/bringup.md).

`present` probes USB once. That pass stands until you run `present` again. Later commands use the record and still require `HUMAN_VERIFY` in that process.

```bash
export HUMAN_VERIFY=1
make stage BOARD=pico STAGE=present
make stage BOARD=pico STAGE=workflow
export HUMAN_IR_PATH=1
make hwil BOARD=pico
```

Flash after `present` has passed. Re-run `present` when the USB identity to record has changed (BOOTSEL versus CircuitPython).

```bash
export HUMAN_VERIFY=1 HUMAN_FLASH=1
make load-circuitpython
make firmware
```

## Keymap

Editable example: [`software/keymap.example.yaml`](software/keymap.example.yaml). Copy to `software/keymap.yaml` after real AUX captures. Chrome notes: [`docs/chrome-troubleshooting.md`](docs/chrome-troubleshooting.md). Player validation matrix: [`docs/remote/player-validation-matrix.md`](docs/remote/player-validation-matrix.md).

## Phase 2 (deferred)

Later: a small web app to control the Pico remotely for (a) IR TX of CineMate on/off/vol and (b) the same browser HID controls. Requires capture library, TX under `max_ir_tx_*` ceilings, and new human assent before aiming IR at the Interface module.
