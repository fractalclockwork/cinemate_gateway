# CircuitPython firmware (Pico)

Pins: **GP14** IR RX, **GP15** IR TX (held low in phase 1). Match [`hardware/boards/pico.yaml`](../../boards/pico.yaml).

`KEYMAP` lives in [`keymap_gen.py`](keymap_gen.py), generated from [`software/keymap.yaml`](../../../software/keymap.yaml):

```bash
make firmware-keymap
```

Decode path is Sony SIRC (12/15/20). Default `MODE = "map"`: union `KEYMAP` covers AUX+`20636` (amazon, SIRC-20) and VCR+`20033` (youtubetv, SIRC-12). Keep `boot.py` `CAPTURE_BUILD` in sync with `MODE`.

Vendored **`lib/adafruit_hid`** (Adafruit CircuitPython HID, MIT — see [`lib/adafruit_hid/VENDOR.md`](lib/adafruit_hid/VENDOR.md)) ships with this tree so a single deploy stays usable after unplug/replug.

## Deploy

1. Install CircuitPython for **Raspberry Pi Pico** (UF2) once — see [`environment/README.md`](../../../environment/README.md).
2. Copy the whole firmware tree (regenerates keymap first; includes `lib/`):

   ```bash
   OPERATOR_VERIFY=1 make firmware
   # or auto on save:
   OPERATOR_VERIFY=1 make firmware-watch
   ```

   `present` must already have passed. **No `OPERATOR_FLASH`** for CIRCUITPY app deploys (that flag is UF2-only). Deploy **fails** if `lib/adafruit_hid` is missing after copy.

3. Hands-free and **digest-gated**: stamp → copy → clean `.Trash`/`.fseventsd` → eject → MCU reset → serial `digest=<sha>` must match. `boot.py` sets `supervisor.runtime.autoreload = False` so remounts do not stop the IR loop. Close **tio** first (`killall tio`).
4. Modes (keep `boot.py` `CAPTURE_BUILD` in sync with `code.py` `MODE`):
   - **`"map"` (default)** — IR → HID from `KEYMAP`.
   - **`"capture"`** — device-code bring-up: set `MODE = "capture"` and `CAPTURE_BUILD = True`, redeploy; serial prints `frame_key` only (no HID). Note which Bose source is selected.
   - Host `make capture` can still arm `/CAPTURE_ONLY` for Raw REPL pulse catalogs.

Phase 1 must not aim the IR LED at the CineMate Interface module.
