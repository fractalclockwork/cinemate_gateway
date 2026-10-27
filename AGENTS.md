# Agentic rules

This repo is structured by **role**. Agents must stand in one role at a time and follow that tree’s `AGENTS.md`.

**Terminology:** **HWIL** = hardware-in-the-loop (automation of the physical device under test). **Human** / **human-in-the-loop** = the operator, who validates and verifies the bench. Every HWIL test waits until `HUMAN_VERIFY=1`. The Pico is the device under test. DUT presence is the `present` stage; that pass stands until the operator runs `present` again. A capture `session.json` is an IR listen, not the presence record. The `environment/` role is the Dev-Host toolchain, not the bench. Assent env vars are `HUMAN_*`: verification (`HUMAN_VERIFY`) and permissions (`HUMAN_FLASH`, `HUMAN_IR_PATH`).

| Role | Tree | May invent? | Notes |
| --- | --- | --- | --- |
| **human** (human-in-the-loop) | [`human/`](human/) | Never assent | Do not set `HUMAN_*` or type YES |
| **hardware** (HWIL) | [`hardware/`](hardware/) | After assent + evidence | Stages, flash, IR capture path |
| **kicad protoboard** | [`docs/kicad/ir-gateway/`](docs/kicad/ir-gateway/) | After human sch/place gates | Schematic → snap → Manhattan wire-wrap ([`AGENTS.md`](docs/kicad/ir-gateway/AGENTS.md)) |
| **software** | [`software/`](software/) | Freely | Decode + HID fixtures; no USB |
| **environment** | [`environment/`](environment/), [`docker/`](docker/) | Freely for builds | pico-dev image, UF2 pointers; no forged assent |
| **lesson** | [`lesson/`](lesson/) | Content only | Unlocked by `reports/pico/stage.json` image pass |
| **harness** | [`harness/`](harness/) | Paths + ready gates only | No flash, no IR TX, no prompts |

Evidence under `reports/` is the only unlock token across roles.

Spec: [`docs/SPEC.md`](docs/SPEC.md). Living handoff: [`STATUS.md`](STATUS.md). Methodology: [`docs/methodology/`](docs/methodology/README.md). Manual facts: [`docs/manual-facts.md`](docs/manual-facts.md). Doc index: [`docs/README.md`](docs/README.md).
