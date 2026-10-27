#!/usr/bin/env python3
"""Generate ir-gateway schematic + Manhattan wire-wrap PCB (sexpr; no pcbnew).

crt-drive style: orthogonal insulated jumpers as copper layers (F.Cu / B.Cu /
InN.Cu named JumperN). Crossings use different layers. THT pads short all
layers, so tracks never pass through foreign pads. Wire-wrap prototype —
add another jumper layer and re-route as needed.
"""

from __future__ import annotations

import re
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
SYM_DIR = Path("/usr/share/kicad/symbols")
LOCAL_SYM = HERE / "symbols"
FP_DIR = Path("/usr/share/kicad/footprints")
G = 2.54
PROJECT = "ir-gateway"
HIT = 0.85  # mm — foreign pad keep-out (matches crt-drive)

PIN_GPIO14 = "19"
PIN_GPIO15 = "20"
PIN_3V3 = "36"
PIN_GND = "38"

FOOTPRINTS = {
    "A1": ("Module", "RaspberryPi_Pico_Common_THT", "RaspberryPi_Pico"),
    "U2": ("OptoDevice", "Vishay_MINIMOLD-3Pin", "CHQ1838"),
    "Q1": ("Package_TO_SOT_THT", "TO-92_Inline", "2N3904"),
    "D1": ("LED_THT", "LED_D5.0mm", "IR_LED"),
    "R1": (
        "Resistor_THT",
        "R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal",
        "1k",
    ),
    "R2": (
        "Resistor_THT",
        "R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal",
        "100",
    ),
    "C1": ("Capacitor_THT", "C_Disc_D5.0mm_W2.5mm_P2.50mm", "100n"),
}

# Hole-grid placement relative to Pico pad 1 (matches operator wire-wrap layout
# after docs/kicad/ir-gateway/_snap_route.py). Rotations live on the PCB file.
PLACEMENT = {
    "A1": (0, 0),
    "C1": (10, 2),
    "R2": (10, 4),
    "D1": (13, 2),
    "R1": (14, 4),
    "Q1": (15, 1),
    "U2": (10, 18),
}

PAD_NETS = {
    "A1": {PIN_3V3: "+3V3", PIN_GND: "GND", PIN_GPIO14: "IR_RX", PIN_GPIO15: "IR_TX"},
    # CHQ1838: 1=OUT, 2=GND, 3=VCC (not TSOP17xx GND/Vs/OUT order)
    "U2": {"1": "IR_RX", "2": "GND", "3": "+3V3"},
    "C1": {"1": "+3V3", "2": "GND"},
    "R1": {"1": "IR_TX", "2": "Q1_B"},
    "Q1": {"1": "GND", "2": "Q1_B", "3": "LED_K"},
    "D1": {"1": "LED_K", "2": "LED_A"},
    "R2": {"1": "+3V3", "2": "LED_A"},
}

NETS = ["", "+3V3", "GND", "IR_RX", "IR_TX", "Q1_B", "LED_K", "LED_A"]

# Copper stack: F.Cu, In1..In12 as Jumper1..12, B.Cu — "infinite" for wire-wrap.
COPPER_LAYERS = [("F.Cu", None)]
for i in range(1, 13):
    COPPER_LAYERS.append((f"In{i}.Cu", f"Jumper{i}"))
COPPER_LAYERS.append(("B.Cu", None))


def uid() -> str:
    return str(uuid.uuid4())


def extract_symbol(lib_path: Path, name: str) -> str:
    """Return lib_symbols block renamed to Library:Name (KiCad instance key)."""
    text = lib_path.read_text()
    marker = f'(symbol "{name}"'
    start = text.find(marker)
    if start < 0:
        raise SystemExit(f"symbol {name} not in {lib_path}")
    rest = text[start:]
    depth = 0
    for i, ch in enumerate(rest):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                block = rest[: i + 1]
                lib = lib_path.stem  # e.g. Device.kicad_sym -> Device
                full = f"{lib}:{name}"
                block = block.replace(f'(symbol "{name}"', f'(symbol "{full}"', 1)
                # Alias symbols: (extends "Parent") → (extends "Lib:Parent")
                block = re.sub(
                    r'\(extends "([^:"]+)"\)',
                    rf'(extends "{lib}:\1")',
                    block,
                )
                return "\n".join(
                    ("\t\t" + line if line else line) for line in block.splitlines()
                )
    raise SystemExit(f"unbalanced symbol {name}")


def parse_pads(mod_text: str) -> dict[str, tuple[float, float]]:
    pads: dict[str, tuple[float, float]] = {}
    for m in re.finditer(
        r'\(pad "([^"]+)"[^\n]*\n(?:.*\n)*?\s*\(at ([-\d.]+) ([-\d.]+)',
        mod_text,
    ):
        pads[m.group(1)] = (float(m.group(2)), float(m.group(3)))
    return pads


def symbol_pin_offsets(lib_path: Path, name: str) -> dict[str, tuple[float, float, float]]:
    text = lib_path.read_text()
    start = text.find(f'(symbol "{name}"')
    if start < 0:
        raise SystemExit(f"missing symbol {name}")
    head = text[start : start + 400]
    if "(extends" in head:
        parent = re.search(r'\(extends "([^"]+)"', head).group(1)
        return symbol_pin_offsets(lib_path, parent)
    rest = text[start:]
    depth = 0
    block = rest
    for i, ch in enumerate(rest):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                block = rest[: i + 1]
                break
    pins: dict[str, tuple[float, float, float]] = {}
    for m in re.finditer(
        r'\(pin \w+ \w+\s*\n\s*\(at ([-\d.]+) ([-\d.]+) ([-\d.]+)\).*?\(number "([^"]+)"',
        block,
        re.S,
    ):
        pins[m.group(4)] = (float(m.group(1)), float(m.group(2)), float(m.group(3)))
    return pins


