# KiCad protoboard (schematic → wire-wrap PCB)

Process for the IR gateway hand-wired / wire-wrap board under this tree. Agents stand in this role only while editing `docs/kicad/ir-gateway/` (and linked board docs). Do **not** invent human verification; stop at each gate until the operator confirms.

**Design facts:** [`hardware-design.md`](hardware-design.md).  
**Tools:** [`_generate.py`](_generate.py) (schematic + initial PCB scaffold), [`_snap_route.py`](_snap_route.py) (2.54 mm snap + Manhattan jumpers).  
**crt-drive precedent:** orthogonal insulated jumpers as copper layers (`F.Cu` / `B.Cu` / `InN.Cu` named `JumperN`).

## Role boundaries

| Allowed | Forbidden |
| --- | --- |
| Generate/update schematic and PCB per the gates below | Skipping a human verification gate |
| Auto-validate nets (ERC, netlist membership, DRC connectivity) | Treating auto-validate as human approval |
| Snap to 2.54 mm and Manhattan-route after placement is verified | Re-placing parts after human placement OK without re-verification |
| Add jumper layers when paths cross | Same-layer crossings; diagonal tracks |
| Point the operator at files / reports | Setting `HUMAN_*` or typing YES for the operator |

Evidence / notes may land under `reports/` when useful; they do not replace the human gates.

---

## Gate flow (do not reorder)

```text
[1] Generate schematic
        ↓
[2] Auto-validate nets / connects     ← agent
        ↓
[3] Human verify schematic            ← STOP until operator OK
        ↓
[4] PCB component placement           ← agent draft / operator edit
        ↓
[5] Human verify rotation + position  ← STOP until operator OK
        ↓
[6] Snap to 2.54 mm grid              ← agent (_snap_route.py)
        ↓
[7] Wire power/ground (own layers)    ← agent, Manhattan
        ↓
[8] Wire signals (new layer on cross) ← agent, Manhattan
        ↓
[9] Auto DRC / connectivity check     ← agent; fix shorts; re-run
```

---

## 1. Generate schematic

1. Encode topology from [`hardware-design.md`](hardware-design.md) (Pico interface, CHQ1838 RX, NPN low-side IR LED).
2. Prefer regenerating via `_generate.py` so lib symbols stay consistent; preserve operator layout fixes by updating the generator to match.
3. Symbol libraries use **+Y up**; the schematic sheet uses **+Y down** — negate library pin Y when attaching wires (see `_generate.py` `pin_xy`).
4. Keep provisional R/C values labeled as working hypotheses until datasheets confirm them.

## 2. Auto-validate nets and connects (agent)

Run before asking for human schematic review:

```bash
kicad-cli sch erc --format report --severity-all \
  --output /tmp/ir-gateway-erc.rpt docs/kicad/ir-gateway/ir-gateway.kicad_sch
kicad-cli sch export netlist --format kicadxml \
  -o /tmp/ir-gateway-net.xml docs/kicad/ir-gateway/ir-gateway.kicad_sch
```

Check membership against the design net list:

| Net | Members |
| --- | --- |
| `+3V3` | J_PICO.1, U2.3 (VCC), C1, R2 |
| `GND` | J_PICO.2, U2.2 (GND), C1, Q1.E |
| `IR_RX` | J_PICO.3, U2.1 (OUT) |
| `IR_TX` | J_PICO.4, R1 → Q1.B |
| LED path | `+3V3`–R2–D1.A / D1.K–Q1.C–`GND` |

CHQ1838 pin order is **1=OUT, 2=GND, 3=VCC** (do not reuse TSOP17xx 1=GND/2=Vs/3=OUT).

Fix dangling wires, power/GND shorts through pin columns, and pin-not-connected errors. **ERC clean is necessary but not sufficient** — still require human verification.

## 3. Human verify schematic (gate)

Stop. Ask the operator to review the sheet in Eeschema (connectivity, polarity, pin map, values).

- Do **not** proceed to PCB placement until the operator explicitly confirms the schematic.
- After operator edits in Eeschema, re-run step 2, fold lasting layout into `_generate.py`, then seek confirmation again if the netlist changed.

