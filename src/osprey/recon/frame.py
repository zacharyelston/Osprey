"""An interlocking ladder frame for a flying wing: what car builders call a
buck, the skeleton a plug or a skin is formed over. CNC-cut from flat sheet,
it slots together without fasteners into a rigid egg-crate.

The frame is two kinds of flat part:
- ribs: sections across the span, in planes of constant y;
- stringers: one line per entry of stringer_chord_fractions on each wing
  half, following that fraction of the chord out to the tip. Each is straight
  in plan between break ribs, in a vertical plane, so it follows the sweep
  and still cuts flat. A straight wing needs no breaks; a curved one (the
  crescent) breaks where a straight run would leave the planform, every
  stringer at the same ribs, so they never cross.

Where a rib and a stringer cross, each gets a slot half the local depth, the
rib from below and the stringer from above. A stringer crosses the ribs at
an angle, so both slots widen by 1/sin(angle). A stringer's ends butt
against the faces of the root rib, the break ribs and the tip rib.

The parts' top edges trace the wing's surface, set skin_offset_mm inside the
outer mould line: plank or fill the frame, fair it to the frame's edges, and
the surface comes out at the designed shape. The whole frame stands on a
flat table (a strongback): every part's bottom edge is the base line,
base_mm below the surface's lowest point.

Two frames: one for the upper surface, and one for the lower surface turned
over (z mirrored), each standing on its own table.

`export` nests both frames' parts on sheets and writes, in millimetres:
- frame_sheet<N>.dxf: one per sheet, R12, layer CUT (closed polylines, the
  part outlines with their slots), LABEL (part names, to engrave or ignore)
  and SHEET (the stock outline, not cut);
- frame_sheet<N>.svg: the same, to look at;
- frame_sheets.png: the nested sheets;
- frame.md: the cut list and how it goes together.

`osprey recon-frame` also renders frame.png: both frames assembled on their
tables (render.frame).

Body frame: x forward, y port, z up.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from osprey.recon import geometry

MM = 1000.0


@dataclass
class FramePart:
    name: str
    kind: str                 # "rib" or "stringer"
    side: str                 # the frame it belongs to: "upper" or "lower"
    outline: np.ndarray       # (N, 2) closed polygon in the part's plane, mm: (a along the part, z)
    origin: tuple             # plan position (x, y) of a = 0, mm
    direction: tuple          # plan unit vector along which a runs
    slots: list = field(default_factory=list)   # (a, depth) of each slot, mm

    @property
    def size(self) -> tuple[float, float]:
        return tuple(np.ptp(self.outline, axis=0))

    def to_3d(self, pts: np.ndarray, offset: float = 0.0) -> np.ndarray:
        """Points (a, z) of the part's plane in the body frame (mm), offset across the sheet."""
        ox, oy = self.origin
        ux, uy = self.direction
        a, z = pts[:, 0], pts[:, 1]
        return np.c_[ox + a * ux - offset * uy, oy + a * uy + offset * ux, z]


class Wing:
    """The sized wing's surface, queryable at any span station."""

    def __init__(self, p, d: dict, side: str = "upper", n_span: int = 61):
        g = p.geometry
        y, le, c, tw, tc, lz = geometry._stations(p, d, n_span)
        self.half = float(y[-1])
        self.st = (y, le, c, tw, tc, lz)
        self.foil = (g.airfoil_camber, g.airfoil_camber_pos)
        self.side = side

    def curve(self, y_m: float, n: int = 80) -> tuple[np.ndarray, np.ndarray]:
        """The surface at span station y (m): x and z (m), ordered aft to forward."""
        y, le, c, tw, tc, lz = self.st
        a = abs(y_m)
        le_, c_, tw_, tc_, lz_ = (float(np.interp(a, y, arr)) for arr in (le, c, tw, tc, lz))
        u, z = geometry.naca4(*self.foil, tc_, n)
        pts = geometry._section(u, z, le_, c_, y_m, tw_, lz_)
        k = len(u) // 2
        part = pts[: k + 1] if self.side == "upper" else pts[k:][::-1]
        xs, zs = part[:, 0], part[:, 2]
        if self.side == "lower":
            zs = -zs                                  # turned over: the lower surface faces up
        order = np.argsort(xs)
        return xs[order], zs[order]

    def chord_x(self, y_m: float) -> tuple[float, float]:
        xs, _ = self.curve(y_m, 40)
        return float(xs.min()), float(xs.max())

    def z_at(self, x_m: float, y_m: float) -> float:
        xs, zs = self.curve(y_m)
        return float(np.interp(x_m, xs, zs))


