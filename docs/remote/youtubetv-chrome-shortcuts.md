# YouTube TV + Chrome shortcuts (gateway)

VCR mode on the Bose remote maps to the **youtubetv** profile. Button **purpose** and initial HID mirror the Amazon/AUX map so the same face keys feel the same.

**Profile:** [`software/profiles/youtubetv.yaml`](../../software/profiles/youtubetv.yaml) (`remote: vcr-20033`).  
**ADR:** [`../decisions/003-vcr-youtubetv-personality.md`](../decisions/003-vcr-youtubetv-personality.md), multi-source [`../decisions/004-multi-source-personalities.md`](../decisions/004-multi-source-personalities.md).  
**Matrix:** [`player-validation-matrix.md`](player-validation-matrix.md).  
**Amazon reference (purpose):** [`amazon-chrome-shortcuts.md`](amazon-chrome-shortcuts.md).

Face left → right: TV / **CBL-SAT**→paramount (`21033`) / **DVD**→kanopy (`20533`) / **VCR**→youtubetv (`20033`) / **AUX**→amazon (`20636`) — [ADR 004](../decisions/004-multi-source-personalities.md).

## Published player behaviour (tv.youtube.com in Chrome)

Space / K play-pause; Left/J rewind; Right/L forward; F fullscreen; Esc back/exit menu. Same HID choices as Amazon therefore apply. Focus the player before testing — Space otherwise activates the last-clicked control.

## Gateway binding (VCR + `20033`)

Labeled from map-mode `unmapped` dump 2026-10-28 (one press each).

| Remote button | Frame key | HID | Intent |
| --- | --- | --- | --- |
| play / pause | `sony-sirc12:2:1a` / `2:19` | Space | Play/pause |
| ffw / frw | `2:1c` / `2:1b` | Right / Left | Seek; hold accelerates like d-pad |
| record | `2:1d` | F | Fullscreen |
| up / down | `2:42` / `2:43` | Mouse move | Pointer (cmds differ from AUX) |
| left / right | `2:62` / `2:61` | Mouse move | Pointer |
| enter | `2:51` | Mouse left click | Activate under pointer |
| back (Exit) | `2:2a` | Escape | Exit / back |
| instant_replay | `sony-sirc12:b4:5b` raw `(180, 91)` | Shift+Alt+Tab | Previous window (one direction) |
| quick_skip | — | unbound | No IR on this personality |
| channel | `2:10` / `2:11` | **Up / Down** | Hold accelerates 0.40→0.08 s |
| page | `b4:60` / `b4:62` (SIRC-15) | **Page Up / Page Down** | Distinct from channel; same hold ramp |
| stop / digits | `2:18`, `2:0`…`2:9` | unbound | Mirror amazon |

Union map: [`software/keymap.yaml`](../../software/keymap.yaml). AUX `1a:*:9a` untouched.

## Operator check order — full HID pass

Focus a playing **tv.youtube.com** title; remote on **VCR**. Report what the picture did for each row (matrix stays `not_run` until then).

1. play / pause → Space  
2. ffw / frw hold → seek  
3. record → F fullscreen  
4. d-pad + enter → pointer + click  
5. back → Escape  
6. instant_replay → previous window (one-way; quick_skip silent)  
7. channel hold → Up / Down; page hold → Page Up / Page Down  
8. Optional AUX regress on Prime if anything feels off
