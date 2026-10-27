#!/usr/bin/env python3
"""Snap footprints to the Pico 2.54 mm hole grid and Manhattan wire-wrap route.

pcbnew LoadBoard segfaults on this board, so this is sexpr-only (crt-drive logic).

Layer policy (operator request):
  - +3V3  → F.Cu
  - GND   → B.Cu
  - other → InN.Cu (JumperN); a new layer is used whenever jumpers cross

Usage:  python3 docs/kicad/ir-gateway/_snap_route.py
"""

from __future__ import annotations

import math
import re
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
PCB = HERE / "ir-gateway.kicad_pcb"
G = 2.54
HIT = 1.35  # mm — > half Pico/ discretes pitch so alleys stay off neighboring pads

# F.Cu = +3V3, In1..In12 = signal jumpers, B.Cu = GND (crt-drive layer order).
LAYER_STACK = [("F.Cu", None)]
for i in range(1, 13):
    LAYER_STACK.append((f"In{i}.Cu", f"Jumper{i}"))
LAYER_STACK.append(("B.Cu", None))
POWER_LAYER = {"+3V3": 0, "GND": len(LAYER_STACK) - 1}

NET_CODES = {
    "": 0,
    "+3V3": 1,
    "GND": 2,
    "IR_RX": 3,
    "IR_TX": 4,
    "Q1_B": 5,
    "LED_K": 6,
    "LED_A": 7,
}


def uid() -> str:
    return str(uuid.uuid4())


def snap(v: float, origin: float) -> float:
    return origin + round((v - origin) / G) * G


def rot_xy(px: float, py: float, deg: float) -> tuple[float, float]:
    # KiCad PCB (at … rot) uses the opposite sign from the usual CCW matrix
    # when matching pad world coords reported by DRC / pcbnew.
    rad = math.radians(-deg)
    return (
        px * math.cos(rad) - py * math.sin(rad),
        px * math.sin(rad) + py * math.cos(rad),
    )


# Only these Pico pins participate in routing (module has many 3V3/GND pads).
A1_ROUTE_PINS = {"19": "IR_RX", "20": "IR_TX", "36": "+3V3", "38": "GND"}


def same_pt(a, b, tol=0.05):
    return abs(a[0] - b[0]) <= tol and abs(a[1] - b[1]) <= tol


def parse_footprints(text: str) -> list[dict]:
    fps = []
    parts = re.split(r"\n\t\(footprint ", text)
    for chunk in parts[1:]:
        body = "(footprint " + chunk
        depth = 0
        end = None
        for i, ch in enumerate(body):
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        fp = body[:end]
        name = re.search(r'\(footprint "([^"]+)"', fp).group(1)
        at = re.search(
            r"\n\t\t\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)", fp
        )
        ref = re.search(r'\(property "Reference" "([^"]+)"', fp).group(1)
        x, y = float(at.group(1)), float(at.group(2))
        rot = float(at.group(3) or 0)
        pads = {}
        for pm in re.finditer(
            r'\(pad "([^"]+)" \w+ \w+\s*\n\t\t\t\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)',
            fp,
        ):
            num = pm.group(1)
            px, py = float(pm.group(2)), float(pm.group(3))
            sub = fp[pm.end() : pm.end() + 500]
            nm = re.search(r'\(net (?:\d+ )?"([^"]+)"\)', sub)
            # Also match (net N "name")
            if not nm:
                nm = re.search(r'\(net \d+ "([^"]+)"\)', sub)
            net = nm.group(1) if nm else ""
            pads[num] = (px, py, net)
        fps.append(
            {"ref": ref, "name": name, "x": x, "y": y, "rot": rot, "pads": pads, "raw": fp}
        )
    return fps


def set_fp_at(fp_raw: str, x: float, y: float, rot: float) -> str:
    if abs(rot) < 1e-9:
        repl = f"(at {x:.2f} {y:.2f})"
    else:
        repl = f"(at {x:.2f} {y:.2f} {rot:g})"
    return re.sub(
        r"\n\t\t\(at [-\d.]+ [-\d.]+(?: [-\d.]+)?\)",
        "\n\t\t" + repl,
        fp_raw,
        count=1,
    )


def ensure_pad_nets(fp_raw: str, pads: dict) -> str:
    """Normalize pad nets to (net CODE "NAME") when a net is known."""
    out = fp_raw
    for num, (_px, _py, net) in pads.items():
        if not net or net not in NET_CODES:
            continue
        code = NET_CODES[net]
        # Replace existing (net ...) after this pad, or inject
        pattern = rf'(\(pad "{re.escape(num)}"[\s\S]*?)(\(net [^\n]+\))'
        if re.search(pattern, out):
            out = re.sub(
                pattern,
                rf'\1(net {code} "{net}")',
                out,
                count=1,
            )
        else:
            out = re.sub(
                rf'(\(pad "{re.escape(num)}"[\s\S]*?\(remove_unused_layers (?:yes|no)\))',
                rf'\1\n\t\t\t(net {code} "{net}")',
                out,
                count=1,
            )
    return out


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


