# Software (SIL)

Decode helpers, HID packing, profiles, and keymap validation. No USB.

- [`decode.py`](decode.py) — NEC-like / Sony SIRC / pd24 helpers for fixtures and capture classification
- [`hid.py`](hid.py) — keyboard / consumer report packing
- [`profiles/`](profiles/) — AUX remote record and per-app HID encodings
- [`keymap.yaml`](keymap.yaml) — active measured AUX+`20636` → HID map (kanopy)
- [`keymap.example.yaml`](keymap.example.yaml) — synthetic nec-like map for SIL fixtures only
- [`export_firmware_keymap.py`](export_firmware_keymap.py) — writes [`../hardware/firmware/pico/keymap_gen.py`](../hardware/firmware/pico/keymap_gen.py) (`make firmware-keymap`)
- [`fixture.py`](fixture.py) — `make sim` / SIL `image` stage evidence (`sil-hid-fixture`)

```bash
make check
make sim
make firmware-keymap
```
