"""Figures for the top-level README, made only from files in this repository.

    uv run python docs/img/make_readme_figures.py

Reads design/*.toml (through osprey.params) and the kept runs under runs/.
Writes each figure twice into docs/img/, once for GitHub's light theme and
once (``-dark``) for its dark theme; the README picks one with <picture>.
Archived runs are only read, never written.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Polygon, Rectangle, Wedge  # noqa: E402
from PIL import Image  # noqa: E402

from osprey import params  # noqa: E402
from osprey.occlusion import Occluders  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
IMG = ROOT / "docs" / "img"
RUNS = ROOT / "runs"
GECKO = RUNS / "2026-11-06_gecko-sweep"
FIRST = RUNS / "2026-11-06_first-sweep"
RENDER = RUNS / "2026-11-06_gecko-docking-render"
RECON = RUNS / "2026-11-06_recon-missions"
JOBS = [("sar-datum", "Search: MOB 3 km astern"), ("sar-convoy", "Search: 5 km astern, boat sails on"),
        ("sar-offshore", "Search: MOB 10 km, sea state 4"), ("scout-anchorage", "Survey: anchorage 8 km ahead"),
        ("scout-island", "Survey: island shore from anchor"), ("inspect-vessel", "Inspect: vessel 5 km off")]
SHORT = {"sar-datum": "MOB 3 km", "sar-convoy": "5 km, sailing on", "sar-offshore": "MOB 10 km",
         "scout-anchorage": "anchorage", "scout-island": "island", "inspect-vessel": "vessel"}

# Surfaces match GitHub's page backgrounds so the figures sit flush on either theme.
# Series and status colours are the validated default data-viz palette.
THEMES = {
    "light": dict(surface="#ffffff", ink="#0b0b0b", ink2="#52514e", muted="#898781", grid="#e1e0d9",
                  axis="#c3c2b7", panel="#f3f2ee", series=["#2a78d6", "#eb6834", "#1baf7a", "#6250d6", "#e87ba4"],
                  hull="#d9d7cf", mast="#6b6a65", good="#0ca30c", critical="#d03b3b"),
    "dark": dict(surface="#0d1117", ink="#f0efec", ink2="#c3c2b7", muted="#898781", grid="#2c2c2a",
                 axis="#383835", panel="#1a1d23", series=["#3987e5", "#d95926", "#199e70", "#9085e9", "#d55181"],
                 hull="#3a3a37", mast="#a8a69e", good="#0ca30c", critical="#d03b3b"),
}
FONT = {"font.family": "sans-serif", "font.sans-serif": ["DejaVu Sans"], "font.size": 10,
        "svg.hashsalt": "osprey-readme"}   # stable SVG ids, so a rerun changes nothing


def _save(fig, stem: str, theme: str, ext: str = "png"):
    name = f"{stem}{'-dark' if theme == 'dark' else ''}.{ext}"
    kw = {"dpi": 160} if ext == "png" else {}
    fig.savefig(IMG / name, facecolor=fig.get_facecolor(), bbox_inches="tight", pad_inches=0.15,
                metadata={"Software": None} if ext == "png" else {"Date": None}, **kw)
    plt.close(fig)
    print("wrote", IMG / name)


def _style(ax, t):
    ax.set_facecolor(t["surface"])
    for s in ax.spines.values():
        s.set_color(t["axis"])
    ax.tick_params(colors=t["ink2"], labelcolor=t["ink2"])
    ax.xaxis.label.set_color(t["ink2"])
    ax.yaxis.label.set_color(t["ink2"])
    ax.title.set_color(t["ink"])


def _pct(s: str) -> float:
    return float(re.search(r"([\d.]+)\s*%", s).group(1))


def _num(s: str) -> float:
    return float(re.search(r"[-+]?[\d,]*\.?\d+", s).group(0).replace(",", ""))


def _calc(path: Path) -> dict[str, dict]:
    return {c["name"]: c for c in json.loads(path.read_text())}


def _sim_md(path: Path) -> dict:
    """Need-met per task and the whole-horizon-swept share from a sim.md."""
    txt = path.read_text()
    swept = re.search(r"Whole horizon swept: \*\*([\d.]+)%", txt)
    met = {m.group(1): float(m.group(2)) for m in re.finditer(r"^\| ([\w-]+) \|[^|]*\|[^|]*\|[^|]*\| (\d+)% \|",
                                                              txt, re.M)}
    return {"swept": float(swept.group(1)) if swept else None, "met": met}


# --------------------------------------------------------------------------- data from the kept runs

def rig_comparison() -> dict:
    """Five underway and docking numbers for the three mast rigs, all from kept runs."""
    rigs = {}
    for rig in ("gecko5", "mast5-spreaders", "mast5"):
        cw = _sim_md(GECKO / "coastal-watch" / rig / "sim.md")
        mob = _sim_md(GECKO / "mob" / rig / "sim.md")
        dock_dir = (GECKO if rig == "gecko5" else FIRST) / "docking" / rig
        opt = _calc(dock_dir / "calc.json")["Same, with aims optimized for two views"]
        rigs[rig] = {
            "Whole horizon swept\n(coastal-watch, share of time)": cw["swept"],
            "Ferry recognized\n(coastal-watch, need met)": cw["met"]["ferry"],
            "Buoy kept in view during a MOB\n(need met)": mob["met"]["buoy-2"],
            "Water within 3 m of hull,\n2+ cameras (optimized aims)": _pct(opt["value"]),
            "Hull edge with a stereo pair\n(optimized aims)":
                _pct(opt["note"].split("hull edge with a stereo pair:")[1]),
        }
    return rigs


def budgets() -> list[tuple[str, float, float, str, str]]:
    """(label, value, limit, value text, status) for gecko5's pod budgets, coastal-watch report."""
    c = _calc(GECKO / "coastal-watch" / "gecko5" / "calc.json")
    out = []
    mass = c["Mass on the mast / masthead equivalent"]
    v = float(mass["value"].split("/")[1].split()[0])
    out.append(("Mass aloft, masthead equivalent", v, _num(mass["limit"]), f"{v:g} / {_num(mass['limit']):g} kg",
                mass["status"]))
    e = c["Energy per day underway"]
    out.append(("Energy per day underway", _num(e["value"]), _num(e["limit"]),
                f"{_num(e['value']):g} / {_num(e['limit']):g} Ah", e["status"]))
    top = c["top: peak draw at the PoE port"]
    out.append(("Masthead pod, PoE peak draw", _num(top["value"]), _num(top["limit"]),
                f"{_num(top['value']):g} / {_num(top['limit']):g} W", top["status"]))
    fwd = c["fwd: peak draw at the PoE port"]
    lim = params._toml(params.DESIGN / "electronics.toml")["poe"]["802.3bt Type 4"]
    out.append(("Other four pods, PoE peak draw", _num(fwd["value"]), lim, f"{_num(fwd['value']):g} / {lim:g} W",
                fwd["status"]))
    for name, label, unit in (
        ("Relative orientation with pod gyros between horizon fixes", "Pod-to-pod pointing, with gyros", "urad"),
        ("top: SOC encoder load", "SOC video encoder load", "Mpx/s"),
        ("All pods on the switch uplink to the pilot", "Switch uplink to the pilot", "Mb/s"),
        ("top: detection on full-resolution frames", "Detection on full-res frames", "TOPS"),
    ):
        r = c[name]
        out.append((label, _num(r["value"]), _num(r["limit"]),
                    f"{_num(r['value']):g} / {_num(r['limit']):g} {unit}", r["status"]))
    return out


