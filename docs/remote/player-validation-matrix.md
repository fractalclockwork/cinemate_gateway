# Per-player control validation matrix

Record observed results. IR identity can be confirmed before HID; Chrome/player rows need on-device HID smoke first.

**Remote mode:** AUX + Sony DVR `20636` unless noted.  
**IR evidence:** `reports/pico/20261027T043341Z/captures/` (`validated.json`, `aux_dvr_20636_map.yaml`).  
**Profiles:** [`software/profiles/`](../../software/profiles/). Active host keymap: **kanopy**.

Status values: `pass` | `fail` | `blocked` | `unbound` | `not_run`.

Columns: player, button, remote_mode, frame_key, mapped_hid, expected_ui, actual, status, evidence.

## Kanopy (priority)

Profile: [`software/profiles/kanopy.yaml`](../../software/profiles/kanopy.yaml). Source: https://help.kanopy.com/en-us/4140.htm

| player | button | remote_mode | frame_key | mapped_hid | expected_ui | actual | status | evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| kanopy | up | AUX/20636 | sony-sirc20:1a:5f:9a | UP | arrow | | not_run | IR confirmed; HID/Chrome pending on-device firmware |
| kanopy | down | AUX/20636 | sony-sirc20:1a:60:9a | DOWN | arrow | | not_run | IR confirmed; HID/Chrome pending |
| kanopy | left | AUX/20636 | sony-sirc20:1a:62:9a | LEFT | seek_back | | not_run | IR confirmed; HID/Chrome pending |
| kanopy | right | AUX/20636 | sony-sirc20:1a:61:9a | RIGHT | seek_forward | | not_run | IR confirmed; HID/Chrome pending |
| kanopy | enter | AUX/20636 | sony-sirc20:1a:5e:9a | ENTER | activate | | not_run | IR confirmed; HID/Chrome pending |
| kanopy | back | AUX/20636 | sony-sirc20:1a:63:9a | ESCAPE | exit_fullscreen | | not_run | IR confirmed; HID/Chrome pending |
| kanopy | play | AUX/20636 | sony-sirc20:1a:1a:9a | SPACE | play_pause | | not_run | IR confirmed; HID/Chrome pending |
| kanopy | pause | AUX/20636 | sony-sirc20:1a:19:9a | SPACE | play_pause | | not_run | IR confirmed; HID/Chrome pending |
| kanopy | ffw | AUX/20636 | sony-sirc20:1a:1c:9a | RIGHT | seek_forward | | not_run | IR confirmed; HID/Chrome pending |
| kanopy | frw | AUX/20636 | sony-sirc20:1a:1b:9a | LEFT | seek_back | | not_run | IR confirmed; HID/Chrome pending |
| kanopy | stop | AUX/20636 | — | — | unbound | no IR TX | unbound | Stop silent on this personality |
| kanopy | 0–9 | AUX/20636 | see map | null | unbound | | unbound | Digits IR-confirmed; profile leaves HID null |

## Amazon Prime Video

Profile: [`software/profiles/amazon.yaml`](../../software/profiles/amazon.yaml). Fill after Kanopy HID smoke.

| player | button | remote_mode | frame_key | mapped_hid | expected_ui | actual | status | evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| amazon | _(rows TBD)_ | AUX/20636 | | | | | not_run | Switch keymap `profile:` + redeploy when testing |

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

1. Confirm IR `frame_key` (already done for Kanopy nav/transport above).
2. Ensure on-device firmware maps that key to `mapped_hid` and `adafruit_hid` is installed.
3. Focus the player (or key-event viewer for HID smoke).
4. Press the remote button; write **actual** and **status**; point **evidence** at a note, screenshot path, or report stamp.
