# The operator confirms the world

A Bose CineMate remote in AUX mode sends infrared to a Raspberry Pi Pico, and the Pico types ordinary USB keystrokes and mouse motion into Chrome on Linux. In this first phase nothing is transmitted toward the CineMate Interface module; the only infrared LED on the bench is for a short optical loopback, and even that waits for the operator to allow the path.

The circuit is small, a 38 kHz receiver, one transistor, and an LED, and the software is mostly a keymap. What made the project worth writing about is the boundary between what a program can verify and what a person has to confirm. A host can check a netlist, a design-rules report, a USB identity, or a HID byte. It cannot look at pin 1, turn a transistor in its fingers, or tell you that Prime Video actually paused. Those confirmations belong to the operator, who is also the person the gateway is built for.

This note describes the process we intend to repeat. The earlier bring-up writeup is archived at [`history/postmortem-agentic-bringup.md`](history/postmortem-agentic-bringup.md); it documents a repository layout we have since abandoned.

## Two kinds of fact

The host is entitled to assert whatever it can measure: that the Sony SIRC decoder and the keymap export behave (`make check`, `make sim`); that a Pico is enumerated on the USB bus (`make stage STAGE=present`), a record that stands until `present` is run again; that a firmware tree landed on the `CIRCUITPY` drive and that a HID report carried a Space or an arrow; that a schematic netlist contains the intended members and the board check reports no shorts.

Everything else is the operator's to confirm, and the operator expresses that confirmation through three flags that gate every physical command. `OPERATOR_VERIFY=1` says the bench is ready for this test. `OPERATOR_FLASH=1` allows a firmware write. `OPERATOR_IR_PATH=1` says the LED, if used at all, is pointed at the receiver on the bench rather than at the amplifier. An agent may ask for these flags; it may not export them or answer YES on the operator's behalf.

On a playing title, the operator is the one who reports whether the pointer feels right, whether a held scan button keeps seeking, and whether play or pause took effect. A row in the player matrix stays `not_run` until that report exists. A key-event viewer can prove that Space was typed; it cannot prove that the movie stopped. The working method is written down in [`methodology/operator-loop.md`](methodology/operator-loop.md).

## Schematic and board

The protoboard is a wire-wrap front end for the Pico. The design facts live in [`kicad/ir-gateway/hardware-design.md`](kicad/ir-gateway/hardware-design.md) and the order of work in [`kicad/ir-gateway/AGENTS.md`](kicad/ir-gateway/AGENTS.md).

An agent may generate the schematic and run the electrical rules check, and then it stops. The operator reviews the sheet for connectivity, polarity, and the pin map. The receiver is a CHQ1838, whose pin order is OUT, GND, VCC, which is not the TSOP order; a netlist can be perfectly tidy and still tie the data pin to ground if the wrong footprint was copied. Resistor and capacitor values remain working hypotheses until a datasheet confirms them, and the host does not get to promote a hypothesis by writing the word "decided."

Placement is gated the same way. The agent may draft footprints, but the operator confirms rotation and position: the emitter-base-collector order on the TO-92, the anode and cathode on the LED, and the direction the receiver faces. Only then does [`_snap_route.py`](kicad/ir-gateway/_snap_route.py) snap the holes to a 2.54 mm grid and lay orthogonal jumpers, with power and ground on their own layers and a fresh jumper layer wherever two signals would cross. A design-rules check with zero shorts is necessary, but it is neither approval to stuff the board nor permission to aim the LED at the amplifier.

The gate list is long because the order matters. It lives beside the board files and is not pasted into every conversation about Chrome.

## Bring-up

Bring-up follows [`../hardware/docs/bringup.md`](../hardware/docs/bringup.md), whose sections are deliberately independent so that infrared reception and the button map can be real before a browser is ever opened.

The operator verifies the bench first. `present` records which USB device is attached, and `workflow` records the `CIRCUITPY` mount and the pins: GP14 receives, GP15 transmits and is held low. Capture then listens while the operator presses keys; that session is how button codes are learned, and confirming a code writes a stamp under `reports/`. It is a measurement, not a curriculum, and it unlocks nothing. Firmware is copied only after `OPERATOR_FLASH`, with the on-device map generated from the host keymap, and the Pico enumerates as a keyboard, a consumer-control device, and a mouse. The player comes last: focus the Prime title, change one thing, and let the operator say what the picture did.

