# Hardware (HWIL)

Physical stages and flash after the operator verifies the bench (`HUMAN_VERIFY=1`). DUT presence is the `present` pass; later commands use that record.

## Allowed

- Run `make stage` / `make hwil` / `make firmware` within board YAML ceilings.
- Capture IR evidence to `reports/pico/`.

## Forbidden

- Setting `HUMAN_*` flags.
- Starting a stage, capture, loopback, firmware write, or UF2 load before `HUMAN_VERIFY=1`.
- Raising `max_ir_tx_*` to pass a stage.
- Radiating IR toward the CineMate Interface module in phase 1 (LED = optical loopback only).
- Flashing without `HUMAN_FLASH=1`.

## Protoboard (KiCad)

Wire-wrap schematic/PCB process (human sch + placement gates, then 2.54 mm snap and Manhattan layers): [`docs/kicad/ir-gateway/AGENTS.md`](../docs/kicad/ir-gateway/AGENTS.md).