## 4. PCB component placement

1. Place footprints for wire-wrap (THT). Operator may move/rotate freely in Pcbnew.
2. Keep Pico (`A1`) as the grid origin reference.
3. Do not snap or autoroute yet — rough placement for access and lead dress only.
4. `pcbnew` LoadBoard may segfault on this board; prefer sexpr / `_snap_route.py` over Python `pcbnew` automation.

## 5. Human verify rotation and position (gate)

Stop. Ask the operator to confirm:

- Part rotations (especially TO-92 E-B-C, LED anode/cathode, CHQ1838 pin 1 = OUT).
- Relative positions for wire-wrap reach and optical aiming (RX module / TX LED).

Do **not** run `_snap_route.py` until the operator confirms placement.

## 6. Snap to 2.54 mm grid

```bash
python3 docs/kicad/ir-gateway/_snap_route.py
```

- Grid origin = Pico `A1` pad 1.
- Snap footprint `(at x y)` to nearest 2.54 mm; snap rotation to 90° steps.
- Recompute pad world coords with KiCad’s PCB rotation sign (see `_snap_route.py` `rot_xy`).
- Dense courtyards on the TX cluster are expected; do not “fix” packing by spreading parts after human placement OK unless the operator asks.

## 7. Wire power and ground (own layers, Manhattan)

Inside `_snap_route.py` (or equivalent), after snap:

| Layer | Net | Rule |
| --- | --- | --- |
| `F.Cu` | `+3V3` | Dedicated; orthogonal H/V only |
| `B.Cu` | `GND` | Dedicated; orthogonal H/V only |

- Route with pad keep-out: tracks must not run through foreign THT pads (pads short all copper layers).
- Prefer full 2.54 mm alleys (no half-grid) so wire-wrap columns stay clear.
- Connect only the intended Pico pins for power (`36` = `+3V3`, `38` = `GND`), not every library-marked 3V3/GND pad.

## 8. Wire remaining signals (layer per need, Manhattan)

For `IR_RX`, `IR_TX`, `Q1_B`, `LED_A`, `LED_K`, …:

1. Spanning-tree (or equivalent) between pads on each net.
2. Manhattan paths with the same pad avoid rules.
3. Assign `InN.Cu` / `JumperN` by conflict coloring: if two jumpers cross or collinear-overlap, they **must** use different layers.
4. Add another `InN` / `JumperN` whenever the stack is exhausted — treat layer count as unlimited for prototyping.
5. Do not put signal tracks on the dedicated `+3V3` / `GND` layers.

## 9. Auto-validate PCB

```bash
kicad-cli pcb drc --format report --severity-error \
  --output /tmp/ir-gateway-drc.rpt docs/kicad/ir-gateway/ir-gateway.kicad_pcb
```

Require **0** shorting / unconnected-pad errors before calling the route done. Courtyard overlap on a dense wire-wrap cluster may be ignored per project severities; electrical shorts may not.

If the operator moves parts again after a route, return to gate **5**, then re-run **6–9**.

---

## Quick commands

```bash
# Schematic generate (also refreshes scaffold PCB — prefer _snap_route after placement)
python3 docs/kicad/ir-gateway/_generate.py

# After human schematic OK + human placement OK:
python3 docs/kicad/ir-gateway/_snap_route.py
```

## Files

| File | Role |
| --- | --- |
| `ir-gateway.kicad_sch` | Schematic (human-verified) |
| `ir-gateway.kicad_pcb` | Protoboard (snapped + jumpers) |
| `ir-gateway.kicad_pro` | Project / DRC severities |
| `sym-lib-table` | Local `ir-gateway` symbol lib |
| `symbols/ir-gateway.kicad_sym` | CHQ1838 (1=OUT 2=GND 3=VCC) |
| `_generate.py` | Schematic (+ optional PCB scaffold); `bom` mode swaps U2 |
| `_snap_route.py` | Snap 2.54 mm + Manhattan layer route |
| `hardware-design.md` | Decided / hypothesis / open facts |