def _notched_top(samples, notches, wd, zb):
    """A part's top edge, run from its far end back to a = 0, with a slot cut
    down from it at each notch: samples are (a, z), notches (a, half depth, z
    of the top there)."""
    events = [(a, 0, z) for a, z in samples if all(abs(a - an) > wd / 2 for an, *_ in notches)]
    events += [(an, 1, (hd, zt)) for an, hd, zt in notches]
    out = []
    for a, kind, v in sorted(events, key=lambda e: -e[0]):
        if kind == 0:
            out.append((a, v))
        else:
            hd, zt = v
            out += [(a + wd / 2, zt), (a + wd / 2, zb + hd), (a - wd / 2, zb + hd), (a - wd / 2, zt)]
    return out


def build(p, d: dict, side: str = "upper") -> tuple[list[FramePart], dict]:
    """The ribs and stringers of one frame, slots cut, in millimetres."""
    fr = p.frame
    w = Wing(p, d, side)
    t = (fr.thickness_mm + fr.clearance_mm) / MM
    off = fr.skin_offset_mm / MM
    margin = fr.edge_margin_mm / MM
    tip = w.half - 0.02
    ribs_y = np.arange(0.0, tip, fr.rib_spacing_mm / MM)
    ribs_y = np.unique(np.r_[-ribs_y[::-1], ribs_y, [-tip, tip]])
    span_y = np.linspace(-tip, tip, 200)
    zmin = min(float(w.curve(yy)[1].min()) for yy in span_y) - off
    zb = zmin - fr.base_mm / MM                       # the base line, below everything

    def chord_point(f, yy):
        a, b = w.chord_x(yy)                          # trailing edge x, leading edge x
        return b - f * (b - a)

    def covered(x, yy, m_=margin):
        a, b = w.chord_x(yy)
        return a + m_ <= x <= b - m_

    def fits(f, ya, yb, ribs_between):
        """Whether a straight run from fraction f of the chord at ya to the same
        fraction at yb works: inside the planform all along, and at each rib
        it crosses, far enough in from the rib's ends to take a slot."""
        xa, xb = chord_point(f, ya), chord_point(f, yb)
        x = lambda yy: xa + (xb - xa) * (yy - ya) / (yb - ya)       # noqa: E731
        wd = t * math.hypot(xb - xa, yb - ya) / abs(yb - ya)
        return (all(covered(x(yy), yy, 0.0) for yy in np.linspace(ya, yb, 40))
                and all(covered(x(yy), yy, wd / 2 + margin) for yy in ribs_between))

    def runs(out, sgn):
        """The break ribs: the fewest straight runs from root to tip that fit,
        each over at least three rib gaps (two ribs to slot into) if it can,
        else two, else one."""
        n = len(out)
        for min_gap in (3, 2, 1):
            ok = {(k, m): all(fits(f, out[k] + sgn * t / 2, out[m] - sgn * t / 2, out[k + 1:m]) for f in fracs)
                  for k in range(n) for m in range(k + min(min_gap, n - 1 - k), n) if m > k}
            best = {0: (0, [0])}
            for m in range(1, n):
                cands = [(best[k][0] + 1, best[k][1] + [m]) for k in range(m) if k in best and ok.get((k, m))]
                if cands:
                    best[m] = min(cands, key=lambda c: (c[0], -min(np.diff(c[1]))))
            if n - 1 in best:
                return best[n - 1][1]
        return list(range(n))

    fracs = sorted(fr.stringer_chord_fractions)
    stringers = []                                    # (name, side sign, (x, y) at one end, (x, y) at the other)
    for sgn in (1, -1):
        out = [yy for yy in ribs_y if yy * sgn >= 0][:: sgn]    # this half's ribs, root to tip
        breaks = runs(out, sgn)
        for f in fracs:
            for n_, (k0, k1) in enumerate(zip(breaks[:-1], breaks[1:])):
                ya, yb = out[k0] + sgn * t / 2, out[k1] - sgn * t / 2
                name = f"S{'P' if sgn > 0 else 'S'}{f * 100:02.0f}" + (f"-{n_ + 1}" if len(breaks) > 2 else "")
                stringers.append((name, sgn, (chord_point(f, ya), ya), (chord_point(f, yb), yb)))

    def unit(stg):
        (xa, ya), (xb, yb) = stg[2], stg[3]
        v = np.array([xb - xa, yb - ya])
        return v / np.linalg.norm(v)

    def root(stg):
        return np.array(stg[2])

    def at(stg, yy):
        """Where a stringer crosses span station yy: x, and the distance a along it from its inboard end."""
        (xa, ya), (xb, yb) = stg[2], stg[3]
        x = xa + (xb - xa) * (yy - ya) / (yb - ya)
        return x, float(np.linalg.norm(np.array([x, yy]) - root(stg)))

    joints = []                                       # (rib index, stringer index, half depth)
    for j, stg in enumerate(stringers):
        ya, yb = stg[2][1], stg[3][1]
        wd = t / abs(unit(stg)[1])
        L = at(stg, yb)[1]
        for i, yy in enumerate(ribs_y):
            if not min(ya, yb) < yy < max(ya, yb):
                continue                              # not between its ends: it butts the end ribs
            x, a = at(stg, yy)
            if a < wd or a > L - wd or not covered(x, yy, wd / 2 + margin):
                continue                              # too near an end of either part to hold a slot
            joints.append((i, j, (w.z_at(x, yy) - off - zb) / 2))

    def top_z(x, yy):
        return w.z_at(x, yy) - off

    parts: list[FramePart] = []
    for i, yy in enumerate(ribs_y):
        xs, zs = w.curve(yy)
        notches = sorted((at(stringers[j], yy)[0], hd, top_z(at(stringers[j], yy)[0], yy), t / abs(unit(stringers[j])[1]))
                         for ii, j, hd in joints if ii == i)
        base = [(xs[0], zb)]
        for x, hd, _, wd in notches:
            base += [(x - wd / 2, zb), (x - wd / 2, zb + hd), (x + wd / 2, zb + hd), (x + wd / 2, zb)]
        base.append((xs[-1], zb))
        outline = np.r_[np.array(base), np.c_[xs, zs - off][::-1]] * MM
        name = f"R{'P' if yy > 0 else 'S' if yy < 0 else 'C'}{abs(yy) * MM:04.0f}"
        parts.append(FramePart(name, "rib", side, outline, (0.0, yy * MM), (1.0, 0.0),
                               [(x * MM, hd * MM) for x, hd, *_ in notches]))
    for j, stg in enumerate(stringers):
        name = stg[0]
        u = unit(stg)
        wd = t / abs(u[1])
        L = at(stg, stg[3][1])[1]
        r0 = root(stg)
        samples = [(a, top_z(*(r0 + a * u))) for a in np.linspace(0.0, L, max(int(L / 0.008), 4))]
        notches = sorted((at(stg, ribs_y[i])[1], hd, top_z(at(stg, ribs_y[i])[0], ribs_y[i]))
                         for i, jj, hd in joints if jj == j)
        top = _notched_top(samples, notches, wd, zb)
        outline = np.r_[[(0.0, zb), (L, zb)], np.array(top)] * MM
        parts.append(FramePart(name, "stringer", side, outline, tuple(r0 * MM), tuple(u),
                               [(a * MM, (top_z(*(r0 + a * u)) - zb - hd) * MM) for a, hd, _ in notches]))
    info = {"side": side, "ribs": int(len(ribs_y)), "stringers": len(stringers), "joints": len(joints),
            "base_z_mm": zb * MM, "thickness_mm": fr.thickness_mm, "slot_mm": t * MM,
            "max_height_mm": float(max(pt.outline[:, 1].max() for pt in parts) - zb * MM)}
    return parts, info