def write_project() -> None:
    (HERE / "ir-gateway.kicad_pro").write_text(
        """{
  "board": {
    "design_settings": {
      "defaults": { "copper_line_width": 0.25 },
      "net_settings": {
        "classes": [
          {
            "clearance": 0.0,
            "name": "Default",
            "track_width": 0.25,
            "via_diameter": 0.8,
            "via_drill": 0.4
          }
        ]
      },
      "rules": { "min_clearance": 0.0, "min_track_width": 0.2 }
    }
  },
  "meta": { "filename": "ir-gateway.kicad_pro", "version": 3 },
  "sheets": [["ir-gateway.kicad_sch", "Root"]],
  "text_variables": {}
}
"""
    )


def write_schematic() -> None:
    """Discrete IR front-end + Pico header.

    Layout matches the operator-corrected eeschema sheet: demod (C1/U2) left,
    J_PICO mid-right, vertical TX stack R2→D1(rot90)→Q1 with R1 into base.
    Symbol-lib +Y is up; schematic +Y is down — pin_xy() negates library Y.
    """
    import math

    sheet_uuid = uid()
    g = 2.54

    def r(v: float) -> float:
        return round(v, 2)

    libs = [
        (SYM_DIR / "Connector_Generic.kicad_sym", "Conn_01x04"),
        (LOCAL_SYM / "ir-gateway.kicad_sym", "CHQ1838"),
        (SYM_DIR / "Transistor_BJT.kicad_sym", "Q_NPN_EBC"),
        (SYM_DIR / "Device.kicad_sym", "LED"),
        (SYM_DIR / "Device.kicad_sym", "R"),
        (SYM_DIR / "Device.kicad_sym", "C"),
        (SYM_DIR / "power.kicad_sym", "+3V3"),
        (SYM_DIR / "power.kicad_sym", "GND"),
        (SYM_DIR / "power.kicad_sym", "PWR_FLAG"),
    ]
    embedded = "\n".join(extract_symbol(path, name) for path, name in libs)

    def sym(lib_id, ref, value, fp, x, y, pins, rot=0):
        x, y = r(x), r(y)
        pin_block = "\n".join(
            f'\t\t(pin "{p}"\n\t\t\t(uuid "{uid()}")\n\t\t)' for p in pins
        )
        return f"""\t(symbol
\t\t(lib_id "{lib_id}")
\t\t(at {x} {y} {rot})
\t\t(unit 1)
\t\t(exclude_from_sim no)
\t\t(in_bom yes)
\t\t(on_board yes)
\t\t(dnp no)
\t\t(uuid "{uid()}")
\t\t(property "Reference" "{ref}"
\t\t\t(at {r(x - 2 * g)} {r(y - 3 * g)} 0)
\t\t\t(effects (font (size 1.27 1.27)))
\t\t)
\t\t(property "Value" "{value}"
\t\t\t(at {r(x - 2 * g)} {r(y + 3 * g)} 0)
\t\t\t(effects (font (size 1.27 1.27)))
\t\t)
\t\t(property "Footprint" "{fp}"
\t\t\t(at {x} {y} 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
{pin_block}
\t\t(instances
\t\t\t(project "{PROJECT}"
\t\t\t\t(path "/{sheet_uuid}"
\t\t\t\t\t(reference "{ref}")
\t\t\t\t\t(unit 1)
\t\t\t\t)
\t\t\t)
\t\t)
\t)
"""

    def pwr(lib_id, ref, x, y):
        x, y = r(x), r(y)
        val = lib_id.split(":")[1]
        vy = r(y + 2 * g) if "GND" in lib_id else r(y - 1.5 * g)
        return f"""\t(symbol
\t\t(lib_id "{lib_id}")
\t\t(at {x} {y} 0)
\t\t(unit 1)
\t\t(exclude_from_sim no)
\t\t(in_bom yes)
\t\t(on_board yes)
\t\t(dnp no)
\t\t(uuid "{uid()}")
\t\t(property "Reference" "{ref}"
\t\t\t(at {x} {r(y - 2 * g)} 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
\t\t(property "Value" "{val}"
\t\t\t(at {x} {vy} 0)
\t\t\t(effects (font (size 1.27 1.27)))
\t\t)
\t\t(pin "1" (uuid "{uid()}"))
\t\t(instances
\t\t\t(project "{PROJECT}"
\t\t\t\t(path "/{sheet_uuid}"
\t\t\t\t\t(reference "{ref}")
\t\t\t\t\t(unit 1)
\t\t\t\t)
\t\t\t)
\t\t)
\t)
"""

    def wire(x1, y1, x2, y2):
        return f"""\t(wire
\t\t(pts (xy {r(x1)} {r(y1)}) (xy {r(x2)} {r(y2)}))
\t\t(stroke (width 0) (type default))
\t\t(uuid "{uid()}")
\t)
"""

    def junction(x, y):
        return f"""\t(junction
\t\t(at {r(x)} {r(y)})
\t\t(diameter 0)
\t\t(color 0 0 0 0)
\t\t(uuid "{uid()}")
\t)
"""

    parts: list[str] = []
    wires: list[str] = []
    junctions: list[str] = []

    def pin_xy(lib: Path, name: str, at: tuple[float, float], num: str, rot: float = 0):
        ox, oy, _ang = symbol_pin_offsets(lib, name)[num]
        rad = math.radians(rot)
        rx = ox * math.cos(rad) - oy * math.sin(rad)
        ry = ox * math.sin(rad) + oy * math.cos(rad)
        return r(at[0] + rx), r(at[1] - ry)

    # Operator-corrected placements (eeschema)
    j_at = (152.4, 85.09)
    u2_at = (90.17, 68.58)
    c1_at = (54.61, 68.58)
    r1_at = (143.51, 118.11)
    q1_at = (173.99, 128.27)
    d1_at = (176.53, 115.57)
    r2_at = (176.53, 106.68)
    d1_rot = 90

    parts.append(
        sym(
            "Connector_Generic:Conn_01x04",
            "J_PICO",
            "Pico 3V3/GND/GP14/GP15",
            "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
            *j_at,
            ["1", "2", "3", "4"],
        )
    )
    parts.append(
        sym(
            "ir-gateway:CHQ1838",
            "U2",
            "CHQ1838",
            "OptoDevice:Vishay_MINIMOLD-3Pin",
            *u2_at,
            ["1", "2", "3"],
        )
    )
    parts.append(
        sym(
            "Device:C",
            "C1",
            "100n",
            "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P2.50mm",
            *c1_at,
            ["1", "2"],
        )
    )
    parts.append(
        sym(
            "Device:R",
            "R1",
            "1k",
            "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal",
            *r1_at,
            ["1", "2"],
        )
    )
    parts.append(
        sym(
            "Transistor_BJT:Q_NPN_EBC",
            "Q1",
            "2N3904",
            "Package_TO_SOT_THT:TO-92_Inline",
            *q1_at,
            ["1", "2", "3"],
        )
    )
    parts.append(
        sym(
            "Device:LED",
            "D1",
            "IR_LED",
            "LED_THT:LED_D5.0mm",
            *d1_at,
            ["1", "2"],
            rot=d1_rot,
        )
    )
    parts.append(
        sym(
            "Device:R",
            "R2",
            "100",
            "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal",
            *r2_at,
            ["1", "2"],
        )
    )

    conn = SYM_DIR / "Connector_Generic.kicad_sym"
    chq = LOCAL_SYM / "ir-gateway.kicad_sym"
    device = SYM_DIR / "Device.kicad_sym"
    bjt = SYM_DIR / "Transistor_BJT.kicad_sym"

    j1 = pin_xy(conn, "Conn_01x04", j_at, "1")
    j2 = pin_xy(conn, "Conn_01x04", j_at, "2")
    j3 = pin_xy(conn, "Conn_01x04", j_at, "3")
    j4 = pin_xy(conn, "Conn_01x04", j_at, "4")
    u2_o = pin_xy(chq, "CHQ1838", u2_at, "1")  # OUT
    u2_g = pin_xy(chq, "CHQ1838", u2_at, "2")  # GND
    u2_v = pin_xy(chq, "CHQ1838", u2_at, "3")  # VCC
    c1_p = pin_xy(device, "C", c1_at, "1")
    c1_n = pin_xy(device, "C", c1_at, "2")
    r1_a = pin_xy(device, "R", r1_at, "1")
    r1_b = pin_xy(device, "R", r1_at, "2")
    q_e = pin_xy(bjt, "Q_NPN_EBC", q1_at, "1")
    q_b = pin_xy(bjt, "Q_NPN_EBC", q1_at, "2")
    q_c = pin_xy(bjt, "Q_NPN_EBC", q1_at, "3")
    d_k = pin_xy(device, "LED", d1_at, "1", rot=d1_rot)
    d_a = pin_xy(device, "LED", d1_at, "2", rot=d1_rot)
    r2_p = pin_xy(device, "R", r2_at, "1")
    r2_a = pin_xy(device, "R", r2_at, "2")

    # Power rails (left) + flags
    vbus_y, gbus_y = 50.8, 151.13
    parts.append(pwr("power:+3V3", "#PWR01", 26.67, vbus_y))
    parts.append(pwr("power:PWR_FLAG", "#FLG01", 31.75, vbus_y))
    parts.append(pwr("power:GND", "#PWR02", 26.67, gbus_y))
    parts.append(pwr("power:PWR_FLAG", "#FLG02", 31.75, gbus_y))
    wires += [
        wire(26.67, vbus_y, 31.75, vbus_y),
        wire(31.75, vbus_y, 132.08, vbus_y),
        wire(132.08, vbus_y, 176.53, vbus_y),
        wire(26.67, gbus_y, 31.75, gbus_y),
        wire(31.75, gbus_y, 132.08, gbus_y),
        wire(176.53, gbus_y, 132.08, gbus_y),
    ]
    junctions += [
        junction(31.75, vbus_y),
        junction(132.08, vbus_y),
        junction(57.15, vbus_y),
        junction(102.87, vbus_y),
        junction(31.75, gbus_y),
        junction(132.08, gbus_y),
        junction(52.07, gbus_y),
        junction(105.41, gbus_y),
    ]

    # +3V3 drops (side approach — never through C1/R2 pin axis)
    wires += [
        wire(57.15, vbus_y, 57.15, c1_p[1]),
        wire(57.15, c1_p[1], c1_p[0], c1_p[1]),
        wire(102.87, vbus_y, 102.87, u2_v[1]),
        wire(102.87, u2_v[1], u2_v[0], u2_v[1]),
        wire(132.08, vbus_y, 132.08, j1[1]),
        wire(132.08, j1[1], j1[0], j1[1]),
        wire(176.53, vbus_y, 176.53, r2_p[1]),
    ]
    # GND drops
    wires += [
        wire(52.07, gbus_y, 52.07, c1_n[1]),
        wire(52.07, c1_n[1], c1_n[0], c1_n[1]),
        wire(105.41, gbus_y, 105.41, u2_g[1]),
        wire(105.41, u2_g[1], u2_g[0], u2_g[1]),
        wire(132.08, gbus_y, 132.08, j2[1]),
        wire(132.08, j2[1], j2[0], j2[1]),
        wire(q_e[0], q_e[1], q_e[0], gbus_y),
    ]

    # IR_RX: U2.OUT ↔ J_PICO.3
    wires += [
        wire(u2_o[0], u2_o[1], 127, u2_o[1]),
        wire(127, u2_o[1], 127, j3[1]),
        wire(127, j3[1], j3[0], j3[1]),
    ]
    # IR_TX: J_PICO.4 ↔ R1.1
    wires += [
        wire(j4[0], j4[1], r1_a[0], j4[1]),
        wire(r1_a[0], j4[1], r1_a[0], r1_a[1]),
    ]
    # Q1_B: R1.2 ↔ Q1.B
    wires += [
        wire(r1_b[0], r1_b[1], r1_b[0], q_b[1]),
        wire(r1_b[0], q_b[1], q_b[0], q_b[1]),
    ]
    # LED stack on x=176.53: R2.2→D1.A, D1.K→Q1.C (no dangling stub)
    wires += [
        wire(r2_a[0], r2_a[1], d_a[0], d_a[1]),
        wire(d_k[0], d_k[1], q_c[0], q_c[1]),
    ]

    note = f"""\t(text "DEMOD"
\t\t(at 54.61 55.88 0)
\t\t(effects (font (size 1.4 1.4)) (justify left top))
\t\t(uuid "{uid()}")
\t)
\t(text "J_PICO: 1=+3V3 2=GND 3=IR_RX→GPIO14 4=IR_TX←GPIO15\\nPCB A1 = full Pico; InN.Cu = JumperN insulated wire-wrap (Manhattan)\\nR1=1k R2=100 C1=100n provisional — hardware-design.md"
\t\t(at 25.4 7.62 0)
\t\t(effects (font (size 1.4 1.4)) (justify left top))
\t\t(uuid "{uid()}")
\t)
"""

    sch = f"""(kicad_sch
\t(version 20250114)
\t(generator "ir-gateway-_generate")
\t(generator_version "10.0")
\t(uuid "{sheet_uuid}")
\t(paper "A3")
\t(title_block
\t\t(title "ir-remote-bose IR gateway")
\t\t(comment 1 "Manhattan / wire-wrap protoboard")
\t\t(comment 2 "Provisional R/C — hardware-design.md")
\t)
\t(lib_symbols
{embedded}
\t)
{''.join(parts)}
{''.join(junctions)}
{''.join(wires)}
{note}
\t(sheet_instances
\t\t(path "/" (page "1"))
\t)
\t(embedded_fonts no)
)
"""
    (HERE / "ir-gateway.kicad_sch").write_text(sch)


