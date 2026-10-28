# Agentic rules

Agents work one tree at a time and follow that tree’s `AGENTS.md`.

**Terminology:** The **operator** confirms the bench and is the end user of the gateway. The **Pico** is the device under test. The **host** may measure USB identity, decode, and HID report bytes. It may not claim that the player paused, that the pointer feels right, or that a window is focused. **HWIL** means a command that touches the Pico or the IR path. Every HWIL command waits until `OPERATOR_VERIFY=1`. DUT presence is the `present` stage; that pass stands until the operator runs `present` again. A capture `session.json` is an IR listen, not the presence record. The `environment/` tree is the Dev-Host toolchain, not the bench. Confirmation flags: `OPERATOR_VERIFY` (all HWIL), `OPERATOR_FLASH` (**UF2 / picotool only** — not CIRCUITPY `make firmware`), `OPERATOR_IR_PATH` (optical loopback).

| Tree | May invent? | Notes |
| --- | --- | --- |
| **operator** [`operator/`](operator/) | Never confirmation | Do not set `OPERATOR_*` or type YES |
| **hardware** [`hardware/`](hardware/) | After confirmation + evidence | Stages, flash, IR capture |
| **kicad protoboard** [`docs/kicad/ir-gateway/`](docs/kicad/ir-gateway/) | After operator sch/place gates | Schematic → snap → Manhattan wire-wrap |
| **software** [`software/`](software/) | Freely | Decode + HID fixtures; no USB |
| **environment** [`environment/`](environment/), [`docker/`](docker/) | Freely for builds | pico-dev image, UF2 pointers; no forged confirmation |

Spec: [`docs/SPEC.md`](docs/SPEC.md). Living handoff: [`STATUS.md`](STATUS.md). Method: [`docs/methodology/operator-loop.md`](docs/methodology/operator-loop.md). Manual facts: [`docs/manual-facts.md`](docs/manual-facts.md). Doc index: [`docs/README.md`](docs/README.md).