# --------------------------------------------------------------------------- figures

def fig_rig_compare(theme: str):
    t = THEMES[theme]
    data = rig_comparison()
    rigs = list(data)
    metrics = list(data[rigs[0]])
    with plt.rc_context(FONT):
        fig, ax = plt.subplots(figsize=(8.6, 5.4), facecolor=t["surface"])
        _style(ax, t)
        h = 0.26
        for i, m in enumerate(metrics):
            for j, rig in enumerate(rigs):
                y = i + (j - 1) * (h + 0.02)
                v = data[rig][m]
                ax.barh(y, max(v, 0.6), height=h, color=t["series"][j], edgecolor=t["surface"], linewidth=1)
                ax.text(v + 1.2, y, f"{v:g} %", va="center", ha="left", fontsize=8.5, color=t["ink2"])
        ax.set_yticks(range(len(metrics)), metrics, fontsize=9, color=t["ink"])
        ax.invert_yaxis()
        ax.set_xlim(0, 112)
        ax.set_xticks([0, 25, 50, 75, 100], ["0", "25", "50", "75", "100 %"])
        ax.grid(axis="x", color=t["grid"], lw=0.8)
        ax.set_axisbelow(True)
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
        ax.tick_params(axis="y", length=0)
        handles = [Rectangle((0, 0), 1, 1, color=t["series"][j]) for j in range(len(rigs))]
        labels = ["gecko5: 5 pods, 10 eyes, sector watch", "mast5-spreaders: 5 PTZs, 1 reserve",
                  "mast5: 5 PTZs, side ones on mast brackets, 1 reserve"]
        leg = ax.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.38, -0.07), ncol=2, frameon=False,
                        fontsize=8.5)
        for txt in leg.get_texts():
            txt.set_color(t["ink2"])
        ax.set_title("Three mast rigs, same boat and scenarios (higher is better)", loc="left", fontsize=11,
                     color=t["ink"], pad=10)
        _save(fig, "rig-compare", theme)