# ----- PCB routing (crt-drive Manhattan + layer coloring) -----


def same_pt(a, b, tol=0.05):
    return abs(a[0] - b[0]) <= tol and abs(a[1] - b[1]) <= tol


def seg_hits_pad(a, b, pads, net, ends):
    ax, ay = a
    bx, by = b
    for px, py, pnet in pads:
        if pnet == net:
            continue
        if any(same_pt((px, py), e, HIT) for e in ends):
            continue
        if abs(ay - by) < 1e-6:
            if abs(py - ay) > HIT:
                continue
            lo, hi = (ax, bx) if ax <= bx else (bx, ax)
            if lo - HIT <= px <= hi + HIT:
                return True
        elif abs(ax - bx) < 1e-6:
            if abs(px - ax) > HIT:
                continue
            lo, hi = (ay, by) if ay <= by else (by, ay)
            if lo - HIT <= py <= hi + HIT:
                return True
    return False


def path_blocked(pts, net, pads):
    ends = [pts[0], pts[-1]]
    for p1, p2 in zip(pts, pts[1:]):
        if same_pt(p1, p2):
            continue
        if seg_hits_pad(p1, p2, pads, net, ends):
            return True
    return False


def grid_vals(v0, v1, origin, extra=6):
    lo, hi = (v0, v1) if v0 <= v1 else (v1, v0)
    start = origin + round((lo - origin) / G) * G - extra * G
    stop = origin + round((hi - origin) / G) * G + extra * G
    vals = []
    v = start
    while v <= stop + 1e-9:
        vals.append(round(v, 4))
        v += G
    return vals


