# Specification — ir-remote-bose

Normative product and system requirements for this repository. Living session state belongs in [`STATUS.md`](../STATUS.md). Manual-derived facts belong in [`manual-facts.md`](manual-facts.md). How the operator confirms the bench belongs in [`methodology/operator-loop.md`](methodology/operator-loop.md) and root [`AGENTS.md`](../AGENTS.md).

An early chat brief (`PROMPT.md`) was retired in favor of this document.

## 1. Purpose

Build a personal **remote-control gateway**:

1. Receive IR from the **Bose CineMate Digital Home Theater** universal remote in **AUX** mode.
2. Decode on a **Raspberry Pi Pico**.
3. Inject ordinary **USB HID** keyboard, consumer-control (media), and/or **mouse** events into a host PC.
4. Drive normal browser actions in **Chrome on Linux** on streaming sites (navigation, select, back, play/pause, seek)—without assuming a site API or identical shortcuts across services.

## 2. Non-goals

- Streaming-service APIs, DRM bypass, account automation, or evading site restrictions.
- Interfering with other people’s devices or equipment.
- Inventing IR protocols, device codes, button encodings, or programming steps not supported by the manuals or measured evidence.
- Phase 1: transmitting IR toward the CineMate **Interface module** (amp control). An IR LED may be used only for bench optical loopback (and later Phase 2 under new assent).

## 3. Constraints

| Constraint | Requirement |
| --- | --- |
| Manual-first | Owner’s guide and Device Codes book are primary product sources. Label **confirmed** vs **must test** vs **unknown**. See [`manual-facts.md`](manual-facts.md). |
| AUX personality | AUX selects a **programmed** device profile (five-digit library code), not a fixed factory Bose IR set. Unprogrammed sources may emit nothing useful. |
| Code-book direction | Codes program **this Bose remote to control other brands**. They are not IR dumps and not codes to make another remote operate Bose gear. |
| Receive preference | Prefer RX + decode of the original remote. Do not TX unless there is a clear, assented reason. |
| User-input only | Map to ordinary HID keyboard/media events the operator could type. Prefer keys over browser automation. |
| Confirmation | Physical bench work requires the operator to set `OPERATOR_VERIFY` (and `OPERATOR_FLASH` / `OPERATOR_IR_PATH` where applicable). Agents must not invent that confirmation. |

### Staged remote personalities (Decided / in progress)

Source buttons left → right on the face: **TV / CBL-SAT / DVD / VCR / AUX**.

| Bose source | Profile | Library code | Personality | Status |
| --- | --- | --- | --- | --- |
| TV | none | `10178` | `tv-10178` | Separate source; nec-like; not a player |
| CBL-SAT | paramount | `21033` | `cblsat-21033` | SIRC-20 `1a:cmd:62` (+ shared `:49` with DVD) |
| DVD | kanopy | `20533` | `dvd-20533` | SIRC-20 `1a:cmd:49` |
| VCR | youtubetv | `20033` | `vcr-20033` | SIRC-12; HID mirrors amazon; quick_skip silent; replay=`b4:5b` |
| AUX | amazon | `20636` | `sony-dvr-20636` | Measured SIRC-20; working |

Prefer Sony list codes on every player source (including CBL-SAT) so IR stays on the validated SIRC path. Never reuse `20636` or `20000`. Slotting, pool, walks, conflict rules: [`decisions/004-multi-source-personalities.md`](decisions/004-multi-source-personalities.md). VCR detail: [`decisions/003-vcr-youtubetv-personality.md`](decisions/003-vcr-youtubetv-personality.md). AUX: [`decisions/001-aux-personality-20636.md`](decisions/001-aux-personality-20636.md). Data: [`software/profiles/remote.yaml`](../software/profiles/remote.yaml).

## 4. Architecture (Decided)

| Layer | Choice |
| --- | --- |
| MCU | Raspberry Pi Pico, **CircuitPython** |
| Host interface | Pico enumerates as **USB HID** keyboard + consumer control + mouse (not a host-side serial daemon for Phase 1) |
| IR RX / TX pins | **GP14** RX, **GP15** TX (TX held low in Phase 1) — [`hardware/boards/pico.yaml`](../hardware/boards/pico.yaml) |
| Decode | Thin on-device Sony SIRC; host SIL helpers in [`software/decode.py`](../software/decode.py) |
| Keymap | Host [`software/keymap.yaml`](../software/keymap.yaml) → `make firmware-keymap` → [`hardware/firmware/pico/keymap_gen.py`](../hardware/firmware/pico/keymap_gen.py) |
| App profiles | Per-player HID under [`software/profiles/`](../software/profiles/); host keymap is a **union** of IR frames (face order TV / CBL-SAT / DVD / VCR / AUX; append after each capture) |
| Trees | `operator/` confirmation, `hardware/` bench, `software/` host checks, `environment/` toolchain — see [`AGENTS.md`](../AGENTS.md) |

Hardware bring-up and pin/electrical caveats: [`hardware/docs/boards/pico.md`](../hardware/docs/boards/pico.md), [`hardware/docs/bringup.md`](../hardware/docs/bringup.md). Protoboard: [`kicad/ir-gateway/`](kicad/ir-gateway/).

## 5. Phases

### Phase 1 (current)

- RX Bose remote → decode → HID → Chrome.
- IR LED = optical **loopback** only (not Interface TX).
- Capture / confirm-map produce IR identity evidence; HID smoke and player validation follow on-device firmware deploy.

### Phase 2 (deferred)

- Small web app to drive the Pico for (a) IR TX of CineMate on/off/vol and (b) the same browser HID controls.
- Requires a capture library, TX under `max_ir_tx_*` ceilings, and a new operator flag (`OPERATOR_TX`) before aiming at the Interface module.

## 6. Evidence and validation

| Concern | Where |
| --- | --- |
| Manual vs measured facts | [`manual-facts.md`](manual-facts.md) |
| IR button map / inventory | [`remote/button-inventory.md`](remote/button-inventory.md), `reports/pico/*/captures/` (local, gitignored) |
| Button-code capture | `make capture`; stamps in `reports/pico/*/captures/` (local, gitignored) |
| Host HID fixture | `make sim` — synthetic report only, not live IR |
| Optical loopback | `make loopback` + `OPERATOR_IR_PATH` |
| Player control matrix | [`remote/player-validation-matrix.md`](remote/player-validation-matrix.md) |
| Blink / programming LEDs | [`remote/blink-observation-worksheet.md`](remote/blink-observation-worksheet.md), [`decisions/002-blink-observation-protocol.md`](decisions/002-blink-observation-protocol.md) |
| Chrome / HID troubleshooting | [`chrome-troubleshooting.md`](chrome-troubleshooting.md), [`remote/amazon-chrome-shortcuts.md`](remote/amazon-chrome-shortcuts.md) |
| Bring-up ladder (IR without HID) | [`hardware/docs/bringup.md`](../hardware/docs/bringup.md) sections A–D |

Repeat/long-press and debounce policy live in board YAML (`debounce_ms`, `max_repeat_hz`) and firmware `DEBOUNCE_S`. Same physical button in different remote **sources** may yield different IR payloads — treat source mode as part of the map identity.

## 7. Open work

Do not duplicate session handoff here. See [`STATUS.md`](../STATUS.md) for Decided / Open / next operator commands (firmware flash + vendored HID lib, HID smoke, Amazon matrix, blink worksheet, publish).

## 8. License and publish

MIT ([`LICENSE`](../LICENSE)). Publish notes: [`github-readiness.md`](github-readiness.md). Third-party manuals are not in this tree; do not add the owner’s guide PDF without a copyright decision.
