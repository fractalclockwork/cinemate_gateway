# Pipeline

| Make target | Role | Assent | Evidence |
| --- | --- | --- | --- |
| `make check` | software | none | pytest (host) |
| `make check-docker` | environment + software | none | pytest in pico-dev container |
| `make image` / `smoke` | environment | none | Docker image build / toolchain smoke |
| `make sim` | software SIL | none | fixture print |
| `make pico-discover` | environment / HWIL prep | none (read-only) | lsusb / optional picotool |
| `make stage STAGE=present` | HWIL | `OPERATOR_VERIFY=1` | USB probe once → `reports/pico/stage.json`. Stands until `present` is run again |
| `make load-circuitpython` | toolchain → board | `OPERATOR_VERIFY=1` + `OPERATOR_FLASH=1` + `present` pass | picotool load UF2 (BOOTSEL). Uses the present record |
| `make stage STAGE=workflow` | HWIL | `OPERATOR_VERIFY=1` + `present` pass | Stored USB identity; CIRCUITPY mount is a workflow fact |
| `make capture` / `loopback` | HWIL | `OPERATOR_VERIFY=1` (+ `OPERATOR_IR_PATH` for loopback) | Physical IR map / optical stamps |
| `make firmware` | HWIL | `OPERATOR_VERIFY=1` + `present` pass | copy CircuitPython app to CIRCUITPY (no `OPERATOR_FLASH`) |
| `make firmware-watch` | HWIL | `OPERATOR_VERIFY=1` + `present` | auto-redeploy on keymap/firmware change |

`present` is the only USB presence probe. Re-run it when the USB identity to record has changed (BOOTSEL versus CircuitPython).

Sim: `IR_GATEWAY_HWIL_SIM=1` skips live USB for CI-style runs. It does not replace `OPERATOR_VERIFY` or a `present` pass. `make sim` is the host HID fixture. Physical IR uses capture and loopback.

USB compose (`docker-compose.usb.yml`) is for operator-driven discover/UF2 only; agents do not enable privileged USB or forge assent.