def manhattan_path(a, b, net, pads, ox, oy):
    ax, ay = a
    bx, by = b
    candidates: list[list[tuple[float, float]]] = []
    if abs(ax - bx) < 1e-6 or abs(ay - by) < 1e-6:
        candidates.append([a, b])
    candidates.append([a, (bx, ay), b])
    candidates.append([a, (ax, by), b])
    for x in grid_vals(ax, bx, ox):
        if abs(x - ax) < 0.4 or abs(x - bx) < 0.4:
            continue
        candidates.append([a, (x, ay), (x, by), b])
    for y in grid_vals(ay, by, oy):
        if abs(y - ay) < 0.4 or abs(y - by) < 0.4:
            continue
        candidates.append([a, (ax, y), (bx, y), b])
    half = G / 2
    for x in (ax + half, ax - half, bx + half, bx - half):
        candidates.append([a, (x, ay), (x, by), b])
    for y in (ay + half, ay - half, by + half, by - half):
        candidates.append([a, (ax, y), (bx, y), b])
    for sx in (-G, G, -2 * G, 2 * G):
        for sy in (-G, G, -2 * G, 2 * G):
            candidates.append(
                [a, (ax + sx, ay), (ax + sx, by + sy), (bx, by + sy), b]
            )
            candidates.append(
                [a, (ax, ay + sy), (bx + sx, ay + sy), (bx + sx, by), b]
            )

    def score(pts):
        length = 0.0
        segs = 0
        for p1, p2 in zip(pts, pts[1:]):
            if same_pt(p1, p2):
                continue
            segs += 1
            length += abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])
        return (segs, length)

    clear = [p for p in candidates if not path_blocked(p, net, pads)]
    if clear:
        clear.sort(key=score)
        return clear[0]
    candidates.sort(key=score)
    print(f"  warn: no clear path for {net} {a} -> {b}")
    return candidates[0]


def polyline_segs(pts):
    return [
        (p1, p2)
        for p1, p2 in zip(pts, pts[1:])
        if not same_pt(p1, p2)
    ]