def triangulate(poly: np.ndarray) -> np.ndarray:
    """Ear-clip a simple polygon (N, 2) into triangles (M, 3) of its vertex
    indices, wound like the polygon. Collinear vertices are dropped."""
    n = len(poly)
    area = 0.5 * float(np.sum(poly[:, 0] * np.roll(poly[:, 1], -1) - np.roll(poly[:, 0], -1) * poly[:, 1]))
    s = 1.0 if area > 0 else -1.0
    idx = list(range(n))
    tris = []

    def cross(o, a, b):
        return s * ((a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]))

    eps = 1e-9 * max(float(np.ptp(poly)), 1.0) ** 2
    guard = 0
    while len(idx) > 3 and guard < 10 * n * n:
        guard += 1
        m = len(idx)
        clipped = False
        for k in range(m):
            i0, i1, i2 = idx[k - 1], idx[k], idx[(k + 1) % m]
            a, b, c = poly[i0], poly[i1], poly[i2]
            cr = cross(a, b, c)
            if abs(cr) <= eps:
                idx.pop(k)                            # collinear: no triangle, just drop it
                clipped = True
                break
            if cr < 0:
                continue                              # reflex
            inside = False
            for q in idx:
                if q in (i0, i1, i2):
                    continue
                pq = poly[q]
                if cross(a, b, pq) >= -eps and cross(b, c, pq) >= -eps and cross(c, a, pq) >= -eps:
                    inside = True
                    break
            if not inside:
                tris.append((i0, i1, i2))
                idx.pop(k)
                clipped = True
                break
        if not clipped:
            break
    if len(idx) == 3 and abs(cross(*poly[idx])) > eps:
        tris.append(tuple(idx))
    return np.array(tris, int).reshape(-1, 3)


