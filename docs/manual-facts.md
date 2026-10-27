# Bose CineMate remote — verified facts vs experiments

Primary sources (in this repo):

- [cinemate_cinemate_digital_home_theater_speaker_system.pdf](cinemate_cinemate_digital_home_theater_speaker_system.pdf) — owner’s guide
- [cinemate_remote.pdf](cinemate_remote.pdf) — CineMate Universal Remote Device Codes book

Do not invent IR protocols, device codes, button encodings, or programming steps beyond what these manuals state. Label unknowns and test them.

## Confirmed (manual)

### Product / IR role

- The system includes a **universal infrared (IR) remote** and an **Interface module** that receives IR remote-control signals and provides audio connections (owner’s guide, product features / introduction).
- The Interface module receives commands that turn speakers on, change volume, and mute or turn off the speaker system; place it with clear line of sight to the remote (owner’s guide, “Positioning the Interface module”).

### Source buttons and AUX

- The remote has five **source** buttons: **TV**, **CBL-SAT**, **DVD**, **VCR**, **AUX**. Selecting a source selects which device the remote currently controls (owner’s guide, “Remote control operating guide”, source and input selection; also “Switching control from one device to another”, ~p. 16).
- **AUX** (owner’s guide, ~p. 17): “Selects the AUX source. When the AUX source is selected, the remote will control the functions of a VCR or DVR device that is connected to your AUX jack.” AUX On-Off turns that VCR/DVR on or off.
- Footnote on those source descriptions: **requires programming the remote with a specific device code** (same page).
- Menu/program-selection buttons control **only one source at a time**, depending on which source is selected: TV, CBL-SAT, DVD, VCR, or AUX (owner’s guide, ~p. 18).
- In addition to controlling the selected source, the remote **always** controls basic CineMate speaker functions (on, volume, mute/off) (owner’s guide, ~p. 16).

### Programming this remote (not the reverse)

- The universal remote can be programmed to control TV, cable/satellite, VCR, DVD, and DVR (owner’s guide, “Setting up the remote to control other sources”, ~p. 14).
- Each source needs a **five-digit device code**. Codes are in the Device Codes book included with the product (same section).
- TV setup procedure (~pp. 14–15): hold **Setup** until all five source buttons light → press the **source** button → enter five-digit code → source button blinks twice → test with that source’s On-Off. **Same procedure** for other sources using the appropriate source button and code.
- Invalid key / unavailable code: five source buttons flash rapidly three times; restart programming (note on ~p. 15).
- Combination devices: prefer COMBINATION listings first, then individual types (owner’s guide ~p. 15; Device Codes book intro).
- **Verifying a device code** (owner’s guide, ~p. 21): Setup → source button → Info → press 1…5 and count blinks for each digit → Exit.

### Device Codes book scope

- Book title/context: codes to set up the **CineMate universal remote to control video devices** used with the speaker system; setup procedure is in the owner’s guide (Device Codes book, “Finding the right device codes”).
- Listed headings include **TV, CBL, SAT, DVD, VCR, DVR, DVD-R, ACC**, and combination sections. There is **no separate “AUX” code list**. AUX is a **source button** that holds a programmed code, typically from **VCR** or **DVR** (per AUX description in the owner’s guide).
- These codes are for programming **this Bose remote to operate other brands**. They are **not** codes for programming another brand’s remote to operate Bose equipment, and they are **not** a published IR protocol dump.

## Measured

- Unprogrammed **CBL-SAT**, **DVD**, **VCR**, and **AUX** emit no command encoding (operator determination). Those source buttons do not provide a factory IR personality to map.
- AUX code-check (owner's guide, "Verifying a device code", ~p. 21) previously read Sony DVR `20636` back as blink counts `2, 0, 6, 3, 6`.
- Entering a code on AUX can make the five source buttons flash three times after the fifth digit. The owner's guide calls that pattern an invalid key or an unavailable code (~p. 15). That pattern was seen for `20636` and `21972`; the `20636` digits still read back afterward.
- AUX On-Off while `20636` was stored produced SIRC-20 timings archived as `sony-sirc20:1a:15:9a` in `reports/pico/20261027T032519Z/captures/`. That decode is **rejected** for staged validation (operator: wrong / not usable as `0000`). Do not map buttons from that session.

## Selected programming personality (staged)

**Blink correction:** on this remote, a short flash then two flashes after entering a library code is the **accept** pattern. Programming AUX with TV code `10178` kept that blink sequence and AUX On-Off controlled the TV. Earlier “three-flash = reject” readings for AUX/VCR attempts were wrong for this unit.

**Source LED = IR TX activity (operator):** while a source is selected (TV / VCR / AUX, etc.), that source’s LED blinks when a press actually transmits an IR command. No blink ⇒ that button does not emit under the programmed personality (do not wait on the CHQ1838 for it).

**TV** code-check: `10178`. TV controls work.

**Unique capture (current):** AUX holds Sony DVR **`20636`** (`sony-dvr-20636`, code-check `2,0,6,3,6`). Also free to press **TV** `10178`. `HUMAN_VERIFY=1 make capture FRESH=1` is listen-only (no prompts); press keys freely, Ctrl+C when done. Map button→code afterwards from `unique_codes.json`.

- Session `reports/pico/20261027T043341Z/captures/`: listen-only unique catalog (~47 unique / 105 hits).
- **Operator protocol split:**
  - `sony-sirc20:*` → AUX / Sony DVR `20636` device commands (**28** unique keys, address `0x1a` / extended `0x9a`; report `…/aux_dvr_20636_sirc20.md`, map `…/aux_dvr_20636_map.yaml`)
  - `nec-like:*` → TV `10178` commands
  - `unclassified` → **Bose / CineMate speaker-always** (e.g. volume)
- Guided confirm for AUX+20636 (operator-present): digits `1→0x00`…`9→0x08`, `0→0x09`; nav up `5f`, down `60`, right `61`, left `62`, enter `5e`, **back=Exit** `63`, menu `6f`, guide `73`, page/ch `10`/`11`, Instant Replay/previous `5b`, on_off `15`; transport pause `19`, play `1a`, frw `1b`, ffw `1c`, record `1d`, quick_skip `72`, list `2b`. Plan-wave **stop** unbound. On-Off confirmed in `software/profiles/remote.yaml`; wave evidence `reports/pico/20261027T043341Z/captures/{validated,buttons}.json` and `keymap.*.yaml`. Inventory: [`docs/remote/button-inventory.md`](remote/button-inventory.md).
- VCR catch-all `20000` abandoned: external decoder only saw up/down. Archive `reports/pico/20261027T040450Z/captures/`.

## Must test (unknown until measured)

- Whether the same physical button yields **different** IR payloads across sources.
- Full Bose speaker-always set (on/off/vol/mute) once unclassified frames are decoded; interaction with HID volume on the PC.
- Auto-repeat / long-press timing and whether the Pico should suppress or map repeats.
- Exact IR receiver/LED electrical levels once parts are chosen (see `hardware/docs/boards/pico.md`).

## Phase 1 policy for this project

- Prefer **receiving and decoding** the original remote; do not TX toward the CineMate Interface module in phase 1.
- IR LED on the Pico is for **HWIL optical loopback** (and future TX), not for controlling the amp yet.
- Map AUX-mode presses to ordinary **USB HID** keyboard/media keys for Chrome on Linux. No streaming-site APIs, DRM bypass, or account automation.
