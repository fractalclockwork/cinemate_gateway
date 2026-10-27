# CircuitPython firmware (Pico)

Pins: **GP14** IR RX, **GP15** IR TX (held low in phase 1). Match [`hardware/boards/pico.yaml`](../../boards/pico.yaml).

`KEYMAP` lives in [`keymap_gen.py`](keymap_gen.py), generated from [`software/keymap.yaml`](../../../software/keymap.yaml):

```bash
make firmware-keymap
```

Decode path is Sony SIRC (12/15/20). Active map is AUX+`20636` SIRC-20 → keyboard / consumer / **mouse** HID for the **amazon** profile (`MODE = "map"` by default).

Vendored **`lib/adafruit_hid`** (Adafruit CircuitPython HID, MIT — see [`lib/adafruit_hid/VENDOR.md`](lib/adafruit_hid/VENDOR.md)) ships with this tree so a single deploy stays usable after unplug/replug.

## Deploy

1. Install CircuitPython for **Raspberry Pi Pico** (UF2) once — see [`environment/README.md`](../../../environment/README.md).
2. Copy the whole firmware tree (regenerates keymap first; includes `lib/`):

   ```bash
   OPERATOR_VERIFY=1 OPERATOR_FLASH=1 make firmware
   ```

   `present` must already have passed. Deploy **fails** if `lib/adafruit_hid` is missing after copy (not a warning).

3. Unplug/replug to confirm HID still enumerates without a manual library hunt.
4. `MODE = "capture"` in `code.py` logs pulses/frames over USB serial; `"map"` emits HID from `KEYMAP`.

Phase 1 must not aim the IR LED at the CineMate Interface module.
