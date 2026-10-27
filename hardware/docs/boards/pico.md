# Raspberry Pi Pico (RP2040) — IR gateway

## Confirmed

- Board: **Raspberry Pi Pico** (standard, non-W) over **USB** to a **Linux** host.
- Role: IR **receive** from Bose CineMate universal remote (AUX mode) → **USB HID** keyboard/consumer control for Chrome.
- IR **LED** reserved for HWIL optical loopback (phase 1) and future CineMate TX (phase 2).

## Depends on part datasheets (do not invent)

Fill these after choosing modules. Until then pins stay `null` in [`../../boards/pico.yaml`](../../boards/pico.yaml).

| Item | What to verify |
| --- | --- |
| IR receiver | Part number, VCC (3.3 V vs 5 V), GND, OUT polarity, carrier (often 38 kHz) |
| IR LED | Forward voltage/current; series resistor; whether a transistor driver is required vs GPIO direct |
| Pico GPIO | Which GP pin for RX OUT and TX drive; avoid USB-critical pins |

### Suggested wiring checklist (operator)

1. Confirm IR module absolute maximum ratings against Pico 3.3 V IO.
2. Common ground: Pico GND ↔ module GND ↔ LED cathode return.
3. RX OUT → chosen `ir_rx` GPIO (pull-up if datasheet requires).
4. TX GPIO → resistor (and driver if needed) → IR LED → return.
5. USB to Linux host; no external 5 V into 3.3 V-only pins.

## USB identity

Bootloader / CircuitPython product IDs vary by firmware. Board YAML lists Raspberry Pi vendor `2e8a` and common product IDs; `present` stage probes USB and records what was seen.

## Firmware

CircuitPython sources under [`../../firmware/pico/`](../../firmware/pico/). After `present` has passed: `HUMAN_VERIFY=1 HUMAN_FLASH=1 make firmware`.


## Decided GPIO (protoboard)

| Signal | Pico | Notes |
| --- | --- | --- |
| `IR_RX` | GPIO14 (pin 19) | CHQ1838 OUT |
| `IR_TX` | GPIO15 (pin 20) | NPN base via 1 kΩ |

KiCad protoboard: [`docs/kicad/ir-gateway/`](../../../docs/kicad/ir-gateway/).
