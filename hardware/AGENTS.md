# Hardware (HWIL)

Physical stages after the operator verifies the bench (`OPERATOR_VERIFY=1`). DUT presence is the `present` pass; later commands use that record.

## Allowed

- Run `make stage`, `make capture`, `make loopback`, `make firmware`, and `make firmware-watch` within board YAML ceilings.
- CIRCUITPY app deploy (`make firmware`) after `OPERATOR_VERIFY=1` + present — **no `OPERATOR_FLASH`**.
- Capture IR evidence to `reports/pico/`.

## Forbidden

- Setting `OPERATOR_*` flags.
- Starting a stage, capture, loopback, firmware app deploy, or UF2 load before `OPERATOR_VERIFY=1`.
- Raising `max_ir_tx_*` to pass a stage.
- Radiating IR toward the CineMate Interface module in phase 1 (LED = optical loopback only).
- UF2 / picotool CircuitPython load without `OPERATOR_FLASH=1` (bootloader write only).

## Protoboard (KiCad)

Wire-wrap schematic/PCB process (operator schematic and placement gates, then 2.54 mm snap and Manhattan layers): [`docs/kicad/ir-gateway/AGENTS.md`](../docs/kicad/ir-gateway/AGENTS.md).
