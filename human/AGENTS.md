# Human-in-the-loop

Assent only. The operator validates and verifies the bench. Agents must **not** invent that verification, flash permission, or IR path confirmation. DUT presence is the `present` stage, not a flag.

## Allowed

- Read [`assent.py`](assent.py) and this file.
- Ask the operator to set `HUMAN_VERIFY`, `HUMAN_FLASH`, `HUMAN_IR_PATH`, or type `YES`.

## Forbidden

- Exporting `HUMAN_VERIFY=1`, `HUMAN_FLASH=1`, or `HUMAN_IR_PATH=1` without real operator verification.
- Starting a HWIL test before `HUMAN_VERIFY=1`.
- Typing `YES` on behalf of the operator.
- Importing hardware flash / IR TX modules from this tree.
