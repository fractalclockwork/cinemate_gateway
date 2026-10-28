# STATUS — ir-remote-bose

Living handoff. Agents: read this before broad search. Update at end of each session.

Source buttons left → right: **TV / CBL-SAT / DVD / VCR / AUX**.

## Decided — all source modes

| Bose source | Profile | Code | Personality | IR family |
| --- | --- | --- | --- | --- |
| TV | — | `10178` | `tv-10178` | nec-like (not a player) |
| CBL-SAT | paramount | `21033` | `cblsat-21033` | SIRC-20 `1a:cmd:62` + shared `:49` |
| DVD | kanopy | `20533` | `dvd-20533` | SIRC-20 `1a:cmd:49` |
| VCR | youtubetv | `20033` | `vcr-20033` | SIRC-12 (+ `b4:5b` replay) |
| AUX | amazon | `20636` | `sony-dvr-20636` | SIRC-20 `1a:cmd:9a` |

## In progress — YouTube TV full HID pass

Amazon-mirrored VCR map is complete except **quick_skip** (silent on `20033`). Mouse d-pad + enter confirmed; transport/HID smoke OK under imperfect focus. Next: focused full test on tv.youtube.com; fill matrix rows from operator report.

Unbound (mirror amazon): stop, digits, quick_skip.

## Open

1. Full VCR→YouTube TV validation (checklist below); update matrix `actual`/`status`.
2. Hunt AUX/DVR library codes with **continuous** page/channel IR repeat (AUX `20636` only bursts a few times; Up/Down still useful on Prime). See post-mortem §5.1a.
3. CBL-SAT / DVD map rows later.

## Note — flash reload / USB stall

`make firmware`: **`OPERATOR_VERIFY=1` only**. Digest-gated eject+reset. Autoreload off. Map mode: **no CDC echo on presses** (ready banner only) — HID+serial flood wedged USB until unplug. D-pad mouse rate-limited. Auto: `OPERATOR_VERIFY=1 make firmware-watch`.

AUX page/channel share `1a:10`/`1a:11` → **Up/Down** + SEEK_KEYS ramp. **Caveat:** AUX `20636` only IR-repeats those buttons a few times while held; VCR `20033` repeats continuously — device profile, not firmware.

## Handoff — full test

```text
# Focus Chrome on a playing tv.youtube.com title, select VCR on the remote.
# One change / observe per button; report what the picture did.
```

| button | expect |
| --- | --- |
| play / pause | play_pause |
| ffw / frw (hold) | seek |
| record | fullscreen (F) |
| d-pad + enter | pointer + click |
| back | exit / dismiss |
| instant_replay | previous window (Shift+Alt+Tab) |
| channel | Up / Down arrows (hold accelerates) |
| page | Page Up / Down (SIRC-15 `b4:60`/`b4:62`; hold accelerates) |
| quick_skip | silent — skip |
