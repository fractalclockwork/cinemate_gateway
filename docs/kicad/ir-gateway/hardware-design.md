# IR gateway protoboard — hardware design

Hand-wired / wire-wrap prototype for the Pico IR RX + TX path (crt-drive style). KiCad models insulated jumpers as `InN.Cu` layers named `JumperN` (Manhattan H/V only). THT pads short all layers, so routes dodge foreign pads; crossings use a different jumper layer. Treat layer count as unlimited — add another `InN` / re-route when wire-wrapping.

Status language: **Decided**, **Working hypothesis**, **Open**.

## Decided

- MCU: Raspberry Pi Pico (RP2040), USB-powered from host.
- IR receive: **CHQ1838** 38 kHz demodulator (`OptoDevice:Vishay_MINIMOLD-3Pin`). Pins: **1=OUT, 2=GND, 3=VCC** (not TSOP17xx order).
- IR transmit: IR LED + **single NPN** low-side switch (**2N3904**, TO-92 E-B-C).
- Drive: GPIO → base resistor → NPN base; emitter to GND; collector pulls LED cathode; anode fed from `+3V3` through series resistor.
- GPIO map:
  - **GPIO14** (Pico pin 19) ← IR receiver OUT (`IR_RX`)
  - **GPIO15** (Pico pin 20) → TX base drive (`IR_TX`)
- Power: Pico **3V3** (pin 36) is the only rail for RX VCC and LED anode feed. Common GND from Pico pin 38 (and module GND).
- Routing: orthogonal Manhattan only; crossings on distinct jumper layers (wire-wrap).

## Working hypothesis (verify against datasheets before stuffing)

| Ref | Value | Intent |
| --- | --- | --- |
| U2 | CHQ1838 | 38 kHz PCM RX; VCC = 3.3 V (confirm abs max) |
| D1 | 5 mm IR LED (~940 nm) | TX / optical loopback |
| R1 | 1 kΩ | NPN base (~2–3 mA from 3.3 V GPIO) |
| R2 | 100 Ω | LED series; ~15–20 mA if Vf ≈ 1.2–1.5 V at 3.3 V |
| C1 | 100 nF | Bypass at U2 VCC to GND |
| Q1 | 2N3904 | Low-side switch |

Confirm U2 absolute max / recommended VCC, OUT idle level, and D1 Vf/If before locking R2. Do not invent other values as confirmed.

## Open

- Exact IR LED part number (operator).
- Whether U2 needs an external pull-up on OUT (check CHQ1838 datasheet).
- Optical aiming / shroud for loopback vs CineMate TX (phase 2).

## Net list

| Net | Members |
| --- | --- |
| `+3V3` | A1 pin 36, U2.3 (VCC), R2.1, C1.1, J_PICO.1 |
| `GND` | A1 pin 38, U2.2 (GND), Q1 E, C1.2, J_PICO.2 |
| `IR_RX` | U2.1 (OUT), J_PICO.3 → GPIO14 |
| `IR_TX` | J_PICO.4 ← GPIO15, R1.1 |
| `Q1_B` | R1.2, Q1 B |
| `LED_K` | D1 K, Q1 C |
| `LED_A` | D1 A, R2.2 |

Schematic sheet: demod (C1/U2) left, `J_PICO` mid, vertical TX stack `R2` → `D1` (90°) → `Q1` with `R1` into base.

## PCB wire-wrap

Agent process (gates, layers, commands): [`AGENTS.md`](AGENTS.md).  
Snap + Manhattan route: [`_snap_route.py`](_snap_route.py) (2.54 mm hole grid from Pico A1).

| Layer | Net |
| --- | --- |
| `F.Cu` | `+3V3` |
| `B.Cu` | `GND` |
| `InN.Cu` (`JumperN`) | signals; a new jumper layer when paths cross |

Courtyard overlaps on the dense TX cluster are expected for hand wire-wrap.

## Files

- Project: [`ir-gateway.kicad_pro`](ir-gateway.kicad_pro)
- Schematic: [`ir-gateway.kicad_sch`](ir-gateway.kicad_sch)
- PCB: [`ir-gateway.kicad_pcb`](ir-gateway.kicad_pcb)
- Symbol: [`symbols/ir-gateway.kicad_sym`](symbols/ir-gateway.kicad_sym) (`ir-gateway:CHQ1838`)
- Regenerator: [`_generate.py`](_generate.py)