def segs_cross(p1, p2, q1, q2):
    if any(
        same_pt(u, v)
        for u in (p1, p2)
        for v in (q1, q2)
    ):
        return False

    def side(a, b, c):
        v = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
        return 1 if v > 0 else (-1 if v < 0 else 0)

    s1, s2 = side(p1, p2, q1), side(p1, p2, q2)
    s3, s4 = side(q1, q2, p1), side(q1, q2, p2)
    if 0 in (s1, s2, s3, s4):
        return False
    return s1 != s2 and s3 != s4


def collinear_overlap(p1, p2, q1, q2, tol=0.2):
    def iv(a0, a1, b0, b1):
        lo_a, hi_a = (a0, a1) if a0 <= a1 else (a1, a0)
        lo_b, hi_b = (b0, b1) if b0 <= b1 else (b1, b0)
        return lo_a < hi_b - tol and lo_b < hi_a - tol

    if abs(p1[1] - p2[1]) <= tol and abs(q1[1] - q2[1]) <= tol and abs(p1[1] - q1[1]) <= tol:
        return iv(p1[0], p2[0], q1[0], q2[0])
    if abs(p1[0] - p2[0]) <= tol and abs(q1[0] - q2[0]) <= tol and abs(p1[0] - q1[0]) <= tol:
        return iv(p1[1], p2[1], q1[1], q2[1])
    return False


def paths_conflict(pa, pb):
    for a, b in polyline_segs(pa):
        for c, d in polyline_segs(pb):
            if segs_cross(a, b, c, d) or collinear_overlap(a, b, c, d):
                return True
            if any(same_pt(u, v) for u in (a, b) for v in (c, d)):
                return True
    return False


def color_paths(paths):
    colors = [-1] * len(paths)
    for i, path in enumerate(paths):
        used = set()
        for j in range(i):
            if colors[j] >= 0 and paths_conflict(path, paths[j]):
                used.add(colors[j])
        c = 0
        while c in used:
            c += 1
        if c >= len(COPPER_LAYERS):
            raise SystemExit(f"need more jumper layers (want {c + 1})")
        colors[i] = c
    return colors


def spanning_edges(pads_on_net):
    """MST edges preferring already-aligned pairs (crt-drive)."""
    n = len(pads_on_net)
    if n < 2:
        return []
    edges = []
    for i in range(n):
        for j in range(i + 1, n):
            a, b = pads_on_net[i][:2], pads_on_net[j][:2]
            w = abs(a[0] - b[0]) + abs(a[1] - b[1])
            if abs(a[0] - b[0]) < 0.2 or abs(a[1] - b[1]) < 0.2:
                w *= 0.01
            edges.append((w, i, j))
    edges.sort()
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    out = []
    for _w, i, j in edges:
        a, b = find(i), find(j)
        if a == b:
            continue
        parent[a] = b
        out.append((pads_on_net[i], pads_on_net[j]))
        if len(out) == n - 1:
            break
    return out


