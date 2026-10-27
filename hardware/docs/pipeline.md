# Pipeline

| Make target | Role | Assent | Evidence |
| --- | --- | --- | --- |
| `make check` | software + harness | none | pytest (host) |
| `make check-docker` | environment + software | none | pytest in pico-dev container |
| `make image` / `smoke` | environment | none | Docker image build / toolchain smoke |
| `make sim` | software SIL | none | fixture print |
| `make pico-discover` | environment / HWIL prep | none (read-only) | lsusb / optional picotool |
| `make stage STAGE=present` | HWIL | `HUMAN_VERIFY=1` | USB probe once → `reports/pico/stage.json`. Stands until `present` is run again |
| `make load-circuitpython` | toolchain → board | `HUMAN_VERIFY=1` + `HUMAN_FLASH=1` + `present` pass | picotool load UF2 (BOOTSEL). Uses the present record |
| `make stage STAGE=workflow` | HWIL | `HUMAN_VERIFY=1` + `present` pass | Stored USB identity; CIRCUITPY mount is a workflow fact |
| `make hwil` (`image`) | SIL gate (stage id `image`) | `HUMAN_VERIFY=1` + prior stages | `sil-hid-fixture` stamp — **not** live IR |
| `make capture` / `loopback` | HWIL | `HUMAN_VERIFY=1` (+ `HUMAN_IR_PATH` for loopback) | Physical IR map / optical stamps |
| `make firmware` | HWIL | `HUMAN_VERIFY=1` + `HUMAN_FLASH=1` + `present` pass | copy CircuitPython app to CIRCUITPY. Uses the present record |

`present` is the only USB presence probe. Re-run it when the USB identity to record has changed (BOOTSEL versus CircuitPython).

Sim: `IR_GATEWAY_HWIL_SIM=1` skips live USB for CI-style runs. It does not replace `HUMAN_VERIFY` or a `present` pass. The `image` stage is a SIL HID fixture only; physical IR uses capture/loopback.

USB compose (`docker-compose.usb.yml`) is for operator-driven discover/UF2 only; agents do not enable privileged USB or forge assent.