def solid(part: FramePart, thickness_mm: float) -> tuple[np.ndarray, np.ndarray]:
    """The part as a closed mesh in the body frame, metres, faces wound outward."""
    poly = part.outline
    area = 0.5 * float(np.sum(poly[:, 0] * np.roll(poly[:, 1], -1) - np.roll(poly[:, 0], -1) * poly[:, 1]))
    if area < 0:
        poly = poly[::-1]
    n = len(poly)
    h = thickness_mm / 2
    v = np.r_[part.to_3d(poly, -h), part.to_3d(poly, h)] / MM
    tri = triangulate(poly)
    # A counter-clockwise outline in (a, z) faces -across, so the -h cap keeps
    # its winding and the +h cap flips; the sides face out of the outline.
    side = []
    for i in range(n):
        j = (i + 1) % n
        side += [(i, n + j, j), (i, n + i, n + j)]
    f = np.concatenate([tri, tri[:, ::-1] + n, np.array(side)])
    return v, f


def nest(parts: list[FramePart], sheet_mm, gap_mm: float) -> list[list[tuple[FramePart, float, float, bool]]]:
    """Shelf-pack the parts' bounding boxes onto sheets: (part, x, y, turned
    90 degrees) for each placement, a list per sheet. Tallest parts first;
    a part longer than the sheet turns to run across it."""
    W, H = sheet_mm
    boxes = []
    for q in parts:
        w, h = q.size
        turn = w > W - 2 * gap_mm
        boxes.append((q, *((h, w) if turn else (w, h)), turn))
    for q, w, h, _ in boxes:
        if w > W - 2 * gap_mm or h > H - 2 * gap_mm:
            raise ValueError(f"{q.name} ({w:.0f} x {h:.0f} mm) does not fit a {W:.0f} x {H:.0f} mm sheet")
    boxes.sort(key=lambda b: (-b[2], -b[1]))
    sheets, cur = [], []
    x = y = gap_mm
    row_h = 0.0
    for q, w, h, turn in boxes:
        if x + w > W - gap_mm:
            x, y, row_h = gap_mm, y + row_h + gap_mm, 0.0
        if y + h > H - gap_mm:
            sheets.append(cur)
            cur, x, y, row_h = [], gap_mm, gap_mm, 0.0
        cur.append((q, x, y, turn))
        x += w + gap_mm
        row_h = max(row_h, h)
    if cur:
        sheets.append(cur)
    return sheets


def placed(q: FramePart, x: float, y: float, turn: bool) -> np.ndarray:
    """A part's outline where it sits on the sheet."""
    pts = q.outline - q.outline.min(0)
    if turn:
        pts = np.c_[pts[:, 1], q.size[0] - pts[:, 0]]
    return pts + [x, y]


def label(q: FramePart) -> str:
    return f"{q.side[0].upper()}-{q.name}"


def _label_at(q: FramePart, pts: np.ndarray) -> tuple[float, float, float]:
    """Where a part's name goes: text height and lower-left corner, inside the part above its base."""
    lo, hi = pts.min(0), pts.max(0)
    h = float(min(8.0, max(3.0, (hi[1] - lo[1]) / 5)))
    return h, float(lo[0] + (hi[0] - lo[0]) * 0.3), float(lo[1] + 0.25 * (hi[1] - lo[1]))


