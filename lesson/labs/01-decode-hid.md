# Decode → HID

After `make hwil` passes:

1. Run `make lesson` to confirm the SIL fixture still maps example IR keys to HID reports.
2. Program AUX with `10178`; code-check AUX ([`docs/manual-facts.md`](../../docs/manual-facts.md)). Short+double flash is accept on this unit.
3. Capture On-Off first (`HUMAN_VERIFY=1 make capture BUTTON=on_off FRESH=1`); agreeing a/b samples accept and advance through the remaining buttons.
4. Render `software/keymap.yaml` with `--profile` only from accepted buttons. Leave `software/keymap.example.yaml` synthetic.
