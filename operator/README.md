# Operator

The operator validates the bench and is the person who uses the gateway. The Pico is the device under test, and every HWIL test waits until `OPERATOR_VERIFY=1`.

DUT presence is measured by `make stage STAGE=present`, which is the only place `find_pico` runs. The pass recorded in `reports/pico/stage.json` stands until the operator runs `present` again, even across sittings, and later HWIL commands rely on that record.

The `environment/` tree is the Dev-Host toolchain. A capture `session.json` is an IR listen, which is how button codes are learned; that session is a measurement, not a curriculum.

| Flag | Meaning |
| --- | --- |
| `OPERATOR_VERIFY=1` | The operator has verified the bench. Required before any HWIL test starts |
| `OPERATOR_FLASH=1` | Permission to write CircuitPython or firmware |
| `OPERATOR_IR_PATH=1` | Permission for the optical path: IR RX aimed, LED safe for a short optical loopback, not CineMate TX |
| `OPERATOR_BUTTON_OK=1` | Optional scripted YES for a single confirm-map button |

Host checks (`make check`, `make sim`) have no bench to verify and do not read these flags.

The sim flag `IR_GATEWAY_HWIL_SIM=1` skips USB and YES prompts for CI. It does not forge operator verification: HWIL entry still needs `OPERATOR_VERIFY`, and commands that require `OPERATOR_IR_PATH` still need that flag set by the operator or by CI policy.

Agents must never set these flags.

The Python package re-exports the stdlib `operator` module so `itemgetter` and the rest keep working when this repo is on `PYTHONPATH`.
