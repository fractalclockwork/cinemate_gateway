# Per-player control validation matrix

Record observed results. IR identity can be confirmed before HID; Chrome/player rows need on-device HID smoke first.

**Remote mode:** AUX + Sony DVR `20636` unless noted.  
**IR evidence:** `reports/pico/20261027T043341Z/captures/` (`validated.json`, `aux_dvr_20636_map.yaml`).  
**Profiles:** [`software/profiles/`](../../software/profiles/). Active host keymap: **amazon**.  
**Multi-source slots** (face left → right): [ADR 004](../decisions/004-multi-source-personalities.md) — TV/`10178` (no player), CBL-SAT/`21033`→paramount, DVD/`20533`→kanopy, VCR/`20033`→youtubetv, AUX/`20636`→amazon.  
**Amazon shortcuts / IR conflict notes:** [`amazon-chrome-shortcuts.md`](amazon-chrome-shortcuts.md).

Status values: `pass` | `fail` | `blocked` | `unbound` | `not_run`.

Columns: player, button, remote_mode, frame_key, mapped_hid, expected_ui, actual, status, evidence.

## Paramount+ (CBL-SAT / `21033`)

Profile: [`software/profiles/paramount.yaml`](../../software/profiles/paramount.yaml) (`remote: cblsat-21033`).  
SIRC-20 `1a:cmd:62` (unique) + some `1a:cmd:49` shared with DVD ([ADR 004](../decisions/004-multi-source-personalities.md)).

| player | button | remote_mode | frame_key | mapped_hid | expected_ui | actual | status | evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| paramount | _(label + map next)_ | CBL-SAT/21033 | `1a:*:62` / shared `:49` | | | | not_run | tio probe 2026-10-28 |

## Kanopy (DVD / `20533`)

Profile: [`software/profiles/kanopy.yaml`](../../software/profiles/kanopy.yaml) (`remote: dvd-20533`). Source: https://help.kanopy.com/en-us/4140.htm  
SIRC-20 `1a:cmd:49` (includes stop). Do not reuse AUX `1a:*:9a` frames.

| player | button | remote_mode | frame_key | mapped_hid | expected_ui | actual | status | evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| kanopy | _(rows after labeled map)_ | DVD/20533 | `1a:*:49` | | | | not_run | tio probe 2026-10-28 |

## YouTube TV (VCR / `20033`)

Profile: [`software/profiles/youtubetv.yaml`](../../software/profiles/youtubetv.yaml) (`remote: vcr-20033`). Purpose + HID mirror amazon ([ADR 003](../decisions/003-vcr-youtubetv-personality.md), [`youtubetv-chrome-shortcuts.md`](youtubetv-chrome-shortcuts.md)). IR: SIRC-12 `2:cmd`.

| player | button | remote_mode | frame_key | mapped_hid | expected_ui | actual | status | evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| youtubetv | play | VCR/20033 | sony-sirc12:2:1a | SPACE | play_pause | | not_run | |
| youtubetv | pause | VCR/20033 | sony-sirc12:2:19 | SPACE | play_pause | | not_run | operator: pause OK |
| youtubetv | ffw | VCR/20033 | sony-sirc12:2:1c | RIGHT | seek_forward | | not_run | |
| youtubetv | frw | VCR/20033 | sony-sirc12:2:1b | LEFT | seek_back | | not_run | operator: left/right seek OK |
| youtubetv | record | VCR/20033 | sony-sirc12:2:1d | F | fullscreen | | not_run | |
| youtubetv | up | VCR/20033 | sony-sirc12:2:42 | MOUSE_UP | pointer_up | | not_run | labeled unmapped (2,66) |
| youtubetv | down | VCR/20033 | sony-sirc12:2:43 | MOUSE_DOWN | pointer_down | | not_run | labeled unmapped (2,67) |
| youtubetv | left | VCR/20033 | sony-sirc12:2:62 | MOUSE_LEFT | pointer_left | | not_run | hid seen in tio |
| youtubetv | right | VCR/20033 | sony-sirc12:2:61 | MOUSE_RIGHT | pointer_right | | not_run | hid seen in tio |
| youtubetv | enter | VCR/20033 | sony-sirc12:2:51 | MOUSE_LEFT_CLICK | click | | not_run | labeled unmapped (2,81) |
| youtubetv | back | VCR/20033 | sony-sirc12:2:2a | ESCAPE | exit_playback | | not_run | labeled unmapped (2,42) |
| youtubetv | instant_replay | VCR/20033 | sony-sirc12:b4:5b | SHIFT_ALT_TAB | switch_window_prev | | not_run | labeled unmapped (180,91) |
| youtubetv | quick_skip | VCR/20033 | — | — | unbound | no IR TX | unbound | forward curve silent on 20033 |
| youtubetv | channel_up | VCR/20033 | sony-sirc12:2:10 | UP | arrow_up | | not_run | hold accelerates 0.40→0.08 s |
| youtubetv | channel_down | VCR/20033 | sony-sirc12:2:11 | DOWN | arrow_down | | not_run | |
| youtubetv | page_up | VCR/20033 | sony-sirc15:b4:60 | PAGE_UP | page_up | | not_run | distinct from channel; hold accelerates |
| youtubetv | page_down | VCR/20033 | sony-sirc15:b4:62 | PAGE_DOWN | page_down | | not_run | |