def grid_vals(v0, v1, origin, extra=8):
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
    # Prefer full 2.54 mm alleys only (no half-grid) for wire-wrap hole columns.
    for sx in (-G, G, -2 * G, 2 * G, -3 * G, 3 * G, -4 * G, 4 * G):
        for sy in (-G, G, -2 * G, 2 * G, -3 * G, 3 * G):
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
    return [(p1, p2) for p1, p2 in zip(pts, pts[1:]) if not same_pt(p1, p2)]


def segs_cross(p1, p2, q1, q2):
    if any(same_pt(u, v) for u in (p1, p2) for v in (q1, q2)):
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

    if (
        abs(p1[1] - p2[1]) <= tol
        and abs(q1[1] - q2[1]) <= tol
        and abs(p1[1] - q1[1]) <= tol
    ):
        return iv(p1[0], p2[0], q1[0], q2[0])
    if (
        abs(p1[0] - p2[0]) <= tol
        and abs(q1[0] - q2[0]) <= tol
        and abs(p1[0] - q1[0]) <= tol
    ):
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


def spanning_edges(pads_on_net):
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


def rebuild_layers_block() -> str:
    # crt-drive order: F.Cu, In1..InN (JumperN), B.Cu — avoids ordinal confusion
    lines = ['\t\t(0 "F.Cu" signal)']
    for i in range(1, 13):
        lines.append(f'\t\t({2 * i + 2} "In{i}.Cu" signal "Jumper{i}")')
    lines.append('\t\t(2 "B.Cu" signal)')
    lines += [
        '\t\t(5 "F.SilkS" user "F.Silkscreen")',
        '\t\t(1 "F.Mask" user)',
        '\t\t(19 "Cmts.User" user "User.Comments")',
        '\t\t(25 "Edge.Cuts" user)',
        '\t\t(35 "F.Fab" user)',
    ]
    return "\t(layers\n" + "\n".join(lines) + "\n\t)"


def segment_sexpr(x1, y1, x2, y2, width, layer, net):
    return f"""\t(segment
\t\t(start {x1:.4f} {y1:.4f})
\t\t(end {x2:.4f} {y2:.4f})
\t\t(width {width})
\t\t(layer "{layer}")
\t\t(net {NET_CODES[net]})
\t\t(uuid "{uid()}")
\t)
"""