def write_pcb() -> None:
    net_codes = {n: i for i, n in enumerate(NETS)}
    origin_x, origin_y = 50.8, 40.64

    abs_pads: dict[str, dict[str, tuple[float, float]]] = {}
    fp_blocks: list[str] = []
    pad_list: list[tuple[float, float, str]] = []  # x,y,net

    for ref, (gx, gy) in PLACEMENT.items():
        lib, name, value = FOOTPRINTS[ref]
        at_x = origin_x + gx * G
        at_y = origin_y + gy * G
        mod_path = FP_DIR / f"{lib}.pretty" / f"{name}.kicad_mod"
        mod = mod_path.read_text()
        pads = parse_pads(mod)
        abs_pads[ref] = {n: (at_x + px, at_y + py) for n, (px, py) in pads.items()}

        # Embed full library footprint; inject nets + board instance fields.
        body = mod.strip()
        body = re.sub(
            r'^\(footprint "[^"]*"',
            f'(footprint "{lib}:{name}"',
            body,
            count=1,
        )
        # Drop library-only header fields that confuse board instances
        body = re.sub(r'\n\t\(version [^\n]+\)', '', body, count=1)
        body = re.sub(r'\n\t\(generator [^\n]+\)', '', body, count=1)
        body = re.sub(r'\n\t\(generator_version [^\n]+\)', '', body, count=1)

        # Insert board placement after layer line
        fp_uuid = uid()
        if re.search(r'\n\t\(layer "F\.Cu"\)', body):
            body = re.sub(
                r'\n\t\(layer "F\.Cu"\)',
                f'\n\t(layer "F.Cu")\n\t(uuid "{fp_uuid}")\n\t(at {at_x} {at_y})',
                body,
                count=1,
            )
        else:
            body = body.replace(
                f'(footprint "{lib}:{name}"',
                f'(footprint "{lib}:{name}"\n\t(layer "F.Cu")\n\t(uuid "{fp_uuid}")\n\t(at {at_x} {at_y})',
                1,
            )

        # Inject net after each pad's (layers ...) / (remove_unused_layers ...)
        for num, pnet in PAD_NETS.get(ref, {}).items():
            code = net_codes[pnet]
            pattern = (
                rf'(\(pad "{re.escape(num)}"[\s\S]*?'
                rf'\(remove_unused_layers (?:yes|no)\))'
            )
            repl = rf'\1\n\t\t(net {code} "{pnet}")'
            body, nsub = re.subn(pattern, repl, body, count=1)
            if nsub != 1:
                # Fallback: after (layers ...) line
                pattern2 = rf'(\(pad "{re.escape(num)}"[\s\S]*?\(layers "[^"]*" "[^"]*"\))'
                body, nsub = re.subn(
                    pattern2, rf'\1\n\t\t(net {code} "{pnet}")', body, count=1
                )
            if nsub != 1:
                print(f"  warn: net inject failed for {ref}.{num}")

        if ref == "Q1":
            # Keep annular ≥0.1 mm (drill 0.5 → size ≥0.7); stay small vs 1.27 mm pitch.
            body = re.sub(
                r'(\(pad "[123]" thru_hole \w+\s*\n\t\t\(at [-\d.]+ [-\d.]+\)\s*\n\t\t)\(size [-\d.]+ [-\d.]+\)',
                r'\1(size 1.0 1.0)',
                body,
            )
            body = re.sub(
                r'(\(pad "[123]" thru_hole \w+\s*\n\t\t\(at [-\d.]+ [-\d.]+\)\s*\n\t\t\(size 1\.0 1\.0\)\s*\n\t\t)\(drill [-\d.]+\)',
                r'\1(drill 0.5)',
                body,
            )

        body = re.sub(
            r'\(property "Reference" "[^"]*"',
            f'(property "Reference" "{ref}"',
            body,
            count=1,
        )
        body = re.sub(
            r'\(property "Value" "[^"]*"',
            f'(property "Value" "{value}"',
            body,
            count=1,
        )

        indented = "\n".join(
            ("\t" + line if line else line) for line in body.splitlines()
        )
        fp_blocks.append(indented + "\n")

        for num, (px, py) in pads.items():
            pnet = PAD_NETS.get(ref, {}).get(num, "")
            pad_list.append((at_x + px, at_y + py, pnet or f"{ref}.{num}"))

    by_net: dict[str, list[tuple[float, float, str]]] = {}
    for ref, mapping in PAD_NETS.items():
        for num, net in mapping.items():
            # Prefer single GND attach on Pico (pin 38), like crt-drive.
            if ref == "A1" and net == "GND" and num != PIN_GND:
                continue
            x, y = abs_pads[ref][num]
            by_net.setdefault(net, []).append((x, y, f"{ref}.{num}"))

    jumpers = []
    for net, pads in sorted(by_net.items()):
        # Dedupe coincident
        unique = []
        for p in pads:
            if any(same_pt(p[:2], q[:2]) for q in unique):
                continue
            unique.append(p)
        for a, b in spanning_edges(unique):
            path = manhattan_path(a[:2], b[:2], net, pad_list, origin_x, origin_y)
            jumpers.append((net, path))
            print(f"  {net:8} {a[2]:>6} -> {b[2]:<6}  {[(round(p[0],2), round(p[1],2)) for p in path]}")

    paths = [p for _n, p in jumpers]
    colors = color_paths(paths)
    print("jumper layers used", sorted(set(colors)))

    tracks = []
    for (net, path), color in zip(jumpers, colors):
        layer_name = COPPER_LAYERS[color][0]
        width = 0.6 if net in ("+3V3", "GND") else 0.35
        for (x1, y1), (x2, y2) in polyline_segs(path):
            if abs(x1 - x2) > 1e-6 and abs(y1 - y2) > 1e-6:
                raise SystemExit(f"non-manhattan {net}: {(x1,y1)} -> {(x2,y2)}")
            tracks.append(
                f"""\t(segment
\t\t(start {x1:.4f} {y1:.4f})
\t\t(end {x2:.4f} {y2:.4f})
\t\t(width {width})
\t\t(layer "{layer_name}")
\t\t(net {net_codes[net]})
\t\t(uuid "{uid()}")
\t)
"""
            )

    layer_lines = []
    # Match crt-drive ordinals for F/In/B; extra In layers for headroom.
    ordinals = {
        "F.Cu": 0,
        "In1.Cu": 4,
        "In2.Cu": 6,
        "In3.Cu": 8,
        "In4.Cu": 10,
        "In5.Cu": 12,
        "In6.Cu": 14,
        "In7.Cu": 16,
        "In8.Cu": 18,
        "In9.Cu": 20,
        "In10.Cu": 22,
        "In11.Cu": 24,
        "In12.Cu": 26,
        "B.Cu": 2,
    }
    for name, uname in COPPER_LAYERS:
        ord_ = ordinals[name]
        if uname:
            layer_lines.append(f'\t\t({ord_} "{name}" signal "{uname}")')
        else:
            layer_lines.append(f'\t\t({ord_} "{name}" signal)')
    layer_lines += [
        '\t\t(5 "F.SilkS" user "F.Silkscreen")',
        '\t\t(1 "F.Mask" user)',
        '\t\t(19 "Cmts.User" user "User.Comments")',
        '\t\t(25 "Edge.Cuts" user)',
        '\t\t(35 "F.Fab" user)',
    ]
    net_lines = [f'\t(net {i} "{n}")' for i, n in enumerate(NETS)]

    xs = [p[0] for p in pad_list]
    ys = [p[1] for p in pad_list]
    margin = 2 * G
    x0 = origin_x + round((min(xs) - margin - origin_x) / G) * G
    y0 = origin_y + round((min(ys) - margin - origin_y) / G) * G
    x1 = origin_x + round((max(xs) + margin - origin_x) / G) * G
    y1 = origin_y + round((max(ys) + margin - origin_y) / G) * G

    outline = f"""\t(gr_rect
\t\t(start {x0:.2f} {y0:.2f})
\t\t(end {x1:.2f} {y1:.2f})
\t\t(stroke (width 0.15) (type default))
\t\t(fill none)
\t\t(layer "Edge.Cuts")
\t\t(uuid "{uid()}")
\t)
\t(gr_text "ir-gateway wire-wrap | Manhattan H/V | InN.Cu=JumperN (re-route freely)"
\t\t(at {x0 + 2:.2f} {y1 - 2:.2f} 0)
\t\t(layer "Cmts.User")
\t\t(uuid "{uid()}")
\t\t(effects (font (size 1.2 1.2) (thickness 0.15)) (justify left))
\t)
"""

    pcb = f"""(kicad_pcb
\t(version 20241229)
\t(generator "ir-gateway-_generate")
\t(generator_version "10.0")
\t(general
\t\t(thickness 1.6)
\t\t(legacy_teardrops no)
\t)
\t(paper "A4")
\t(title_block
\t\t(title "ir-remote-bose IR gateway")
\t\t(comment 1 "Wire-wrap / Manhattan protoboard")
\t)
\t(layers
{chr(10).join(layer_lines)}
\t)
\t(setup
\t\t(pad_to_mask_clearance 0)
\t\t(allow_soldermask_bridges_in_footprints no)
\t\t(stackup
\t\t\t(layer "F.Cu" (type copper))
\t\t\t(layer "dielectric 1" (type dielectric) (thickness 0.1) (material FR4) (epsilon_r 4.5) (loss_tangent 0.02))
\t\t\t(layer "In1.Cu" (type copper))
\t\t\t(layer "dielectric 2" (type dielectric) (thickness 0.1) (material FR4) (epsilon_r 4.5) (loss_tangent 0.02))
\t\t\t(layer "In2.Cu" (type copper))
\t\t\t(layer "dielectric 3" (type dielectric) (thickness 0.1) (material FR4) (epsilon_r 4.5) (loss_tangent 0.02))
\t\t\t(layer "In3.Cu" (type copper))
\t\t\t(layer "dielectric 4" (type dielectric) (thickness 0.1) (material FR4) (epsilon_r 4.5) (loss_tangent 0.02))
\t\t\t(layer "In4.Cu" (type copper))
\t\t\t(layer "dielectric 5" (type dielectric) (thickness 0.1) (material FR4) (epsilon_r 4.5) (loss_tangent 0.02))
\t\t\t(layer "In5.Cu" (type copper))
\t\t\t(layer "dielectric 6" (type dielectric) (thickness 0.1) (material FR4) (epsilon_r 4.5) (loss_tangent 0.02))
\t\t\t(layer "In6.Cu" (type copper))
\t\t\t(layer "dielectric 7" (type dielectric) (thickness 0.1) (material FR4) (epsilon_r 4.5) (loss_tangent 0.02))
\t\t\t(layer "In7.Cu" (type copper))
\t\t\t(layer "dielectric 8" (type dielectric) (thickness 0.1) (material FR4) (epsilon_r 4.5) (loss_tangent 0.02))
\t\t\t(layer "In8.Cu" (type copper))
\t\t\t(layer "dielectric 9" (type dielectric) (thickness 0.1) (material FR4) (epsilon_r 4.5) (loss_tangent 0.02))
\t\t\t(layer "In9.Cu" (type copper))
\t\t\t(layer "dielectric 10" (type dielectric) (thickness 0.1) (material FR4) (epsilon_r 4.5) (loss_tangent 0.02))
\t\t\t(layer "In10.Cu" (type copper))
\t\t\t(layer "dielectric 11" (type dielectric) (thickness 0.1) (material FR4) (epsilon_r 4.5) (loss_tangent 0.02))
\t\t\t(layer "In11.Cu" (type copper))
\t\t\t(layer "dielectric 12" (type dielectric) (thickness 0.1) (material FR4) (epsilon_r 4.5) (loss_tangent 0.02))
\t\t\t(layer "In12.Cu" (type copper))
\t\t\t(layer "dielectric 13" (type dielectric) (thickness 0.1) (material FR4) (epsilon_r 4.5) (loss_tangent 0.02))
\t\t\t(layer "B.Cu" (type copper))
\t\t\t(copper_finish "None")
\t\t\t(dielectric_constraints no)
\t\t)
\t\t(pcbplotparams
\t\t\t(layerselection 0x00010fc_ffffffff)
\t\t\t(plot_on_all_layers_selection 0x0000000_00000000)
\t\t\t(disableapertmacros no)
\t\t\t(usegerberextensions no)
\t\t\t(usegerberattributes yes)
\t\t\t(usegerberadvancedattributes yes)
\t\t\t(creategerberjobfile yes)
\t\t\t(dashed_line_dash_ratio 12.000000)
\t\t\t(dashed_line_gap_ratio 3.000000)
\t\t\t(svgprecision 4)
\t\t\t(plotframeref no)
\t\t\t(mode 1)
\t\t\t(useauxorigin no)
\t\t\t(hpglpennumber 1)
\t\t\t(hpglpenspeed 20)
\t\t\t(hpglpendiameter 15.000000)
\t\t\t(pdf_front_fp_property_popup yes)
\t\t\t(pdf_back_fp_property_popup yes)
\t\t\t(dxfpolygonmode yes)
\t\t\t(dxfimperialunits yes)
\t\t\t(dxfusepcbnewfont yes)
\t\t\t(psnegative no)
\t\t\t(psa4output no)
\t\t\t(plotreference yes)
\t\t\t(plotvalue yes)
\t\t\t(plotfptext yes)
\t\t\t(plotinvisibletext no)
\t\t\t(sketchpadsonfab no)
\t\t\t(subtractmaskfromsilk no)
\t\t\t(outputformat 1)
\t\t\t(mirror no)
\t\t\t(drillshape 1)
\t\t\t(scaleselection 1)
\t\t\t(outputdirectory "")
\t\t)
\t)
{chr(10).join(net_lines)}
{''.join(fp_blocks)}
{''.join(tracks)}
{outline}
)
"""
    (HERE / "ir-gateway.kicad_pcb").write_text(pcb)