def fig_budgets(theme: str):
    t = THEMES[theme]
    rows = budgets()
    with plt.rc_context(FONT):
        fig, ax = plt.subplots(figsize=(8.6, 4.2), facecolor=t["surface"])
        _style(ax, t)
        for i, (label, v, lim, txt, status) in enumerate(rows):
            frac = 100 * v / lim
            col = t["critical"] if status == "FAIL" else t["good"]
            ax.barh(i, frac, height=0.6, color=col)
            word = "FAIL" if status == "FAIL" else "pass"
            ax.text(max(frac, 100) + 5, i, f"{word}  {txt}", va="center", ha="left", fontsize=8.5,
                    color=t["ink"] if status == "FAIL" else t["ink2"],
                    fontweight="bold" if status == "FAIL" else "normal")
        ax.axvline(100, color=t["ink2"], lw=1.2, ls=(0, (4, 3)))
        ax.text(100, -0.85, "limit", ha="center", va="bottom", fontsize=8.5, color=t["ink2"])
        ax.set_yticks(range(len(rows)), [r[0] for r in rows], fontsize=9, color=t["ink"])
        ax.invert_yaxis()
        ax.set_ylim(len(rows) - 0.5, -1.0)
        ax.set_xlim(0, 470)
        ax.set_xticks([0, 100, 200, 300], ["0", "100 %", "200 %", "300 %"])
        ax.set_xlabel("share of the limit, from the gecko5 coastal-watch report (REF inputs)")
        ax.grid(axis="x", color=t["grid"], lw=0.8)
        ax.set_axisbelow(True)
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
        ax.tick_params(axis="y", length=0)
        ax.set_title("gecko5 budgets: compute and network fit, mass and power do not", loc="left", fontsize=11,
                     color=t["ink"], pad=10)
        _save(fig, "budgets", theme)


def fig_nest_layout(theme: str):
    """Side view of the mast with the five pods, and a plan view of their watch sectors."""
    t = THEMES[theme]
    p = params.load("coastal-watch", "gecko5")
    b, m, sp = p.boat, p.mast, p.sailplan
    pods = p.pod
    occ = Occluders(mast=(m.radius_m, m.deck_z_m, m.truck_z_m), hull=b)
    col = {d.id: t["series"][i] for i, d in enumerate(pods)}
    with plt.rc_context(FONT):
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 6.2), facecolor=t["surface"],
                                       gridspec_kw={"width_ratios": [1.05, 1]})
        # --- side elevation, bow to the right
        _style(ax1, t)
        ax1.add_patch(Polygon([[b.stern_x_m, 0], [b.bow_x_m, 0], [b.bow_x_m, b.freeboard_m],
                               [b.stern_x_m, b.freeboard_m]], closed=True, color=t["hull"], lw=0))
        ax1.axhline(0, color=t["series"][0], lw=1, alpha=0.6)
        ax1.plot([0, 0], [m.deck_z_m, m.truck_z_m], color=t["mast"], lw=4, solid_capstyle="butt")
        for z in m.spreaders_z_m:
            ax1.plot([-0.25, 0.25], [z, z], color=t["mast"], lw=2)
        ax1.plot([0, -sp.boom_length_m], [sp.boom_z_m, sp.boom_z_m], color=t["mast"], lw=2.5)
        ax1.plot([sp.forestay_tack_x_m, 0], [b.freeboard_m, sp.forestay_head_z_m], color=t["muted"], lw=1)
        for d in pods:
            x, y, z = d.pos_m
            ax1.add_patch(FancyBboxPatch((x - 0.18, z - 0.32), 0.36, 0.64, boxstyle="round,pad=0.02,rounding_size=0.08",
                                         color=col[d.id], lw=0, zorder=5))
        labels = {}
        for d in pods:
            labels.setdefault(d.pos_m[2], []).append(d.id)
        for z, ids in labels.items():
            ax1.annotate(f"{' / '.join(ids)}  {z:.2f} m", (0.3, z), xytext=(1.6, z), va="center", fontsize=9,
                         color=t["ink"], arrowprops=dict(arrowstyle="-", color=t["muted"], lw=0.8))
        ax1.text(b.bow_x_m, -0.6, "bow", ha="right", va="top", color=t["ink2"], fontsize=9)
        ax1.text(b.stern_x_m, -0.6, "stern", ha="left", va="top", color=t["ink2"], fontsize=9)
        ax1.set_xlim(b.stern_x_m - 0.3, b.bow_x_m + 3.2)
        ax1.set_ylim(-1.6, 20.2)
        ax1.set_aspect("equal")
        ax1.set_ylabel("height above the waterline, m")
        ax1.set_xticks([])
        for s in ("top", "right", "bottom"):
            ax1.spines[s].set_visible(False)
        ax1.set_title("Pods on the mast (side view)", loc="left", fontsize=11, color=t["ink"])
        # --- plan view, bow up, port to the left
        _style(ax2, t)
        xs = np.linspace(b.stern_x_m, b.bow_x_m, 200)
        hw = occ.half_beam(xs)
        ax2.fill(np.r_[hw, -hw[::-1]], np.r_[xs, xs[::-1]], color=t["hull"], lw=0, zorder=1)
        R = 8.5
        for i, d in enumerate(pods):
            x, y, _ = d.pos_m
            px, py = -y, x                                   # starboard to the right, forward up
            if d.sector_deg >= 360:
                ax2.add_patch(plt.Circle((px, py), R + 1.6, fill=False, ec=col[d.id], lw=2.2, ls=(0, (5, 3)), zorder=3))
                ax2.text(0, R + 1.6 + py, f"{d.id}: all round", ha="center", va="bottom", zorder=8,
                         bbox=dict(fc=t["surface"], ec="none", pad=1.5), fontsize=9, color=t["ink"])
                continue
            # face_az is measured toward port from the bow; on the page that is counter-clockwise from up.
            centre = 90 + d.face_az_deg
            ax2.add_patch(Wedge((px, py), R, centre - d.sector_deg / 2, centre + d.sector_deg / 2,
                                fc=col[d.id], alpha=0.22, ec="none", zorder=2))
            ax2.add_patch(Wedge((px, py), R, centre - d.sector_deg / 2, centre + d.sector_deg / 2,
                                fc="none", ec=col[d.id], lw=1.6, zorder=3))
            a = np.radians(centre)
            ax2.text(px + 0.72 * R * np.cos(a), py + 0.72 * R * np.sin(a), f"{d.id}\n{d.sector_deg:g}°",
                     ha="center", va="center", fontsize=9, color=t["ink"], zorder=6)
        for d in pods:
            ax2.plot(-d.pos_m[1], d.pos_m[0], "o", ms=7, color=col[d.id], mec=t["surface"], mew=1.2, zorder=7)
        ax2.text(0, b.bow_x_m + 0.3, "bow", ha="center", va="bottom", fontsize=9, color=t["ink2"], zorder=6)
        ax2.text(-R - 1.0, -R - 1.4, "port", ha="left", fontsize=9, color=t["ink2"])
        ax2.text(R + 1.0, -R - 1.4, "starboard", ha="right", fontsize=9, color=t["ink2"])
        ax2.set_xlim(-R - 1.8, R + 1.8)
        ax2.set_ylim(-R - 1.8, R + 2.6)
        ax2.set_aspect("equal")
        ax2.axis("off")
        ax2.set_title("Watch sectors (plan view, overlapping)", loc="left", fontsize=11, color=t["ink"])
        fig.tight_layout()
        _save(fig, "nest-layout", theme)


