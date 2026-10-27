# Software (SIL)

Decode helpers, HID packing, and keymap validation. No USB.

- [`decode.py`](decode.py) — NEC-like synth/decode for fixtures (not Bose-confirmed)
- [`hid.py`](hid.py) — keyboard / consumer report packing
- [`profiles/`](profiles/) — AUX remote record and per-app HID encodings
- [`keymap.example.yaml`](keymap.example.yaml) — editable Chrome-oriented example
- [`fixture.py`](fixture.py) — `make sim` / image-stage evidence

```bash
make check
make sim
```