def write_dxf(path: Path, sheet, sheet_mm):
    """One sheet as an R12 DXF in millimetres: layers CUT, LABEL, SHEET."""
    W, H = sheet_mm
    out = ["0", "SECTION", "2", "HEADER", "9", "$ACADVER", "1", "AC1009", "9", "$INSUNITS", "70", "4",
           "0", "ENDSEC", "0", "SECTION", "2", "TABLES", "0", "TABLE", "2", "LAYER", "70", "3"]
    for name, colour in (("CUT", 7), ("LABEL", 1), ("SHEET", 8)):
        out += ["0", "LAYER", "2", name, "70", "0", "62", str(colour), "6", "CONTINUOUS"]
    out += ["0", "ENDTAB", "0", "ENDSEC", "0", "SECTION", "2", "ENTITIES"]

    def poly(pts, layer):
        out.extend(["0", "POLYLINE", "8", layer, "66", "1", "10", "0.0", "20", "0.0", "30", "0.0", "70", "1"])
        for px, py in pts:
            out.extend(["0", "VERTEX", "8", layer, "10", f"{px:.3f}", "20", f"{py:.3f}", "30", "0.0"])
        out.extend(["0", "SEQEND", "8", layer])

    poly([(0, 0), (W, 0), (W, H), (0, H)], "SHEET")
    for q, x, y, turn in sheet:
        pts = placed(q, x, y, turn)
        poly(pts, "CUT")
        h, tx, ty = _label_at(q, pts)
        out += ["0", "TEXT", "8", "LABEL", "10", f"{tx:.3f}", "20", f"{ty:.3f}", "30", "0.0", "40", f"{h:.2f}",
                "1", label(q)]
    out += ["0", "ENDSEC", "0", "EOF"]
    path.write_text("\n".join(out) + "\n")


def write_svg(path: Path, sheet, sheet_mm):
    W, H = sheet_mm
    body = [f'<rect x="0" y="0" width="{W:g}" height="{H:g}" fill="#e9dcc4" stroke="#888" stroke-width="2"/>']
    for q, x, y, turn in sheet:
        pts = placed(q, x, y, turn)
        d = " ".join(f"{px:.2f},{H - py:.2f}" for px, py in pts)
        fill = "#c79a63" if q.kind == "rib" else "#a7784a"
        body.append(f'<polygon points="{d}" fill="{fill}" stroke="#222" stroke-width="0.8"/>')
        h, tx, ty = _label_at(q, pts)
        body.append(f'<text x="{tx:.1f}" y="{H - ty:.1f}" font-size="{h:.1f}" font-family="monospace" '
                    f'fill="#b00">{label(q)}</text>')
    path.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:g}mm" height="{H:g}mm" '
                    f'viewBox="0 0 {W:g} {H:g}">\n' + "\n".join(body) + "\n</svg>\n")