def fig_pod(theme: str):
    """Schematic of one gecko pod, annotated from design/electronics.toml and design/cameras.toml."""
    t = THEMES[theme]
    el = params._toml(params.DESIGN / "electronics.toml")
    cams = params._toml(params.DESIGN / "cameras.toml")["camera"]
    kit, soc, imu = el["kit"]["gecko"], el["soc"]["orin_nx"], el["imu"]["mems_industrial"]
    up, down, lng = cams["ptz_mid"], cams["ptz_mid_down"], cams["ptz_long"]
    pod_kg = kit["housing_kg"] + soc["mass_kg"] + imu["mass_kg"]
    gap = kit["up_dz_m"] - kit["down_dz_m"]
    with plt.rc_context(FONT):
        fig, ax = plt.subplots(figsize=(9.5, 6.0), facecolor=t["surface"])
        ax.set_facecolor(t["surface"])
        ax.set_xlim(-3.2, 12.5)
        ax.set_ylim(-6.0, 5.4)
        ax.set_aspect("equal")
        ax.axis("off")
        # mast and cable
        ax.add_patch(Rectangle((-2.6, -6.0), 0.7, 11.4, color=t["mast"], lw=0))
        ax.text(-2.25, 5.0, "mast", rotation=90, ha="center", va="top", color=t["surface"], fontsize=9)
        ax.plot([-1.9, -1.2], [0, 0], color=t["mast"], lw=6, solid_capstyle="butt")       # clamp arm
        ax.plot([-1.0, -1.6, -1.6], [-0.9, -0.9, -6.0], color=t["series"][1], lw=2)
        # fields of regard (camera tilt limits, measured from the horizontal, outward)
        cy_up, cy_dn = 2.25, -2.25
        for cy, cam, c in ((cy_up, up, t["series"][0]), (cy_dn, down, t["series"][2])):
            lo, hi = cam["tilt_deg"]
            ax.add_patch(Wedge((1.6, cy), 3.6, lo, hi, fc=c, alpha=0.16, ec="none", zorder=1))
            ax.add_patch(Wedge((1.6, cy), 3.6, lo, hi, fc="none", ec=c, lw=1, ls=(0, (3, 3)), zorder=1))
        # pod body
        ax.add_patch(FancyBboxPatch((-1.2, -1.3), 5.6, 2.6, boxstyle="round,pad=0.05,rounding_size=0.5",
                                    fc=t["panel"], ec=t["ink2"], lw=1.4, zorder=3))
        for i, (name, c) in enumerate((("SOC", t["series"][3]), ("IMU", t["series"][4]),
                                       ("PoE PD", t["series"][1]))):
            ax.add_patch(FancyBboxPatch((-0.85 + i * 1.75, -0.45), 1.5, 0.9,
                                        boxstyle="round,pad=0.02,rounding_size=0.15",
                                        fc=c, ec="none", zorder=4))
            ax.text(-0.1 + i * 1.75, 0, name, ha="center", va="center", fontsize=8.5, color="#ffffff",
                    fontweight="bold", zorder=5)
        # upper and lower PTZ: a yoke and a dome each
        for cy, sgn, c in ((cy_up, 1, t["series"][0]), (cy_dn, -1, t["series"][2])):
            y0 = 1.3 if sgn > 0 else cy                       # the yoke between the pod body and the dome
            ax.add_patch(Rectangle((1.3, y0), 0.6, abs(cy) - 1.3, color=t["ink2"], lw=0, zorder=2))
            ax.add_patch(plt.Circle((1.6, cy), 0.75, color=c, zorder=4))
            ax.add_patch(plt.Circle((2.05, cy), 0.28, color=t["surface"], zorder=5))
        ax.annotate("", xy=(5.3, cy_up), xytext=(5.3, cy_dn),
                    arrowprops=dict(arrowstyle="<->", color=t["ink2"], lw=1))
        ax.text(5.45, 0, f"{gap:.2f} m\nbetween\nthe eyes", va="center", fontsize=8.5, color=t["ink2"])
        # annotations
        x0 = 7.0
        notes = [
            (cy_up + 1.6, t["series"][0], "Upper eye: PTZ",
             f"4K, {up['focal_mm'][0]:g}-{up['focal_mm'][1]:g} mm, "
             f"tilt {up['tilt_deg'][0]:+g}° to {up['tilt_deg'][1]:+g}°\n"
             f"masthead pod: long zoom {lng['focal_mm'][0]:g}-{lng['focal_mm'][1]:g} mm, fast stage"),
            (0.75, t["series"][3], "SOC",
             f"Orin NX class, {soc['tops_int8']:g} TOPS INT8, {soc['power_w'][0]:g}/{soc['power_w'][1]:g} W\n"
             "encodes both streams, detects before compression"),
            (-0.75, t["series"][4], "6-axis IMU",
             f"gyro + accel at {imu['rate_hz']:g} Hz; attitude on every frame,\n"
             f"PTP clock ({el['network']['ptp_sync_us']:g} us shutter sync)"),
            (-2.25, t["series"][1], "PoE PD, one gigabit cable",
             f"power and data down the mast; 802.3bt Type 4 = {el['poe']['802.3bt Type 4']:g} W"),
            (cy_dn - 1.2, t["series"][2], "Lower eye: the same PTZ, hung inverted",
             f"tilt {down['tilt_deg'][0]:+g}° to {down['tilt_deg'][1]:+g}°; water, deck and dock"),
        ]
        for y, c, head, body in notes:
            ax.add_patch(Rectangle((x0 - 0.35, y - 0.15), 0.2, 0.3, color=c, lw=0))
            ax.text(x0, y + 0.02, head, fontsize=9.5, fontweight="bold", color=t["ink"], va="bottom")
            ax.text(x0, y - 0.05, body, fontsize=8.3, color=t["ink2"], va="top", linespacing=1.3)
        ax.text(7.0, -5.35, "Shaded: each eye's tilt range, facing outward. The pod body hides\n"
                "straight down from the upper eye and the sky from the lower one.\n"
                f"Pod electronics and housing {pod_kg:.2f} kg. All values are REF stand-ins.",
                fontsize=8, color=t["muted"], va="bottom", linespacing=1.4)
        ax.set_title("A gecko pod: two eyes, one cable", loc="left", fontsize=12, color=t["ink"])
        _save(fig, "gecko-pod", theme, ext="svg")


