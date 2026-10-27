# cinemate-gateway

Evidence-gated **Raspberry Pi Pico** gateway: receive the **Bose CineMate** universal remote in **AUX** mode and inject ordinary **USB HID** keyboard/media keys into **Chrome on Linux**.

Normative requirements: [`docs/SPEC.md`](docs/SPEC.md). Phase 1 does **not** transmit IR to the CineMate Interface module; an IR LED is reserved for HWIL optical loopback and a later web/TX phase.

License: [MIT](LICENSE).

## Documentation

| Doc | Role |
| --- | --- |
| [`docs/SPEC.md`](docs/SPEC.md) | Product / system specification |
| [`STATUS.md`](STATUS.md) | Living Decided / Open / handoff |
| [`docs/README.md`](docs/README.md) | Full documentation index |
| [`docs/manual-facts.md`](docs/manual-facts.md) | Manual vs measured remote facts |
| [`AGENTS.md`](AGENTS.md) | Role-gated agent rules |
| [`docs/methodology/`](docs/methodology/README.md) | SIL / HWIL evidence methodology |

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

No hardware or assent required:

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

Wire-wrap IR RX/TX front-end: [`docs/kicad/ir-gateway/`](docs/kicad/ir-gateway/). Process + human gates: [`docs/kicad/ir-gateway/AGENTS.md`](docs/kicad/ir-gateway/AGENTS.md). Design notes: [`docs/kicad/ir-gateway/hardware-design.md`](docs/kicad/ir-gateway/hardware-design.md).

## HWIL bring-up (operator)

Physical stages need operator assent (`HUMAN_*`). Follow [`hardware/docs/bringup.md`](hardware/docs/bringup.md) sections **A–D** (IR reception and button mapping can pass **without** HID or Chrome).

```bash
export HUMAN_VERIFY=1
make stage BOARD=pico STAGE=present
make stage BOARD=pico STAGE=workflow
HUMAN_VERIFY=1 make capture FRESH=1    # listen-only IR catalog
```

`make hwil` (`STAGE=image`) is a **SIL HID fixture** only (`sil-hid-fixture`)—not live optical or IR→HID proof. Prefer capture / `make loopback` stamps for physical IR. Flash after `present` has passed:

```bash
export HUMAN_VERIFY=1 HUMAN_FLASH=1
make load-circuitpython
# install adafruit_hid on CIRCUITPY/lib — see hardware/firmware/pico/README.md
make firmware
```

## Keymap

Active map: [`software/keymap.yaml`](software/keymap.yaml) (kanopy / AUX+`20636`). Example for SIL fixtures: [`software/keymap.example.yaml`](software/keymap.example.yaml). Regenerate on-device fragment: `make firmware-keymap`.

Chrome notes: [`docs/chrome-troubleshooting.md`](docs/chrome-troubleshooting.md). Player validation: [`docs/remote/player-validation-matrix.md`](docs/remote/player-validation-matrix.md).

## Phase 2 (deferred)

Later: a small web app to control the Pico for (a) IR TX of CineMate on/off/vol and (b) the same browser HID controls. Requires capture library, TX under `max_ir_tx_*` ceilings, and new human assent before aiming IR at the Interface module. See [`docs/SPEC.md`](docs/SPEC.md) §5.
# cinemate_gateway
