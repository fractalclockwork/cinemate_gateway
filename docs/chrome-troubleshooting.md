# Chrome / Linux HID troubleshooting

Phase 1: Pico appears as a USB keyboard + consumer-control device. Focus the Chrome tab that should receive keys.

## Checklist

| Symptom | What to check |
| --- | --- |
| Missed IR presses | Line of sight to IR RX; ambient IR/sun; wrong carrier; `MODE=capture` shows pulses; debounce too aggressive |
| Repeated / stuck keys | Remote auto-repeat; lower `max_repeat_hz` / raise `debounce_ms` in board YAML + firmware `DEBOUNCE_S` |
| Keys go nowhere | Chrome (or OS) focus not on the player tab; another window stole focus |
| Browser conflicts | Avoid mapping to Ctrl/Alt/Super chords; Escape may exit fullscreen — intentional for “back” |
| Volume surprises | Consumer Volume hits **system** volume; page players may use separate volume. Prefer Space/media for playback; consider ignoring speaker-always Bose vol codes once identified |
| Accidental OS shortcuts | Do not bind media keys that launch desktop overlays if undesired; trim `software/keymap.yaml` |
| Source does nothing | AUX + Sony DVR **20636** is the staged map personality (TV source **10178** is separate). Code-check AUX (`2,0,6,3,6`); log blinks on the worksheet. Capture On-Off before other buttons. Short+double flash after entry is the **reported** accept pattern on this unit — see blink worksheet / manual-facts |
| Same button, wrong action | Source mode not AUX; speaker-always codes overlapping; update ignore list |

## Quick verification

1. Open a plain text field or [keyboard event test page](https://w3c.github.io/uievents/tools/key-event-viewer.html) in Chrome.
2. Press AUX on the remote, then arrows / OK / Exit.
3. Confirm HID events match `software/keymap.yaml` (or the example map during SIL).

## Phase 2 (deferred)

A LAN web app may later drive the Pico to TX CineMate on/off/vol and inject the same HID map remotely. That needs new assent (`HUMAN_TX`) and must not be confused with phase-1 loopback-only LED use. See root `README.md`.