`make sim` can print a synthetic HID report with no Pico attached. That report says nothing about whether a button on the remote did anything.

## What we copied, and then removed

The first process was borrowed from a general lab method: roles, a lesson that unlocked after a synthetic "image" stage, a harness whose job was to refuse work, and environment variables named `HUMAN_*`. The person at the bench was cast as a gate in a curriculum.

That shape cost time, because agents spent effort protecting lesson unlocks and stage names that had nothing to do with the product. `HUMAN` was also the wrong word. The operator builds the board, flashes the Pico, watches the movie, and lives with the keymap, so the flags are now `OPERATOR_*`. The lesson tree and the harness role are gone; button-code learning remains, as capture.

A later friction was subtler: unique IR listen still ran under map-mode HID, so library-code bring-up fought the player keymap in the same terminal. Capture-only (`/CAPTURE_ONLY`, HID off, `frame_key` print) isolates device-code work from player integration; the archived postmortem §5.0 records that gap and the split.

## How the instructions are loaded

Three kinds of text reach the agent at three different times, and confusing them is how a short safety rule grows into a novel or a board procedure goes unread because it was never in front of the agent.

The root [`AGENTS.md`](../AGENTS.md) is always on, present in every session. It is short because every turn pays for it. It names the operator, the Pico, and the host, and it forbids inventing confirmation. A second always-on copy of the same paragraph would bill the same tokens twice.

The nested files, [`operator/AGENTS.md`](../operator/AGENTS.md), [`hardware/AGENTS.md`](../hardware/AGENTS.md), [`software/AGENTS.md`](../software/AGENTS.md), and [`environment/AGENTS.md`](../environment/AGENTS.md), appear only when that directory is being worked on. They are constraints rather than tutorials: do not flash, do not open USB from the decode tests, do not set flags from the toolchain. The KiCad `AGENTS.md` is the long one, and it appears when the board is the work. Cursor also repeats a nested `AGENTS.md` as a rule beside the file, so a long file is paid twice during that task. The short ones should stay short.

A project skill under [`.cursor/skills/bench-session/`](../.cursor/skills/bench-session/SKILL.md) is read only when the task matches: a firmware flash, pointer or seek feel, play or pause on Prime. The agent chooses it from the description. The body is the procedure, one change, flash only after `OPERATOR_FLASH`, ask what the screen did, and if play or pause seems dead, check focus before retuning timing. It points at the operator-loop note rather than reproducing it.

[`STATUS.md`](../STATUS.md) is the handoff between sessions. The agent opens it when it needs it; it is not part of the always-on prompt, and neither is the archived postmortem.

None of this removes the operator. "A bit too much acceleration" and "that was focus" are observations only a person can make. What the skill does is keep an agent from recording a pass the operator never reported, and from retuning debounce when the window was simply somewhere else.

## Misses that taught the split

On the firmware side, the activity LED blinked on every press while the host received no keys. The decoder was splitting frames, and the LED only proved that edges existed. Later, play and pause appeared broken after a seek-repeat change even though the keys were leaving the Pico; Quick Skip sends Alt+Tab, so the next Space landed on whatever window was in front, or scrolled the page. A longer software latch only made the buttons feel late. Putting the player back in focus made a single tap work again.

On the hardware side the matching mistakes are a netlist that is electrically consistent with the receiver wired backwards, and a Manhattan route laid before the operator has turned the transistor or the LED. The checker is green and the part in your hand is still wrong. The same rule covers both cases: a clean report is a host fact, and the physical object and the picture on the screen belong to the operator.

## The next physical project

Start with a short always-on rule that says who confirms the world and which flags an agent must never set. Keep board gates beside the board and firmware limits beside the firmware. Write one skill for the session you will repeat, one change and then the person at the bench. Keep a status file. Never claim that an agent validated the stuffed board or the player.
