"""Hand-off for the moulds: the sized blended wing's outer mould line (OML)
as files a plug can be cut or printed from.

A plug is the positive shape the moulds are taken off (boat builders call
it the buck; car builders mean the ladder frame by that, see frame.py). The
wing parts at its chord line into an upper and a lower mould. Each plug is the
solid above (or below) that parting surface, with a flat face where the
moulds meet. The files are in millimetres, x forward, y port, z up:
- oml.stl: the whole outer surface, both sides;
- plug_upper.stl and plug_lower.stl: the two plug halves, closed solids
  ready for a CNC toolpath or a slicer;
- sections.csv: every spanwise station's upper and lower surface points,
  for hot-wire templates, CadQuery lofts or checking a cut plug;
- plug.md: sizes, the stock block each half needs, and skin area and
  laminate weight for ordering cloth.

`osprey recon-plug` also renders plugs.png: both halves on a bench, parting
faces down, the upper one inside a ghost of its stock block.

A smooth B-rep (STEP) loft from sections.csv in CadQuery is the next step
for CNC; these meshes are fine for printing a plug or roughing it.
"""

from __future__ import annotations

import math
import struct
from pathlib import Path

import numpy as np

from osprey.recon import geometry

MM = 1000.0


def _stl(path: Path, parts: list[tuple[np.ndarray, np.ndarray]], name: str):
    """Binary STL of several meshes, in millimetres."""
    tris = []
    for v, f in parts:
        tris.append(v[f] * MM)
    t = np.concatenate(tris)
    n = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    with open(path, "wb") as fh:
        fh.write(name.encode()[:80].ljust(80, b" "))
        fh.write(struct.pack("<I", len(t)))
        for k in range(len(t)):
            fh.write(struct.pack("<12fH", *n[k], *t[k, 0], *t[k, 1], *t[k, 2], 0))


def _meshes(rings: list[np.ndarray]) -> list[tuple[np.ndarray, np.ndarray]]:
    n = len(rings) // 2
    return [geometry.loft(rings[:n]), geometry.loft(rings[n:])]


def _area(v: np.ndarray, f: np.ndarray) -> float:
    return float(np.linalg.norm(np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]]), axis=1).sum() / 2)


def _volume(v: np.ndarray, f: np.ndarray) -> float:
    return float(abs(np.einsum("ij,ij->i", v[f[:, 0]], np.cross(v[f[:, 1]], v[f[:, 2]])).sum()) / 6)


def export(p, d: dict, out: Path, *, margin_mm: float = 25.0) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    oml = _meshes(geometry.bwb_surface(p, d))
    upper = _meshes(geometry.bwb_surface(p, d, half="upper"))
    lower = _meshes(geometry.bwb_surface(p, d, half="lower"))
    _stl(out / "oml.stl", oml, "osprey recon bwb outer mould line, mm")
    _stl(out / "plug_upper.stl", upper, "osprey recon bwb upper plug, mm")
    _stl(out / "plug_lower.stl", lower, "osprey recon bwb lower plug, mm")

    g = p.geometry
    y, le, c, tw, tc, lz = geometry._stations(p, d)
    with open(out / "sections.csv", "w") as fh:
        fh.write("station,y_mm,surface,x_mm,z_mm,chord_mm,twist_deg,t_over_c\n")
        for i in range(len(y)):
            u, z = geometry.naca4(g.airfoil_camber, g.airfoil_camber_pos, float(tc[i]), 60)
            pts = geometry._section(u, z, le[i], c[i], y[i], tw[i], lz[i])
            k = len(u) // 2
            for j, row in enumerate(pts):
                surf = "upper" if j <= k else "lower"
                fh.write(f"{i},{row[1] * MM:.2f},{surf},{row[0] * MM:.2f},{row[2] * MM:.2f},{c[i] * MM:.1f},"
                         f"{math.degrees(tw[i]):.2f},{tc[i]:.4f}\n")

    def box(meshes):
        allv = np.concatenate([v for v, _ in meshes]) * MM
        lo, hi = allv.min(0), allv.max(0)
        return lo, hi, hi - lo + 2 * margin_mm

    wet = sum(_area(v, f) for v, f in oml)
    lam = getattr(p.skin, "areal_kg_m2", None) or p.skin.wall_m * p.skin.density_kgm3
    info = {"span_mm": d["span_m"] * MM, "root_chord_mm": c[0] * MM, "tip_chord_mm": c[-1] * MM,
            "root_depth_mm": c[0] * tc[0] * MM, "sweep_deg": d.get("sweep_deg", 0.0),
            "wetted_m2": wet, "skin_kg": wet * lam, "enclosed_l": sum(_volume(v, f) for v, f in oml) * 1e3}
    lo_u, hi_u, stock_u = box(upper)
    lo_l, hi_l, stock_l = box(lower)
    info["stock_upper_mm"] = stock_u.tolist()
    info["stock_lower_mm"] = stock_l.tolist()
    lines = [f"# Plug hand-off: {p.mission.name}, blended wing body", "",
             "Outer mould line of the sized design, in millimetres (x forward, y port, z up). The wing parts at its "
             "chord line into an upper and a lower mould; each plug is the solid above or below that line.", "",
             "| | |", "|---|---|",
             f"| Span | {info['span_mm']:.0f} mm |",
             f"| Root / tip chord | {info['root_chord_mm']:.0f} / {info['tip_chord_mm']:.0f} mm |",
             f"| Centre-body depth | {info['root_depth_mm']:.0f} mm |",
             f"| Sweep (leading edge) | {info['sweep_deg']:.1f} deg |",
             f"| Wetted area / skin at {lam:g} kg/m² | {wet:.2f} m² / {info['skin_kg']:.2f} kg |",
             f"| Volume inside the OML | {info['enclosed_l']:.1f} l |",
             f"| Stock for the upper plug (L x W x H, with {margin_mm:g} mm margin) | "
             + " x ".join(f"{s_:.0f}" for s_ in stock_u) + " mm |",
             f"| Stock for the lower plug | " + " x ".join(f"{s_:.0f}" for s_ in stock_l) + " mm |", "",
             "Files: `oml.stl`, `plug_upper.stl`, `plug_lower.stl` (closed solids, binary STL), `sections.csv` "
             f"({len(y)} stations, upper and lower points).", "",
             "Notes:",
             "- The parting surface follows each section's chord line, so with washout it is gently twisted, not "
             "flat. Mount each plug on a parting board shaped to it.",
             "- The plugs are the bare OML. Add flanges, draft and a release finish before taking moulds off them.",
             "- Winglets, the payload fairing and the prop mount are separate parts and are not in these files.", ""]
    (out / "plug.md").write_text("\n".join(lines))
    return info
