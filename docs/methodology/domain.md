# IR / HID notes

The working method is [`operator-loop.md`](operator-loop.md).

## Two checks

The host check covers synthetic pulse trains, decode, the keymap, and HID report packing through `make check` and `make sim`. It needs no USB device and reads no operator flags.

The bench check begins when the operator verifies the bench (`OPERATOR_VERIFY=1`) before any physical command. `present` records USB identity once, capture and loopback stamps are the physical IR evidence, and `environment/` provides the Dev-Host toolchain. When a bench command fails it prints the next command for the operator to run.

## Commands

| Command | What it is |
| --- | --- |
| `make stage STAGE=present` | USB identity. Stands until `present` is run again |
| `make stage STAGE=workflow` | CIRCUITPY mount and pin record, using the present pass |
| `make capture` | Listen for button codes, then confirm or validate a map |
| `make loopback` | Optical LED path. Needs `OPERATOR_IR_PATH=1` |
| `make firmware` | Copy the CircuitPython app. Needs `OPERATOR_FLASH=1` and a present pass |

## Loopback ceilings

Optical loopback runs only when `OPERATOR_VERIFY=1` is set, `present` is `pass` in `reports/pico/stage.json`, `OPERATOR_IR_PATH=1` is set, and the pulse train respects `max_ir_tx_ms` and `max_ir_tx_duty` in [`hardware/boards/pico.yaml`](../../hardware/boards/pico.yaml).

## Phase 1 and phase 2

Phase 1 receives the Bose remote and sends HID to Chrome; the LED is loopback only. Phase 2, which is deferred, adds a small web app and IR transmit toward the CineMate Interface, and needs a new operator flag before any radiated IR.