def main() -> None:
    text = PCB.read_text()
    fps = parse_footprints(text)
    pico = next(f for f in fps if f["ref"] == "A1")
    ox, oy = pico["x"], pico["y"]
    print(f"grid origin A1 ({ox}, {oy})")

    # Snap placements
    for f in fps:
        sx, sy = snap(f["x"], ox), snap(f["y"], oy)
        srot = round(f["rot"] / 90.0) * 90.0
        print(
            f"  {f['ref']:3} ({f['x']:7.2f},{f['y']:7.2f}) r={f['rot']:6.1f} "
            f"-> ({sx:.2f},{sy:.2f}) r={srot:g}"
        )
        f["x"], f["y"], f["rot"] = sx, sy, srot
        f["raw"] = set_fp_at(f["raw"], sx, sy, srot)
        f["raw"] = ensure_pad_nets(f["raw"], f["pads"])

    # Absolute pads (all THT are obstacles; named nets for connectivity)
    pad_list: list[tuple[float, float, str]] = []
    by_net: dict[str, list[tuple[float, float, str]]] = {}
    for f in fps:
        for num, (px, py, net) in f["pads"].items():
            rx, ry = rot_xy(px, py, f["rot"])
            ax, ay = f["x"] + rx, f["y"] + ry
            # Prefer canonical A1 net map
            if f["ref"] == "A1":
                net = A1_ROUTE_PINS.get(num, "")
            label = net or f"{f['ref']}.{num}"
            pad_list.append((ax, ay, label))
            if not net:
                continue
            by_net.setdefault(net, []).append((ax, ay, f"{f['ref']}.{num}"))
            print(f"    pad {f['ref']}.{num} ({ax:.2f},{ay:.2f}) {net}")

    # Route: MST per net, Manhattan, pad-avoiding
    jumpers: list[tuple[str, list]] = []
    for net, pads in sorted(by_net.items()):
        unique = []
        for p in pads:
            if any(same_pt(p[:2], q[:2]) for q in unique):
                continue
            unique.append(p)
        for a, b in spanning_edges(unique):
            path = manhattan_path(a[:2], b[:2], net, pad_list, ox, oy)
            jumpers.append((net, path))
            print(
                f"  {net:8} {a[2]:>6} -> {b[2]:<6}  "
                f"{[(round(p[0], 2), round(p[1], 2)) for p in path]}"
            )

    # Layer assignment: power fixed; signals colored; cross → new layer
    colors = [-1] * len(jumpers)
    power_idxs = set(POWER_LAYER.values())
    for i, (net, path) in enumerate(jumpers):
        if net in POWER_LAYER:
            colors[i] = POWER_LAYER[net]
            continue
        used = set()
        for j in range(i):
            if colors[j] in power_idxs:
                continue
            if paths_conflict(path, jumpers[j][1]):
                used.add(colors[j])
        c = 1  # first In layer (index 1)
        while c in used or c in power_idxs:
            c += 1
        if c >= len(LAYER_STACK):
            raise SystemExit(f"need more jumper layers (want index {c})")
        colors[i] = c

    used_layers = sorted(set(colors))
    print(
        "layers:",
        [
            f"{LAYER_STACK[c][1] or LAYER_STACK[c][0]}({c})"
            for c in used_layers
        ],
    )

    tracks = []
    for (net, path), color in zip(jumpers, colors):
        layer = LAYER_STACK[color][0]
        width = 0.6 if net in POWER_LAYER else 0.35
        for (x1, y1), (x2, y2) in polyline_segs(path):
            if abs(x1 - x2) > 1e-6 and abs(y1 - y2) > 1e-6:
                raise SystemExit(f"non-manhattan {net}")
            tracks.append(segment_sexpr(x1, y1, x2, y2, width, layer, net))

    # Rebuild board: header through nets, footprints, tracks, drawings
    # Strip old footprints, segments, and optional gr_* after nets
    # Keep from start through net list, then emit fps + tracks + outline

    # Find (net ...) block end — last net line before first footprint
    m_fp = re.search(r"\n\t\(footprint ", text)
    if not m_fp:
        raise SystemExit("no footprints")
    head = text[: m_fp.start()]

    # Ensure net list present
    if '(net 1 "+3V3")' not in head and '(net "+3V3")' not in head:
        net_block = "\n".join(
            f'\t(net {i} "{n}")' for n, i in sorted(NET_CODES.items(), key=lambda x: x[1])
        )
        head = head.rstrip() + "\n" + net_block + "\n"
    else:
        # Normalize to coded nets
        for name, code in NET_CODES.items():
            if not name:
                continue
            head = re.sub(
                rf'\(net (?:"{re.escape(name)}"|{code} "{re.escape(name)}")\)',
                f'(net {code} "{name}")',
                head,
            )

    # Replace layers block
    head = re.sub(
        r"\t\(layers\n[\s\S]*?\n\t\)",
        rebuild_layers_block(),
        head,
        count=1,
    )

    # Outline from pads
    xs = [p[0] for p in pad_list]
    ys = [p[1] for p in pad_list]
    margin = 2 * G
    x0 = snap(min(xs) - margin, ox)
    y0 = snap(min(ys) - margin, oy)
    x1 = snap(max(xs) + margin, ox)
    y1 = snap(max(ys) + margin, oy)
    outline = f"""\t(gr_rect
\t\t(start {x0:.2f} {y0:.2f})
\t\t(end {x1:.2f} {y1:.2f})
\t\t(stroke (width 0.15) (type default))
\t\t(fill none)
\t\t(layer "Edge.Cuts")
\t\t(uuid "{uid()}")
\t)
\t(gr_text "wire-wrap | +3V3=F.Cu GND=B.Cu | signals=JumperN (new layer on cross)"
\t\t(at {x0 + 2:.2f} {y1 - 2:.2f} 0)
\t\t(layer "Cmts.User")
\t\t(uuid "{uid()}")
\t\t(effects (font (size 1.2 1.2) (thickness 0.15)) (justify left))
\t)
"""

    # Indent footprints as board-level (already have leading tab from raw)
    fp_blocks = []
    for f in fps:
        raw = f["raw"]
        if not raw.startswith("\t"):
            raw = "\t" + raw
        fp_blocks.append(raw)

    out = (
        head.rstrip()
        + "\n"
        + "\n".join(fp_blocks)
        + "\n"
        + "".join(tracks)
        + outline
        + ")\n"
    )
    # head may already end before footprints; ensure single closing
    # If head included trailing content, trim after last net
    PCB.write_text(out)
    print("saved", PCB)

    # Update generator PLACEMENT hint for documentation
    place_lines = []
    for f in fps:
        gx = round((f["x"] - ox) / G)
        gy = round((f["y"] - oy) / G)
        place_lines.append(
            f"  {f['ref']}: grid=({gx},{gy}) mm=({f['x']:.2f},{f['y']:.2f}) rot={f['rot']:g}"
        )
    print("placement summary:")
    print("\n".join(place_lines))


if __name__ == "__main__":
    main()
