# Operator

Confirmation only. The operator validates the bench and is the end user of the gateway. Agents must **not** invent that verification, flash permission, or IR path confirmation. DUT presence is the `present` stage, not a flag.

## Allowed

- Read [`assent.py`](assent.py) and this file.
- Ask the operator to set `OPERATOR_VERIFY`, `OPERATOR_FLASH`, `OPERATOR_IR_PATH`, or type `YES`.

## Forbidden

- Exporting `OPERATOR_VERIFY=1`, `OPERATOR_FLASH=1`, or `OPERATOR_IR_PATH=1` without real operator verification.
- Starting a HWIL test before `OPERATOR_VERIFY=1`.
- Typing `YES` on behalf of the operator.
- Importing hardware flash / IR TX modules from this tree.
