# Human (human-in-the-loop)

The operator validates and verifies the bench. The Pico is the device under test. Every HWIL test waits until `HUMAN_VERIFY=1`.

DUT presence is measured by `make stage STAGE=present`. `find_pico` runs only there. The pass in `reports/pico/stage.json` stands until the operator runs `present` again, including a pass from an earlier sitting. Later HWIL commands use that record.

The `environment/` tree is the Dev-Host toolchain. A capture `session.json` is an IR listen.

| Flag | Meaning |
| --- | --- |
| `HUMAN_VERIFY=1` | Operator has verified the bench. Required before any HWIL test starts |
| `HUMAN_FLASH=1` | Permission to write CircuitPython / firmware |
| `HUMAN_IR_PATH=1` | Permission for the optical path: IR RX aimed; LED safe for short optical loopback (not CineMate TX) |

SIL (`make check`, `make sim`) has no bench to verify and does not read these flags.

Sim flag `IR_GATEWAY_HWIL_SIM=1` skips USB/YES prompts for CI. It does not forge operator verification: HWIL entry still needs `HUMAN_VERIFY`, and stages that require `HUMAN_IR_PATH` still need that flag set by a person (or CI policy).

Agents must never set these flags.
