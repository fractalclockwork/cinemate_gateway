# Operator

The operator validates the bench and uses the gateway. The Pico is the device under test. Every HWIL test waits until `OPERATOR_VERIFY=1`.

DUT presence is measured by `make stage STAGE=present`. `find_pico` runs only there. The pass in `reports/pico/stage.json` stands until the operator runs `present` again, including a pass from an earlier sitting. Later HWIL commands use that record.

The `environment/` tree is the Dev-Host toolchain. A capture `session.json` is an IR listen, which is how button codes are learned. That session is a measurement, not a curriculum.

| Flag | Meaning |
| --- | --- |
| `OPERATOR_VERIFY=1` | Operator has verified the bench. Required before any HWIL test starts |
| `OPERATOR_FLASH=1` | Permission to write CircuitPython / firmware |
| `OPERATOR_IR_PATH=1` | Permission for the optical path: IR RX aimed; LED safe for short optical loopback (not CineMate TX) |
| `OPERATOR_BUTTON_OK=1` | Optional scripted YES for a single confirm-map button |

Host checks (`make check`, `make sim`) have no bench to verify and do not read these flags.

Sim flag `IR_GATEWAY_HWIL_SIM=1` skips USB/YES prompts for CI. It does not forge operator verification: HWIL entry still needs `OPERATOR_VERIFY`, and commands that require `OPERATOR_IR_PATH` still need that flag set by the operator (or CI policy).

Agents must never set these flags.

The Python package re-exports the stdlib `operator` module so `itemgetter` and the rest keep working when this repo is on `PYTHONPATH`.