def export(p, d: dict, out: Path) -> dict:
    """Both frames' parts, nested on sheets: DXF and SVG per sheet, and the cut list."""
    fr = p.frame
    out.mkdir(parents=True, exist_ok=True)
    for old in list(out.glob("frame_sheet*.dxf")) + list(out.glob("frame_sheet*.svg")):
        old.unlink()
    frames, infos = {}, {}
    for side in ("upper", "lower"):
        frames[side], infos[side] = build(p, d, side)
    parts = frames["upper"] + frames["lower"]
    sheets = nest(parts, fr.sheet_mm, fr.part_gap_mm)
    where = {}
    for k, sheet in enumerate(sheets, 1):
        write_dxf(out / f"frame_sheet{k}.dxf", sheet, fr.sheet_mm)
        write_svg(out / f"frame_sheet{k}.svg", sheet, fr.sheet_mm)
    sheets_png(out / "frame_sheets.png", sheets, fr.sheet_mm, f"{p.mission.name}, {d.get('airframe', '')} ladder frame: ")
    for k, sheet in enumerate(sheets, 1):
        for q, *_ in sheet:
            where[id(q)] = k
    used = sum(abs(0.5 * float(np.sum(q.outline[:, 0] * np.roll(q.outline[:, 1], -1)
                                      - np.roll(q.outline[:, 0], -1) * q.outline[:, 1]))) for q in parts) / 1e6
    W, H = fr.sheet_mm
    u, lo = infos["upper"], infos["lower"]
    foot = {k: np.ptp(np.concatenate([q.to_3d(q.outline)[:, :2] for q in v]), axis=0) for k, v in frames.items()}
    lines = [f"# Ladder frame: {p.mission.name}, {d.get('airframe', '')}", "",
             "An interlocking egg-crate of flat parts, CNC-cut from sheet, that stands on a flat table. Its top edges "
             f"trace the wing's surface {fr.skin_offset_mm:g} mm inside the outer mould line: plank or fill it, fair "
             "to the frame, and the surface comes out at the designed shape. Two frames: the upper surface, and the "
             "lower surface turned over. Millimetres; x forward, y port, z up.", "",
             "| | Upper frame | Lower frame |", "|---|---|---|",
             f"| Ribs / stringers / joints | {u['ribs']} / {u['stringers']} / {u['joints']} | "
             f"{lo['ribs']} / {lo['stringers']} / {lo['joints']} |",
             f"| Height off the table | {u['max_height_mm']:.0f} | {lo['max_height_mm']:.0f} |",
             f"| Footprint on the table (x by y) | {foot['upper'][0]:.0f} x {foot['upper'][1]:.0f} | "
             f"{foot['lower'][0]:.0f} x {foot['lower'][1]:.0f} |", "",
             f"Stock: {len(sheets)} sheet{'s' if len(sheets) > 1 else ''} of {W:.0f} x {H:.0f} x {fr.thickness_mm:g} mm "
             f"(MDF or birch ply); the parts use {used:.2f} m² of {len(sheets) * W * H / 1e6:.2f} m². Slots are "
             f"{fr.thickness_mm:g} mm + {fr.clearance_mm:g} mm clearance, widened by 1/sin of the crossing angle "
             "where a stringer runs swept.", "",
             "Files: `frame_sheet<N>.dxf` (R12, layer CUT: closed outlines with slots; LABEL: part names to engrave "
             "or ignore; SHEET: the stock, not cut) and `frame_sheet<N>.svg` to look at. Cut with a "
             f"{fr.thickness_mm:g} mm or smaller end mill; dog-bone the slot corners if the bit is round.", "",
             "Assembly:",
             "- Ribs (`R`): `RC0000` is the root; `RP`/`RS` are port and starboard, named by their distance out in "
             "mm. Their slots open downward.",
             "- Stringers (`S`): `SP`/`SS` port and starboard, named by the fraction of the chord they follow, and "
             "`-1`, `-2`... for the straight runs from root to tip. Their slots open upward. Their ends butt the faces "
             "of the root rib, the tip ribs and the break ribs (the ribs with no slots); glue or screw them there.",
             "- Drop each stringer onto the ribs from above. Every part's bottom edge is the base line: screw or "
             "hot-glue them all to the table.",
             "- Prefixes `U-` and `L-` on the sheets say which frame a part belongs to.", "",
             "| Part | Frame | Kind | Length x height | Slots | Sheet |", "|---|---|---|---|---|---|"]
    for q in parts:
        w_, h_ = q.size
        lines.append(f"| {q.name} | {q.side} | {q.kind} | {w_:.0f} x {h_:.0f} | {len(q.slots)} | {where[id(q)]} |")
    (out / "frame.md").write_text("\n".join(lines) + "\n")
    return {"sheets": len(sheets), "parts": len(parts), "used_m2": used, "upper": u, "lower": lo,
            "frames": frames, "nest": sheets}


def sheets_png(path: Path, sheets, sheet_mm, title: str = ""):
    """The nested sheets, one above the other, parts coloured by kind and named."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon, Rectangle

    W, H = sheet_mm
    fig, axes = plt.subplots(len(sheets), 1, figsize=(14, 7.2 * len(sheets)), squeeze=False)
    for k, (ax, sheet) in enumerate(zip(axes[:, 0], sheets), 1):
        ax.add_patch(Rectangle((0, 0), W, H, fc="#eadfc8", ec="#777", lw=1.2))
        for q, x, y, turn in sheet:
            pts = placed(q, x, y, turn)
            ax.add_patch(Polygon(pts, closed=True, fc="#c99a62" if q.kind == "rib" else "#9c6d3f",
                                 ec="#2a2a2a", lw=0.5))
            h, tx, ty = _label_at(q, pts)
            ax.text(tx, ty, label(q), fontsize=4.5, color="#7a0000", family="monospace", va="bottom")
        ax.set_xlim(-20, W + 20)
        ax.set_ylim(-20, H + 20)
        ax.set_aspect("equal")
        ax.set_title(f"{title}sheet {k}: {W:.0f} x {H:.0f} mm, {len(sheet)} parts", loc="left", fontsize=11)
        ax.set_xticks(np.arange(0, W + 1, 200))
        ax.set_yticks(np.arange(0, H + 1, 200))
        ax.tick_params(labelsize=7)
    fig.tight_layout()
    fig.savefig(path, dpi=170)
    plt.close(fig)
