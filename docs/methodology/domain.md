# IR / HID domain notes

## Two loops

1. **Autonomous (SIL)** — Synthetic pulse trains, NEC-like decode helpers, keymap → HID report packing. `make check` / `make sim`. No USB, no assent.
2. **Physical (HWIL)** — The operator verifies the bench before each test (`HUMAN_VERIFY=1`). The `present` stage measures DUT presence once; that pass stands until `present` is run again. Later stages use the record. Capture and loopback stamps are physical IR evidence. The `environment/` role is the Dev-Host toolchain. Failures print the next operator command.

## Stage fidelity

| Stage / stamp | Fidelity |
| --- | --- |
| `image` (`make hwil`) | **SIL only** — host HID fixture (`sil-hid-fixture`). Unlocks lessons via `require_image`. Not live IR→HID. |
| capture `validated.json` | **Physical IR map** — gate with `harness.ready.require_ir_map` |
| `make loopback` | **Physical optical** — needs `HUMAN_IR_PATH=1` |

## Validation predicate (phase 1)

Physical IR LED energize (optical loopback) unlocks only when:

- `HUMAN_VERIFY=1` (operator has verified the bench)
- Prior stages `present` and `workflow` are `pass` in `reports/pico/stage.json` (`present` is the stored USB presence record)
- `HUMAN_IR_PATH=1` (permission: RX aimed / LED safe for short loopback)
- Proposed TX pulse train respects `max_ir_tx_ms` / `max_ir_tx_duty` in `hardware/boards/pico.yaml`

Every HWIL test waits until `HUMAN_VERIFY=1`. Flash also requires a `present` pass and `HUMAN_FLASH=1`.

## Phase 1 vs phase 2

- Phase 1: **RX** Bose remote → HID for Chrome. LED = loopback only.
- Phase 2 (deferred): web app + IR TX toward CineMate on/off/vol; new `HUMAN_TX` assent before radiated IR to the Interface module.
