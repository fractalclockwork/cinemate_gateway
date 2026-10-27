# IR / HID notes

Working method: [`operator-loop.md`](operator-loop.md).

## Two checks

1. **Host** — Synthetic pulse trains, decode, keymap, HID report packing. `make check` and `make sim`. No USB and no operator flags.
2. **Bench** — The operator verifies the bench (`OPERATOR_VERIFY=1`) before a physical command. `present` records USB identity once. Capture and loopback stamps are physical IR evidence. `environment/` is the Dev-Host toolchain. Failures print the next operator command.

## Commands

| Command | What it is |
| --- | --- |
| `make stage STAGE=present` | USB identity. Stands until `present` is run again |
| `make stage STAGE=workflow` | CIRCUITPY mount and pin record, using the present pass |
| `make capture` | Listen for button codes, then confirm or validate a map |
| `make loopback` | Optical LED path. Needs `OPERATOR_IR_PATH=1` |
| `make firmware` | Copy the CircuitPython app. Needs `OPERATOR_FLASH=1` and a present pass |

## Loopback ceilings

Optical loopback runs only when:

- `OPERATOR_VERIFY=1`
- `present` is `pass` in `reports/pico/stage.json`
- `OPERATOR_IR_PATH=1`
- The pulse train respects `max_ir_tx_ms` / `max_ir_tx_duty` in [`hardware/boards/pico.yaml`](../../hardware/boards/pico.yaml)

## Phase 1 and phase 2

- Phase 1: receive the Bose remote and send HID to Chrome. The LED is loopback only.
- Phase 2 (deferred): a small web app and IR transmit toward the CineMate Interface. That needs a new operator flag before any radiated IR.