def update_board_docs() -> None:
    yaml_path = HERE.parents[2] / "hardware" / "boards" / "pico.yaml"
    text = yaml_path.read_text()
    text = re.sub(r"ir_rx:.*", "ir_rx: 14", text)
    text = re.sub(r"ir_tx:.*", "ir_tx: 15", text)
    yaml_path.write_text(text)

    md = HERE.parents[2] / "hardware" / "docs" / "boards" / "pico.md"
    body = md.read_text()
    if "Decided GPIO" not in body:
        body += """

## Decided GPIO (protoboard)

| Signal | Pico | Notes |
| --- | --- | --- |
| `IR_RX` | GPIO14 (pin 19) | CHQ1838 OUT |
| `IR_TX` | GPIO15 (pin 20) | NPN base via 1 kΩ |

KiCad protoboard: [`docs/kicad/ir-gateway/`](../../../docs/kicad/ir-gateway/).
"""
        md.write_text(body)
    else:
        body = body.replace("TSOP17xx OUT", "CHQ1838 OUT")
        md.write_text(body)


def _u2_minimold_block(at_x: float, at_y: float, at_rot: str | None = None) -> str:
    """Board-level U2 footprint (CHQ1838 / MINIMOLD) with pad nets."""
    at_line = f"(at {at_x} {at_y}" + (f" {at_rot}" if at_rot else "") + ")"
    mod = (FP_DIR / "OptoDevice.pretty" / "Vishay_MINIMOLD-3Pin.kicad_mod").read_text()
    body = mod.strip()
    body = re.sub(
        r'^\(footprint "[^"]*"',
        '(footprint "OptoDevice:Vishay_MINIMOLD-3Pin"',
        body,
        count=1,
    )
    body = re.sub(r"\n\t\(version [^\n]+\)", "", body, count=1)
    body = re.sub(r"\n\t\(generator [^\n]+\)", "", body, count=1)
    body = re.sub(r"\n\t\(generator_version [^\n]+\)", "", body, count=1)
    fp_uuid = uid()
    if re.search(r'\n\t\(layer "F\.Cu"\)', body):
        body = re.sub(
            r'\n\t\(layer "F\.Cu"\)',
            f'\n\t(layer "F.Cu")\n\t(uuid "{fp_uuid}")\n\t{at_line}',
            body,
            count=1,
        )
    else:
        body = body.replace(
            '(footprint "OptoDevice:Vishay_MINIMOLD-3Pin"',
            f'(footprint "OptoDevice:Vishay_MINIMOLD-3Pin"\n\t(layer "F.Cu")\n\t(uuid "{fp_uuid}")\n\t{at_line}',
            1,
        )

    net_map = {"1": (3, "IR_RX"), "2": (2, "GND"), "3": (1, "+3V3")}
    for num, (code, name) in net_map.items():
        pattern = (
            rf'(\(pad "{re.escape(num)}"[\s\S]*?'
            rf'\(remove_unused_layers (?:yes|no)\))'
        )
        repl = rf'\1\n\t\t(net {code} "{name}")'
        body, nsub = re.subn(pattern, repl, body, count=1)
        if nsub != 1:
            print(f"  warn: net inject failed for U2.{num}")

    body = re.sub(
        r'\(property "Reference" "[^"]*"',
        '(property "Reference" "U2"',
        body,
        count=1,
    )
    body = re.sub(
        r'\(property "Value" "[^"]*"',
        '(property "Value" "CHQ1838"',
        body,
        count=1,
    )
    return "\n".join(("\t" + line if line else line) for line in body.splitlines())


