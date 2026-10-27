# Specification — ir-remote-bose

Normative product and system requirements for this repository. Living session state belongs in [`STATUS.md`](../STATUS.md). Manual-derived facts belong in [`manual-facts.md`](manual-facts.md). Process/roles belong in [`methodology/`](methodology/) and root [`AGENTS.md`](../AGENTS.md).

An early chat brief (`PROMPT.md`) was retired in favor of this document.

## 1. Purpose

Build a personal **remote-control gateway**:

1. Receive IR from the **Bose CineMate Digital Home Theater** universal remote in **AUX** mode.
2. Decode on a **Raspberry Pi Pico**.
3. Inject ordinary **USB HID** keyboard and/or consumer-control (media) events into a host PC.
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
| Assent | Physical bench work requires operator `HUMAN_VERIFY` (and `HUMAN_FLASH` / `HUMAN_IR_PATH` where applicable). Agents must not invent assent. |

### Staged remote personality (Decided)

- **AUX:** Sony DVR library code **`20636`** (`sony-dvr-20636`), measured as Sony SIRC-20.
- **TV (separate source):** **`10178`**.
- Details: [`decisions/001-aux-personality-20636.md`](decisions/001-aux-personality-20636.md), [`software/profiles/remote.yaml`](../software/profiles/remote.yaml).

## 4. Architecture (Decided)

| Layer | Choice |
| --- | --- |
| MCU | Raspberry Pi Pico, **CircuitPython** |
| Host interface | Pico enumerates as **USB HID** keyboard + consumer control (not a host-side serial daemon for Phase 1) |
| IR RX / TX pins | **GP14** RX, **GP15** TX (TX held low in Phase 1) — [`hardware/boards/pico.yaml`](../hardware/boards/pico.yaml) |
| Decode | Thin on-device Sony SIRC; host SIL helpers in [`software/decode.py`](../software/decode.py) |
| Keymap | Host [`software/keymap.yaml`](../software/keymap.yaml) → `make firmware-keymap` → [`hardware/firmware/pico/keymap_gen.py`](../hardware/firmware/pico/keymap_gen.py) |
| App profiles | Per-player HID encodings under [`software/profiles/`](../software/profiles/) (kanopy active) |
| Roles | Evidence-gated trees: `human/`, `hardware/`, `software/`, `environment/`, `harness/`, `lesson/` — see [`AGENTS.md`](../AGENTS.md) |

Hardware bring-up and pin/electrical caveats: [`hardware/docs/boards/pico.md`](../hardware/docs/boards/pico.md), [`hardware/docs/bringup.md`](../hardware/docs/bringup.md). Protoboard: [`kicad/ir-gateway/`](kicad/ir-gateway/).

## 5. Phases

### Phase 1 (current)

- RX Bose remote → decode → HID → Chrome.
- IR LED = optical **loopback** only (not Interface TX).
- Capture / confirm-map produce IR identity evidence; HID smoke and player validation follow on-device firmware deploy.

### Phase 2 (deferred)

- Small web app to drive the Pico for (a) IR TX of CineMate on/off/vol and (b) the same browser HID controls.
- Requires capture library, TX under `max_ir_tx_*` ceilings, and new assent (`HUMAN_TX`) before aiming at the Interface module.

## 6. Evidence and validation

| Concern | Where |
| --- | --- |
| Manual vs measured facts | [`manual-facts.md`](manual-facts.md) |
| IR button map / inventory | [`remote/button-inventory.md`](remote/button-inventory.md), `reports/pico/*/captures/` (local, gitignored) |
| Physical IR map gate | `harness.ready.require_ir_map` (needs `validated.json`) |
| SIL `image` stage | **Not** live IR — `sil-hid-fixture` only; unlocks lessons via `require_image` |
| Optical loopback | `make loopback` + `HUMAN_IR_PATH` |
| Player control matrix | [`remote/player-validation-matrix.md`](remote/player-validation-matrix.md) |
| Blink / programming LEDs | [`remote/blink-observation-worksheet.md`](remote/blink-observation-worksheet.md), [`decisions/002-blink-observation-protocol.md`](decisions/002-blink-observation-protocol.md) |
| Chrome / HID troubleshooting | [`chrome-troubleshooting.md`](chrome-troubleshooting.md) |
| Bring-up ladder (IR without HID) | [`hardware/docs/bringup.md`](../hardware/docs/bringup.md) sections A–D |

Repeat/long-press and debounce policy live in board YAML (`debounce_ms`, `max_repeat_hz`) and firmware `DEBOUNCE_S`. Same physical button in different remote **sources** may yield different IR payloads — treat source mode as part of the map identity.

## 7. Open work

Do not duplicate session handoff here. See [`STATUS.md`](../STATUS.md) for Decided / Open / next operator commands (firmware flash, `adafruit_hid`, HID smoke, Kanopy matrix, blink worksheet, publish).

## 8. License and publish

MIT ([`LICENSE`](../LICENSE)). Publish notes: [`github-readiness.md`](github-readiness.md). Third-party manuals under `docs/*.pdf` need a human copyright decision before a public remote.