def fig_synthetic(theme: str):
    """One frame of one camera from the kept gecko5 docking render: RGB, depth and class mask."""
    t = THEMES[theme]
    cam, frame = "port-down", "0050"
    d = RENDER / cam
    rgb = np.asarray(Image.open(d / f"rgb_{frame}.png").convert("RGB"))
    depth = np.asarray(Image.open(d / f"depth_{frame}.png")).astype(float) / 1000.0
    cls = np.asarray(Image.open(d / f"class_{frame}.png"))
    names = json.loads((RENDER / "classes.json").read_text())["classes"]
    vals, counts = np.unique(cls, return_counts=True)
    present = [int(v) for v, n in zip(vals, counts) if v < len(names) and n >= 0.001 * cls.size]   # visible classes
    palette = t["series"] + ["#eda100", "#008300", "#e34948", "#898781"]
    lut = np.zeros((256, 3))
    for i, v in enumerate(present):
        lut[v] = matplotlib.colors.to_rgb(palette[i])
    cls_rgb = lut[cls]
    with plt.rc_context(FONT):
        fig, axs = plt.subplots(1, 3, figsize=(12, 2.9), facecolor=t["surface"])
        axs[0].imshow(rgb)
        axs[0].set_title("RGB", color=t["ink"], fontsize=10, loc="left")
        im = axs[1].imshow(depth, cmap="Greys", vmin=0, vmax=np.ceil(depth.max()))
        axs[1].set_title("metric depth (dark = far)", color=t["ink"], fontsize=10, loc="left")
        cb = fig.colorbar(im, ax=axs[1], fraction=0.035, pad=0.02)
        cb.set_label("m", color=t["ink2"])
        cb.ax.tick_params(colors=t["ink2"], labelsize=8)
        cb.outline.set_edgecolor(t["axis"])
        axs[2].imshow(cls_rgb)
        axs[2].set_title("class mask", color=t["ink"], fontsize=10, loc="left")
        handles = [Rectangle((0, 0), 1, 1, color=palette[i]) for i in range(len(present))]
        leg = axs[2].legend(handles, [names[v] for v in present], loc="center left", bbox_to_anchor=(1.01, 0.5),
                            frameon=False, fontsize=8.5)
        for txt in leg.get_texts():
            txt.set_color(t["ink2"])
        for ax in axs:
            ax.set_xticks([])
            ax.set_yticks([])
            for s in ax.spines.values():
                s.set_visible(False)
        fig.tight_layout()
        _save(fig, "synthetic-frame", theme)


