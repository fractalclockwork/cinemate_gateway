# CircuitPython firmware (Pico)

Pins: **GP14** IR RX, **GP15** IR TX (held low in phase 1). Match [`hardware/boards/pico.yaml`](../../boards/pico.yaml).

`KEYMAP` lives in [`keymap_gen.py`](keymap_gen.py), generated from [`software/keymap.yaml`](../../../software/keymap.yaml):

```bash
make firmware-keymap
```

Decode path is Sony SIRC (12/15/20). Active map is AUX+`20636` SIRC-20 → keyboard HID for the kanopy profile.

## Deploy

1. Install CircuitPython for **Raspberry Pi Pico** (UF2).
2. Install **`adafruit_hid`** on `CIRCUITPY/lib` (Adafruit CircuitPython Library Bundle — copy the `adafruit_hid` folder into `lib/`). Without it, `code.py` fails on import.
3. Copy firmware (regenerates keymap first):

   ```bash
   HUMAN_VERIFY=1 HUMAN_FLASH=1 make firmware
   ```

   `present` must already have passed. That command uses the stored presence record.

4. `MODE = "capture"` in `code.py` logs pulses/frames over USB serial; `"map"` emits HID from `KEYMAP`.

Phase 1 must not aim the IR LED at the CineMate Interface module.