def replace_u2_footprint_preserve_at() -> None:
    """Swap CAST→MINIMOLD on the live PCB without moving other parts.

    Preserves U2 (at x y [rot]) when present; if missing (e.g. prior bad
    replace), restores at the last known human placement (76.2, 86.36).
    Pad pitch differs (CAST pad3 @7.62 vs MINIMOLD @5.08) — re-run
    _snap_route.py afterward.
    """
    pcb_path = HERE / "ir-gateway.kicad_pcb"
    text = pcb_path.read_text()
    # Span from the board-level tab through the matching close paren.
    m = re.search(
        r'\n\t\(footprint "OptoDevice:Vishay_(?:CAST|MINIMOLD)-3Pin"',
        text,
    )
    at_x, at_y, at_rot = 76.2, 86.36, None
    if m:
        start = m.start() + 1  # at '\t(footprint'
        # Confirm this is U2 (or any lone IR rx fp)
        depth = 0
        end = None
        for i in range(start, len(text)):
            if text[i] == "(":
                depth += 1
            elif text[i] == ")":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        assert end is not None
        old = text[start:end]
        if '(property "Reference" "U2"' not in old:
            # Wrong IR footprint instance — fall through to insert
            m = None
        else:
            at_m = re.search(r"\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)", old)
            if not at_m:
                raise SystemExit("U2 (at ...) missing")
            at_x, at_y = float(at_m.group(1)), float(at_m.group(2))
            at_rot = at_m.group(3)
            block = _u2_minimold_block(at_x, at_y, at_rot)
            pcb_path.write_text(text[:start] + block + text[end:])
            print(f"replaced U2 footprint at (at {at_x} {at_y}) → MINIMOLD/CHQ1838")
            return

    # Insert before first (segment or after last footprint
    block = _u2_minimold_block(at_x, at_y, at_rot)
    ins = re.search(r"\n\t\(segment\b", text)
    if not ins:
        ins = re.search(r"\n\t\(gr_rect\b", text)
    if not ins:
        raise SystemExit("cannot find insertion point for U2")
    pcb_path.write_text(text[: ins.start()] + "\n" + block + text[ins.start() :])
    print(f"inserted U2 footprint at (at {at_x} {at_y}) → MINIMOLD/CHQ1838")


def main() -> None:
    import sys

    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    if mode in ("all", "sch", "bom"):
        write_project()
        write_schematic()
        update_board_docs()
        print(f"wrote {HERE / 'ir-gateway.kicad_pro'}")
        print(f"wrote {HERE / 'ir-gateway.kicad_sch'}")
    if mode in ("all", "pcb"):
        write_pcb()
        print(f"wrote {HERE / 'ir-gateway.kicad_pcb'}")
    if mode == "bom":
        # Keep human placement; swap RX footprint + nets only.
        replace_u2_footprint_preserve_at()


if __name__ == "__main__":
    main()