# --------------------------------------------------------------------------- Recon

_FLOWN: dict[tuple, tuple] = {}


def _recon(mission: str, design: str | None = None) -> tuple:
    """A mission's kept design (or another mission's), its kept flight summary,
    and the flight itself, re-flown from the kept design (the sim is deterministic)."""
    key = (mission, design or mission)
    if key not in _FLOWN:
        from osprey.recon import flight
        from osprey.recon.params import load as load_mission

        p = load_mission(mission)
        d = json.loads((RECON / key[1] / "design.json").read_text())
        f = json.loads((RECON / mission / "flight.json").read_text())
        ac = flight.Aircraft.from_design(p, d)
        _FLOWN[key] = (p, d, f, ac, flight.simulate(p, ac))
    return _FLOWN[key]


def _matrix() -> dict:
    return json.loads((RECON / "matrix.json").read_text())


def fig_recon_jobs(theme: str):
    """The one bird through every job: out, on task, home, and what it had left."""
    t = THEMES[theme]
    mx = _matrix()
    bird = mx["one_bird"]
    cells = mx["cells"][bird]
    with plt.rc_context(FONT):
        fig, ax = plt.subplots(figsize=(9.2, 3.9), facecolor=t["surface"])
        _style(ax, t)
        for i, (m, label) in enumerate(JOBS):
            s = cells[m]
            on, task, total = s["on_scene_s"] / 60, s["task_s"] / 60, s["flight_time_s"] / 60
            for x0, w, col in ((0, on, t["series"][0]), (on, task, t["series"][1]), (on + task, total - on - task,
                                                                                    t["series"][2])):
                ax.barh(i, w, left=x0, height=0.62, color=col, edgecolor=t["surface"], lw=0.8)
            goal = f"{s['progress']:.0%} {s['progress_label']}"
            ax.text(total + 1.5, i, f"{goal}, home with {s['energy_left_frac']:.0%}", va="center", fontsize=8.5,
                    color=t["ink2"])
        ax.set_yticks(range(len(JOBS)), [lab for _, lab in JOBS], fontsize=9, color=t["ink"])
        ax.invert_yaxis()
        ax.set_xlim(0, 160)
        ax.set_xlabel("minutes since launch: out (blue), on the job (orange), home (green)")
        ax.grid(axis="x", color=t["grid"], lw=0.8)
        ax.set_axisbelow(True)
        for s_ in ("top", "right", "left"):
            ax.spines[s_].set_visible(False)
        ax.tick_params(axis="y", length=0)
        d = mx["designs"][bird]
        ax.set_title(f"One bird, six jobs: the {d['mass_total_kg']:.2f} kg, {d['span_m']:.2f} m airframe does them all",
                     loc="left", fontsize=11, color=t["ink"], pad=10)
        _save(fig, "recon-jobs", theme)


