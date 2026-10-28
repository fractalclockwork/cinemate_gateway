# Amazon Prime + Chrome shortcuts (gateway)

Durable reference for the **amazon** keymap and operator validation. Prefer ordinary HID; no browser automation.

**Active map:** [`software/keymap.yaml`](../../software/keymap.yaml) (`profile: amazon`).  
**Profile:** [`software/profiles/amazon.yaml`](../../software/profiles/amazon.yaml).  
**Matrix:** [`player-validation-matrix.md`](player-validation-matrix.md).  
**Chrome focus tips:** [`../chrome-troubleshooting.md`](../chrome-troubleshooting.md).

## Published Prime Video player shortcuts

Source: [Keyboard Shortcuts on Prime Video](https://www.primevideo.com/help?nodeId=GE4VW9VWJD7FM6DR) (web / Windows / macOS apps).

| Key | Player action |
| --- | --- |
| **Space** | Play / pause |
| **F** | Enter or exit fullscreen (macOS: Fn+F) |
| **Esc** | Exit fullscreen or exit playback |
| **Left** | Rewind ~10 s |
| **Right** | Fast-forward ~10 s |
| **Up** / **Down** | Raise / lower *player* volume |
| **M** | Mute toggle |
| **C** | Captions on/off; cycle subtitle languages |
| **A** | Cycle audio tracks (incl. descriptions / Dialogue Boost) |

There is **no** published keyboard shortcut for “Next episode.” Sparse UI (Next, rows) is handled with the **pointer** (d-pad mouse move + Enter click) on this gateway.

## Gateway binding (AUX + Sony DVR `20636`)

| Remote button | Frame key | HID | Intent |
| --- | --- | --- | --- |
| play / pause | `…:1a:9a` / `…:19:9a` | Space | Play/pause. Needs the player focused; Quick Skip (Alt+Tab) moves focus away |
| quick_skip (forward) | `…:72:9a` | **Alt+Tab** | Next window |
| instant_replay (backward) | `…:5b:9a` | **Shift+Alt+Tab** | Previous window |
| record | `…:1d:9a` | **F** | Fullscreen |
| back (Exit) | `…:63:9a` | Escape | Exit fullscreen/playback |
| ffw / frw | `…:1c:9a` / `…:1b:9a` | Right / Left | Seek (±10 s); repeats about 3 times a second while held |
| up / down / left / right | `…:5f`…`62` | Mouse move (5 px for 0.25 s, ramps to 24 px by 1.2 s) | Point at sparse UI |
| enter | `…:5e:9a` | Mouse left click | Activate under pointer |
| page▲ / channel▲ | `…:10:9a` (**shared**) | **Up** | SEEK_KEYS ramp; AUX remote only IR-repeats a few times while held |
| page▼ / channel▼ | `…:11:9a` (**shared**) | **Down** | Pair with Up; continuous hold-repeat needs VCR `20033` |

Seek stays on **transport** (ffw/frw). D-pad does **not** send arrow keys on the amazon map (d-pad is mouse).

### Page / channel IR conflict

Inventory and AUX+`20636` capture (2026-10-28) treat **page_up** and **channel_up** as one IR payload (`sony-sirc20:1a:10:9a`), and **page_down** / **channel_down** as `…:1a:11:9a` (page vs channel presses logged as `[dup]`). One frame key can have only one HID action.

| Face / guide labels | Shared IR | Chosen HID | Why |
| --- | --- | --- | --- |
| Page▲ / Channel▲ | `1a:10:9a` | Up | Matches VCR channel feel; hold ramp |
| Page▼ / Channel▼ | `1a:11:9a` | Down | Pair with Up |

Profile leaves `page_up` / `page_down` HID `null` (`ui: alias_channel_*_ir`) so export stays unique. VCR page is distinct SIRC-15 (`b4:60`/`b4:62` → Page Up/Down) and **keeps repeating while held**; AUX rocker does not (library personality).

## Useful Chrome / Linux shortcuts (operator)

Focus the Prime tab before testing. The Pico is keyboard + consumer + **mouse**.

| Shortcut | Use with this gateway |
| --- | --- |
| Click tab / Alt+Tab | Put focus on Chrome (and the Prime tab) |
| Ctrl+Tab / Ctrl+Shift+Tab | Cycle Chrome tabs (OS/browser; not mapped from remote) |
| F11 | Chrome window fullscreen (distinct from player **F**) |
| Esc | Leave browser fullscreen / dismiss overlays; also our remote **back** |
| Up / Down | Shared page/channel IR — accelerating arrow repeat |
| Space | Page scroll when focus is not on the player — ensure player/page has focus |
| Pointer over control, then click | Required for Next / sparse buttons (d-pad + enter) |

Quick Skip and Instant Replay are the Alt+Tab window-switch chords above. Other remote keys stay off Ctrl/Alt/Super. Consumer Volume hits **system** volume; Prime also has in-player volume via Up/Down on the *published* keyboard map (not used for d-pad here).

## Operator check order

1. `make check` and `make firmware-keymap`.
2. With CircuitPython UF2 present and `CIRCUITPY` mounted: `OPERATOR_VERIFY=1 OPERATOR_FLASH=1 make firmware` (deploys `lib/adafruit_hid`).
3. Unplug/replug — HID must still work without reinstalling libs.
4. Focus Prime playing a title → play/pause, record→F, transport seek, d-pad+enter for Next, page/channel rocker→Up/Down. Quick Skip / Instant Replay switch windows.
5. Fill Amazon rows in the player validation matrix.
