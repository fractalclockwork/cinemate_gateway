# Chrome / Linux HID troubleshooting

Phase 1: Pico appears as a USB **keyboard + consumer-control + mouse**. Focus the Chrome tab that should receive keys and pointer events.

Amazon shortcut tables and page/channel IR notes: [`remote/amazon-chrome-shortcuts.md`](remote/amazon-chrome-shortcuts.md).

## Checklist

| Symptom | What to check |
| --- | --- |
| Missed IR presses | Line of sight to IR RX; ambient IR/sun; wrong carrier; `MODE=capture` shows pulses; debounce too aggressive |
| Repeated / stuck keys | Remote auto-repeat; lower `max_repeat_hz` / raise `debounce_ms` in board YAML + firmware `DEBOUNCE_S` |
| Keys go nowhere | Chrome (or OS) focus not on the player tab; another window stole focus |
| Click does nothing | Pointer not over the control — amazon d-pad moves the mouse; Enter is left-click only |
| Browser conflicts | Escape may exit fullscreen — intentional for “back”. Alt+Tab is only the Quick Skip / Instant Replay window switch |
| Volume surprises | Consumer Volume hits **system** volume; page players may use separate volume. Prefer Space/media for playback; consider ignoring speaker-always Bose vol codes once identified |
| Accidental OS shortcuts | Do not bind media keys that launch desktop overlays if undesired; trim `software/keymap.yaml` |
| Source does nothing | AUX + Sony DVR **20636** is the staged map personality (TV source **10178** is separate). Code-check AUX (`2,0,6,3,6`); log blinks on the worksheet. Capture On-Off before other buttons. Short+double flash after entry is the **reported** accept pattern on this unit — see blink worksheet / manual-facts |
| Same button, wrong action | Source mode not AUX; speaker-always codes overlapping; update ignore list |
| ImportError after flash | `adafruit_hid` must be under `CIRCUITPY/lib/` — `make firmware` vendors and copies it; redeploy if missing |

## Quick verification

1. Open a plain text field or [keyboard event test page](https://w3c.github.io/uievents/tools/key-event-viewer.html) in Chrome for keys; watch the OS pointer for mouse moves.
2. Press AUX on the remote, then d-pad / OK (click) / Exit / play / quick_skip.
3. Confirm HID events match `software/keymap.yaml` (amazon: mouse on d-pad, Space/F/Esc/Tab as documented).

## Phase 2 (deferred)

A LAN web app may later drive the Pico to TX CineMate on/off/vol and inject the same HID map remotely. That needs new assent (`OPERATOR_TX`) and must not be confused with phase-1 loopback-only LED use. See root `README.md`.