def fig_recon_matrix(theme: str):
    """Every sized airframe through every mission."""
    t = THEMES[theme]
    mx = _matrix()
    order, best = mx["order"], mx["one_bird"]
    names = [m for m, _ in JOBS]
    short = {m: lab.split(": ")[1] for m, lab in JOBS}
    with plt.rc_context(FONT):
        fig, ax = plt.subplots(figsize=(9.6, 3.9), facecolor=t["surface"])
        _style(ax, t)
        for i, dn in enumerate(order):
            for j, m in enumerate(names):
                s = mx["cells"][dn][m]
                good = s["outcome"] == "recovered" and s["goal_met"]
                col = t["good"] if good else t["critical"]
                alpha = 0.25 + 0.65 * s["energy_left_frac"] if good else 0.28
                ax.add_patch(Rectangle((j + 0.03, i + 0.05), 0.94, 0.9, color=col, alpha=alpha, lw=0))
                txt = f"{s['energy_left_frac']:.0%} left" if good else f"{s['progress']:.0%} {s['progress_label']}"
                ax.text(j + 0.5, i + 0.5, txt, ha="center", va="center", fontsize=8, color=t["ink"])
        ax.set_xlim(0, len(names))
        ax.set_ylim(len(order), 0)
        ax.set_xticks(np.arange(len(names)) + 0.5, [short[m] for m in names], fontsize=8, color=t["ink2"],
                      rotation=18, ha="right")
        lab = {m: lab_ for m, lab_ in JOBS}
        ax.set_yticks(np.arange(len(order)) + 0.5,
                      [f"{lab[dn].split(': ')[1]}, {mx['designs'][dn]['mass_total_kg']:.2f} kg"
                       + ("  (the one)" if dn == best else "") for dn in order], fontsize=8, color=t["ink"])
        for s_ in ax.spines.values():
            s_.set_visible(False)
        ax.tick_params(length=0)
        ax.set_title("Each airframe sized for one job, flown through all of them (green: home with the job done)",
                     loc="left", fontsize=10.5, color=t["ink"], pad=10)
        _save(fig, "recon-matrix", theme)


def fig_recon_wings(theme: str):
    """Each mission's wing to scale, and what its take-off mass is made of."""
    t = THEMES[theme]
    parts = [("fixed: body, avionics, gimbal, motor", "fixed_kg", t["muted"]), ("battery", "battery_kg", t["series"][1]),
             ("printed shell", "skin_kg", t["series"][0]), ("carbon spar", "spar_kg", t["series"][4])]
    with plt.rc_context(FONT):
        fig, (ax, bx) = plt.subplots(1, 2, figsize=(10.4, 5.6), facecolor=t["surface"],
                                     gridspec_kw={"width_ratios": [2.0, 1.15]})
        for a in (ax, bx):
            _style(a, t)
        for i, (m, label) in enumerate(JOBS):
            p, d, f, *_ = _recon(m)
            y = np.array(d["half_span_y_m"])
            c = np.array(d["chords_m"])
            yc = -i * 0.5
            fo = p.wing.fem_origin
            for side in (-1, 1):
                ax.fill(np.r_[side * y, side * y[::-1]], np.r_[yc + fo * c, (yc + fo * c - c)[::-1]],
                        color=t["series"][0], alpha=0.25, ec=t["series"][0], lw=1.2)
                ax.plot(side * y, np.full_like(y, yc), color=t["series"][4], lw=1.6)
            bed = p.print.bed_m[2]
            for k in range(1, int(np.ceil(d["span_m"] / 2 / bed))):
                for side in (-1, 1):
                    ax.plot([side * k * bed] * 2, [yc + fo * c[0] + 0.02, yc + fo * c[0] - c[0] - 0.02],
                            color=t["ink2"], lw=0.8, ls=(0, (2, 2)))
            ax.text(-1.2, yc + 0.15, label, fontsize=8.5, color=t["ink"], ha="left")
            ax.text(1.2, yc + 0.15, f"{d['span_m']:.2f} m, {d['print_panels']} panels", fontsize=8,
                    color=t["ink2"], ha="right")
            bottom = 0.0
            for name, key, col in parts:
                bx.bar(i, d[key], bottom=bottom, color=col, width=0.62, edgecolor=t["surface"], lw=0.8)
                bottom += d[key]
            bx.text(i, bottom + 0.05, f"{bottom:.2f}", ha="center", fontsize=8, color=t["ink"])
        ax.set_xlim(-1.25, 1.25)
        ax.set_ylim(-0.5 * len(JOBS) + 0.1, 0.35)
        ax.set_aspect("equal")
        ax.set_yticks([])
        ax.set_xlabel("span (m), to scale; spar in pink, print joints dotted")
        for s_ in ("top", "right", "left"):
            ax.spines[s_].set_visible(False)
        ax.set_title("Each job's own wing", loc="left", fontsize=11, color=t["ink"], pad=10)
        bx.set_xticks(range(len(JOBS)), [SHORT[m] for m, _ in JOBS], fontsize=8, color=t["ink2"],
                      rotation=30, ha="right")
        bx.set_ylabel("take-off mass (kg)")
        bx.set_ylim(0, 3.6)
        bx.grid(axis="y", color=t["grid"], lw=0.8)
        bx.set_axisbelow(True)
        for s_ in ("top", "right"):
            bx.spines[s_].set_visible(False)
        handles = [Rectangle((0, 0), 1, 1, color=c_) for _, _, c_ in parts]
        leg = bx.legend(handles, [n for n, _, _ in parts], loc="upper left", fontsize=7.5, frameon=False)
        for txt in leg.get_texts():
            txt.set_color(t["ink2"])
        bx.set_title("Mass", loc="left", fontsize=11, color=t["ink"], pad=10)
        fig.tight_layout()
        _save(fig, "recon-wings", theme)


