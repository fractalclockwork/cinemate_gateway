# CineMate remote — physical button inventory

Evidence:

- Face photo: [`cinemate-remote-face.jpg`](cinemate-remote-face.jpg)
- Owner’s guide callouts: [`cinemate-remote-guide-buttons.png`](cinemate-remote-guide-buttons.png)
- AUX+`20636` map: `reports/pico/20261027T043341Z/captures/aux_dvr_20636_map.yaml`

Names below follow the owner’s guide where labeled; otherwise the face print.

## Layout (top → bottom)

| Zone | Buttons (ids) | Notes |
| --- | --- | --- |
| Power / mute | `system_on_off`, `tv_video`, `mute` | White On/Off + Mute are **speaker-always** (Bose). `tv_video` is source/device. |
| Sources | `tv`, `cbl_sat`, `dvd`, `vcr`, `aux` | Select control personality; LED blink = TX under that source. |
| Source On/Off | `tv_on_off`, `cbl_sat_on_off`, `dvd_on_off`, `vcr_on_off`, `aux_on_off` | Mapped AUX On/Off as `on_off`. |
| Nav cluster | `exit`, `page_up`, `page_down`, `menu`, `info`, `guide`, `up`, `down`, `left`, `right`, `enter` | Guide: menu/program buttons follow the selected source. |
| Rockers | `channel_up`, `channel_down`, `volume_up`, `volume_down` | Volume is speaker-always. Channel is device. |
| Transport | `stop`, `pause`, `play`, `frw`, `ffw` | Guide: Scan = rewind/forward. |
| DVR extras | `instant_replay` (= map `back`), `record`, `quick_skip` | Guide names; face print shows curved arrows + red Record. |
| Keypad | `1`…`9`, `0`, `setup`, `previous` | Setup = programming hold; Previous = prior channel. |
| Bottom | `vcr_tv`, `widescreen`, `list`, `a`, `b`, `c` | Face print; A/B/C under List row. |

## AUX + Sony DVR `20636` status

| id | Guide / face | Status |
| --- | --- | --- |
| `on_off` | AUX On/Off | confirmed `1a:15:9a` |
| `up` `down` `left` `right` `enter` | D-pad / ENTER | confirmed |
| `back` | Exit (plan / HID escape) | confirmed `1a:63:9a` |
| `instant_replay` | Instant Replay | confirmed `1a:5b:9a` (same as `previous`) |
| `menu` `guide` | Menu / Guide | confirmed `6f` / `73` |
| `info` | Info | **unbound** |
| `page_up` / `channel_up` | Page▲ / Channel▲ | confirmed `1a:10:9a` (shared IR — amazon keymap: **UP**; see [`amazon-chrome-shortcuts.md`](amazon-chrome-shortcuts.md)) |
| `page_down` / `channel_down` | Page▼ / Channel▼ | confirmed `1a:11:9a` (shared IR — amazon keymap: **DOWN**) |
| `stop` | Stop | **unbound** |
| `pause` `play` `frw` `ffw` | Pause / Play / Scan | confirmed |
| `record` `quick_skip` | Record / Quick Skip | confirmed `1d` / `72` |
| `previous` | Previous | confirmed `1a:5b:9a` (same as `back`) |
| `list` | List | confirmed `2b` |
| `0`…`9` | Numeric | confirmed (`1→0x00`…`9→0x08`, `0→0x09`) |
| `tv_video` `vcr_tv` `widescreen` `a` `b` `c` `setup` | bottom / setup | **unbound** (non-AUX or silent) |

Leftover unlabeled SIRC-20 in catalog: `0b` only.
