# Per-player control validation matrix

Record observed results. IR identity can be confirmed before HID; Chrome/player rows need on-device HID smoke first.

**Remote mode:** AUX + Sony DVR `20636` unless noted.  
**IR evidence:** `reports/pico/20261027T043341Z/captures/` (`validated.json`, `aux_dvr_20636_map.yaml`).  
**Profiles:** [`software/profiles/`](../../software/profiles/). Active host keymap: **amazon**.  
**Amazon shortcuts / IR conflict notes:** [`amazon-chrome-shortcuts.md`](amazon-chrome-shortcuts.md).

Status values: `pass` | `fail` | `blocked` | `unbound` | `not_run`.

Columns: player, button, remote_mode, frame_key, mapped_hid, expected_ui, actual, status, evidence.

## Amazon Prime Video (priority)

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
| amazon | channel_up (page_up alias) | AUX/20636 | sony-sirc20:1a:10:9a | TAB | focus_next | | not_run | Shared IR with page_up — see shortcuts doc |
| amazon | channel_down (page_down alias) | AUX/20636 | sony-sirc20:1a:11:9a | SHIFT_TAB | focus_prev | | not_run | Shared IR with page_down |
| amazon | stop | AUX/20636 | — | — | unbound | no IR TX | unbound | Stop silent on this personality |
| amazon | 0–9 | AUX/20636 | see map | null | unbound | | unbound | Digits IR-confirmed; profile leaves HID null |

## Kanopy (deferred)

Profile: [`software/profiles/kanopy.yaml`](../../software/profiles/kanopy.yaml). Source: https://help.kanopy.com/en-us/4140.htm  
Fill after Amazon HID smoke; switch keymap `profile:` + redeploy when testing.

| player | button | remote_mode | frame_key | mapped_hid | expected_ui | actual | status | evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| kanopy | up | AUX/20636 | sony-sirc20:1a:5f:9a | UP | arrow | | not_run | IR confirmed; deferred behind amazon |
| kanopy | down | AUX/20636 | sony-sirc20:1a:60:9a | DOWN | arrow | | not_run | IR confirmed; deferred |
| kanopy | left | AUX/20636 | sony-sirc20:1a:62:9a | LEFT | seek_back | | not_run | IR confirmed; deferred |
| kanopy | right | AUX/20636 | sony-sirc20:1a:61:9a | RIGHT | seek_forward | | not_run | IR confirmed; deferred |
| kanopy | enter | AUX/20636 | sony-sirc20:1a:5e:9a | ENTER | activate | | not_run | IR confirmed; deferred |
| kanopy | back | AUX/20636 | sony-sirc20:1a:63:9a | ESCAPE | exit_fullscreen | | not_run | IR confirmed; deferred |
| kanopy | play | AUX/20636 | sony-sirc20:1a:1a:9a | SPACE | play_pause | | not_run | IR confirmed; deferred |
| kanopy | pause | AUX/20636 | sony-sirc20:1a:19:9a | SPACE | play_pause | | not_run | IR confirmed; deferred |
| kanopy | ffw | AUX/20636 | sony-sirc20:1a:1c:9a | RIGHT | seek_forward | | not_run | IR confirmed; deferred |
| kanopy | frw | AUX/20636 | sony-sirc20:1a:1b:9a | LEFT | seek_back | | not_run | IR confirmed; deferred |
| kanopy | stop | AUX/20636 | — | — | unbound | no IR TX | unbound | Stop silent on this personality |
| kanopy | 0–9 | AUX/20636 | see map | null | unbound | | unbound | Digits IR-confirmed; profile leaves HID null |

## Paramount+

Profile: [`software/profiles/paramount.yaml`](../../software/profiles/paramount.yaml).

| player | button | remote_mode | frame_key | mapped_hid | expected_ui | actual | status | evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| paramount | _(rows TBD)_ | AUX/20636 | | | | | not_run | |

## YouTube TV

Profile: [`software/profiles/youtubetv.yaml`](../../software/profiles/youtubetv.yaml).

| player | button | remote_mode | frame_key | mapped_hid | expected_ui | actual | status | evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| youtubetv | _(rows TBD)_ | AUX/20636 | | | | | not_run | Many controls unbound in profile by design |

## How to run a row

1. Confirm IR `frame_key` (already done for Amazon nav/transport/quick_skip/page-channel above).
2. Ensure on-device firmware maps that key to `mapped_hid` (`make firmware` ships vendored `adafruit_hid`).
3. Focus the player (or key-event / pointer test page for HID smoke). For click rows, move the pointer onto the control first.
4. Press the remote button; write **actual** and **status**; point **evidence** at a note, screenshot path, or report stamp.