def _track_axes(ax, t, mission: str):
    from matplotlib.colors import LinearSegmentedColormap

    p, d, f, ac, r = _recon(mission)
    task = r["task"]
    cmap = LinearSegmentedColormap.from_list("p", [t["surface"], t["series"][3]])
    if hasattr(task, "grid"):
        g = task.grid
        off = g.datum + g.drift * r["t"][-1]
        shade = g.prior if task.kind == "search" else g.prior * (1 - g.unfound)
        ax.pcolormesh(g.x + off[0], g.y + off[1], shade, cmap=cmap, shading="auto", vmin=0, vmax=shade.max())
    cols = {"outbound": t["series"][0], "task": t["series"][1], "return": t["series"][2]}
    for name, col in cols.items():
        sel = r["phase"] == name
        ax.plot(np.where(sel, r["x"], np.nan), np.where(sel, r["y"], np.nan), color=col, lw=1.2,
                label={"task": task.kind}.get(name, name))
    ax.plot(r["boat_x"], r["boat_y"], color=t["ink"], lw=2.2, label="boat")
    ax.plot([0], [0], marker="^", color=t["ink"], ms=8)
    if task.kind != "survey":
        dd = np.array([task.where(tt) for tt in r["t"]])
        ax.plot(dd[:, 0], dd[:, 1], color=t["series"][3], lw=1, ls=(0, (3, 2)),
                label="person, drifting" if task.kind == "search" else "vessel")
    ax.set_aspect("equal")
    ax.set_xlabel("east (m)")
    for s_ in ("top", "right"):
        ax.spines[s_].set_visible(False)
    leg = ax.legend(loc="best", fontsize=7.5, frameon=False)
    for txt in leg.get_texts():
        txt.set_color(t["ink2"])
    return p, f


def fig_recon_tracks(theme: str):
    """Three kinds of job, flown: a search, a survey, an inspection."""
    t = THEMES[theme]
    picks = [("sar-datum", "Search: MOB 3 km astern"), ("scout-anchorage", "Survey: the anchorage 8 km ahead"),
             ("inspect-vessel", "Inspect: a vessel 5 km off")]
    with plt.rc_context(FONT):
        fig, axs = plt.subplots(1, 3, figsize=(12, 4.8), facecolor=t["surface"],
                                gridspec_kw={"width_ratios": [0.8, 0.9, 1.3]})
        for ax, (m, title) in zip(axs, picks):
            _style(ax, t)
            p, f = _track_axes(ax, t, m)
            what = {"search": "POD", "survey": "imaged", "inspect": "of the orbits"}[f["kind"]]
            ax.set_title(f"{title}\n{f['progress']:.0%} {what}; home in {f['flight_time_s'] / 60:.0f} min with "
                         f"{f['energy_left_frac']:.0%} battery", loc="left", fontsize=9.5, color=t["ink"], pad=8)
        axs[0].set_ylabel("north (m)")
        fig.tight_layout()
        _save(fig, "recon-tracks", theme)


def fig_hero(theme: str):
    """Both halves of Osprey side by side: the mast pods docking, the drone out scouting."""
    t = THEMES[theme]
    sheet = Image.open(IMG / "gecko-docking-sheet.png").convert("RGB")
    tw, th = sheet.size[0] // 4, sheet.size[1] // 3            # 4 x 3 contact sheet of 480 x 270 tiles
    tiles = Image.new("RGB", (2 * tw, 2 * th))
    # The four lower eyes on the dock: top-down, fwd-down / port-down, stbd-down.
    for k, (r, c) in enumerate([(0, 1), (0, 3), (1, 1), (1, 3)]):
        tiles.paste(sheet.crop((c * tw, r * th, (c + 1) * tw, (r + 1) * th)), ((k % 2) * tw, (k // 2) * th))
    with plt.rc_context(FONT):
        fig = plt.figure(figsize=(12, 4.6), facecolor=t["surface"])
        a1 = fig.add_axes([0.0, 0.0, 0.6, 0.9])
        a1.imshow(tiles)
        a1.set_axis_off()
        a1.set_title("Osprey Nest: the pods' lower eyes, docking (synthetic frames)", loc="left", fontsize=11,
                     color=t["ink"])
        # The bird over the sea with the boat below (osprey recon-render, offshore design), cropped.
        bird = Image.open(IMG / "bird-hero.png").convert("RGB").crop((430, 200, 1290, 720))
        a2 = fig.add_axes([0.615, 0.0, 0.385, 0.9])
        a2.imshow(bird)
        a2.set_axis_off()
        a2.set_title("Osprey Recon: the scout, out ahead (rendered)", loc="left", fontsize=11, color=t["ink"])
        _save(fig, "hero", theme)


def main():
    for theme in THEMES:
        fig_hero(theme)
        fig_recon_jobs(theme)
        fig_recon_matrix(theme)
        fig_recon_wings(theme)
        fig_recon_tracks(theme)
        fig_nest_layout(theme)
        fig_pod(theme)
        fig_rig_compare(theme)
        fig_budgets(theme)
        fig_synthetic(theme)


if __name__ == "__main__":
    main()