## Amazon Prime Video (AUX / `20636`)

Profile: [`software/profiles/amazon.yaml`](../../software/profiles/amazon.yaml). Source: https://www.primevideo.com/help?nodeId=GE4VW9VWJD7FM6DR  
Procedure: focus Chrome on a playing Prime title, then press the remote.

| player | button | remote_mode | frame_key | mapped_hid | expected_ui | actual | status | evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| amazon | play | AUX/20636 | sony-sirc20:1a:1a:9a | SPACE | play_pause | key-event viewer: keydown, keypress, beforeinput, input, keyup (one Space) | not_run | HID smoke `reports/pico/20261027T215244Z/hid-listen.jsonl` 21:58:09Z frame (26, 26, 154) → Space. Prime play/pause UI not observed yet |
| amazon | pause | AUX/20636 | sony-sirc20:1a:19:9a | SPACE | play_pause | | not_run | IR confirmed; HID/Chrome pending |
| amazon | quick_skip | AUX/20636 | sony-sirc20:1a:72:9a | ALT_TAB | switch_window | | not_run | IR confirmed; was fullscreen, remapped |
| amazon | instant_replay | AUX/20636 | sony-sirc20:1a:5b:9a | SHIFT_ALT_TAB | switch_window_prev | | not_run | IR confirmed (same frame as previous) |
| amazon | record | AUX/20636 | sony-sirc20:1a:1d:9a | F | fullscreen | | not_run | IR confirmed; fullscreen moved off quick_skip |
| amazon | back | AUX/20636 | sony-sirc20:1a:63:9a | ESCAPE | exit_playback | | not_run | IR confirmed; HID/Chrome pending |
| amazon | ffw | AUX/20636 | sony-sirc20:1a:1c:9a | RIGHT | seek_forward | | not_run | Repeats ~3/s while held |
| amazon | frw | AUX/20636 | sony-sirc20:1a:1b:9a | LEFT | seek_back | | not_run | Repeats ~3/s while held |
| amazon | up | AUX/20636 | sony-sirc20:1a:5f:9a | MOUSE_UP | pointer_up | | not_run | IR confirmed; HID/Chrome pending |
| amazon | down | AUX/20636 | sony-sirc20:1a:60:9a | MOUSE_DOWN | pointer_down | | not_run | IR confirmed; HID/Chrome pending |
| amazon | left | AUX/20636 | sony-sirc20:1a:62:9a | MOUSE_LEFT | pointer_left | | not_run | IR confirmed; HID/Chrome pending |
| amazon | right | AUX/20636 | sony-sirc20:1a:61:9a | MOUSE_RIGHT | pointer_right | | not_run | IR confirmed; HID/Chrome pending |
| amazon | enter | AUX/20636 | sony-sirc20:1a:5e:9a | MOUSE_LEFT_CLICK | click | | not_run | Pointer must be over control first |
| amazon | channel_up (page_up alias) | AUX/20636 | sony-sirc20:1a:10:9a | UP | arrow_up | | not_run | Shared IR with page_up; hold accelerates |
| amazon | channel_down (page_down alias) | AUX/20636 | sony-sirc20:1a:11:9a | DOWN | arrow_down | | not_run | Shared IR with page_down |
| amazon | stop | AUX/20636 | — | — | unbound | no IR TX | unbound | Stop silent on this personality |
| amazon | 0–9 | AUX/20636 | see map | null | unbound | | unbound | Digits IR-confirmed; profile leaves HID null |

## How to run a row

1. Confirm IR `frame_key` (already done for Amazon nav/transport/quick_skip/page-channel above).
2. Ensure on-device firmware maps that key to `mapped_hid` (`make firmware` ships vendored `adafruit_hid`).
3. Focus the player (or key-event / pointer test page for HID smoke). For click rows, move the pointer onto the control first.
4. Press the remote button; write **actual** and **status**; point **evidence** at a note, screenshot path, or report stamp.
