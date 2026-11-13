"""Figures for the reports (matplotlib, headless)."""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from osprey import calcs, occlusion, optics  # noqa: E402
from osprey.rig import Station, stations  # noqa: E402

PALETTE = ["#2a6fdb", "#e0782b", "#2e9e5b", "#b23a8f", "#8c6d1f", "#4a9fb5", "#c94040"]


def motion(mot, heel_deg: float, path: Path, seconds: float = 60.0):
    n = int(seconds / mot.dt)
    t = mot.t[:n]
    fig, ax = plt.subplots(2, 1, figsize=(9, 5), sharex=True)
    ax[0].plot(t, np.degrees(mot.roll[:n]) - heel_deg, label="roll about heel")
    ax[0].plot(t, np.degrees(mot.pitch[:n]), label="pitch")
    ax[0].set_ylabel("deg")
    ax[0].legend(loc="upper right", frameon=False)
    ax[1].plot(t, mot.heave[:n], color=PALETTE[2])
    ax[1].set_ylabel("heave, m")
    ax[1].set_xlabel("time, s")
    fig.suptitle("Boat motion (first minute)")
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def coverage(p, path: Path):
    sts = [s for s in stations(p) if "exterior" in s.zones]
    occ = occlusion.build(p)
    cov, mask = calcs.coverage(p, sts, occ)
    az = np.radians(np.arange(0, 360, 1.0))
    fig = plt.figure(figsize=(6, 6))
    ax = fig.add_subplot(projection="polar")
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(1)  # body azimuth is CCW (port +); port shows on the left
    for i, s in enumerate(sts):
        r = np.where(mask[i], 1 + i, np.nan)
        ax.plot(az, r, lw=6, color=PALETTE[i % len(PALETTE)], label=f"{s.id} ({s.pos[2]:.1f} m)", solid_capstyle="butt")
    ax.plot(az, np.where(mask.any(0), len(sts) + 1.2, np.nan), lw=3, color="k", label=f"any ({cov:.0%})")
    ax.set_rticks([])
    ax.set_xticks(np.radians([0, 90, 180, 270]), ["bow", "port", "stern", "starboard"])
    ax.legend(loc="lower left", bbox_to_anchor=(-0.15, -0.15), frameon=False, fontsize=8, ncol=2)
    ax.set_title(f"Horizon each camera sees past mast and sails\n{p.scenario.sail}, heel {p.scenario.heel_deg:g} deg",
                 fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def reach(p, path: Path):
    """Detection range against eye height, per target class: the height advantage."""
    top = max((s for s in stations(p) if "exterior" in s.zones), key=lambda s: s.pos[2])
    hs = np.array([2.5, 5, 8, 11, 14, 18.9, 25])
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for i, cls in enumerate(["person_in_water", "lobster_buoy", "kayak", "sailboat_30ft", "ship"]):
        kind = getattr(p.target_class, cls)
        d = [calcs.detection_reach(top, kind, p, h_eye=h)[0] for h in hs]
        ax.plot(hs, np.array(d) / 1000, "o-", color=PALETTE[i], label=cls.replace("_", " "))
    ax.plot(hs, [optics.horizon_m(h, p.atmosphere.k_refraction) / 1000 for h in hs], "k--", lw=1, label="horizon")
    ax.set_yscale("log")
    ax.set_xlabel("eye height above water, m")
    ax.set_ylabel("detection range, km")
    ax.set_title(f"Detection reach with the {top.cam_key} at {top.f_max:.0f} mm, {p.sea.state} "
                 f"(Hs {p.sea.hs_m} m), visibility {p.scenario.visibility_km:g} km", fontsize=10)
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def gantt(out: dict, path: Path, title: str):
    ids = out["stations"]
    tasks = list(out["tasks"])
    colors = {tid: PALETTE[i % len(PALETTE)] for i, tid in enumerate(tasks)}
    t = out["t"]
    dt = t[1] - t[0]
    fig, ax = plt.subplots(figsize=(10, 0.6 * len(ids) + 1.6))
    for row, sid in enumerate(ids):
        seq = out["state"][sid]
        start = 0
        for i in range(1, len(seq) + 1):
            if i == len(seq) or seq[i] != seq[start]:
                job = seq[start]
                if job == "watch":
                    c, h = "#d9d9d9", None
                elif job.startswith("slew:"):
                    c, h = colors[job[5:]], "////"
                else:
                    c, h = colors[job], None
                ax.barh(row, (i - start) * dt, left=t[start], color=c, hatch=h, edgecolor="white" if h else c,
                        height=0.7, linewidth=0)
                start = i
    ax.set_yticks(range(len(ids)), ids)
    ax.invert_yaxis()
    ax.set_xlabel("time, s")
    handles = [plt.Rectangle((0, 0), 1, 1, color=colors[t_]) for t_ in tasks] + \
              [plt.Rectangle((0, 0), 1, 1, color="#d9d9d9"),
               plt.Rectangle((0, 0), 1, 1, facecolor="white", edgecolor="k", hatch="////")]
    ax.legend(handles, tasks + ["watch (reserve)", "slewing"], loc="upper center", bbox_to_anchor=(0.5, -0.25),
              ncol=len(tasks) + 2, frameon=False, fontsize=8)
    ax.set_title(title, fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def docking(p, path: Path):
    sts = [s for s in stations(p) if "exterior" in s.zones]
    dk = calcs.docking(p, sts)
    occ = occlusion.build(p, sail="down")
    b = p.boat
    fig, ax = plt.subplots(figsize=(6, 8))
    sc = ax.scatter(-dk["pts"][:, 1], dk["pts"][:, 0], c=np.minimum(dk["count"], 4), cmap="viridis", vmin=0, vmax=4,
                    s=14, marker="s")
    xs = np.linspace(b.stern_x_m, b.bow_x_m, 200)
    hw = occ.half_beam(xs)
    ax.plot(np.r_[hw, -hw[::-1], hw[:1]], np.r_[xs, xs[::-1], xs[:1]], "k-", lw=1.5)
    for s in sts:
        ax.plot(-s.pos[1], s.pos[0], "r^")
        ax.annotate(s.id, (-s.pos[1], s.pos[0]), fontsize=7, xytext=(3, 3), textcoords="offset points")
    fig.colorbar(sc, ax=ax, label="cameras seeing the water point", shrink=0.6)
    ax.set_aspect("equal")
    ax.set_xlabel("starboard +, m")
    ax.set_ylabel("forward, m")
    ax.set_title("Docking look-down coverage", fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def beet(res: dict, path: Path):
    """The Beet: the Beet-4 hybrid's righting curves for each cabin shape and keel pod, and where the Beet-4's
    weight goes for each way of powering it."""
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(15, 5.6), gridspec_kw={"width_ratios": [1.25, 1]})
    ax.axhline(0, color="#444444", lw=0.8)
    ax.axhspan(-150, 0, color="#d62728", alpha=0.05)
    rows = [r for r in res["sweeps"] if "keel_pod_m" in r["over"]]
    for r in rows:
        top, pod = r["over"]["cabin_top_ratio"], r["over"]["keel_pod_m"]
        col = {1.0: PALETTE[0], 0.55: PALETTE[1], 0.35: PALETTE[2]}.get(top, PALETTE[3])
        ls = {0.0: "-", 0.5: "--", 1.0: ":"}.get(pod, "-.")
        shape = "cylinder" if top == 1.0 else f"cone, roof {top:g} of floor"
        ax.plot(r["phi_deg"], np.array(r["gz_m"]) * 100, color=col, ls=ls, lw=2,
                label=f"{shape}, keel pod {pod:g} m")
    ax.set_xlim(0, 180)
    ax.set_xticks(range(0, 181, 30))
    ax.set_xlabel("knocked over from upright (°)")
    ax.set_ylabel("righting arm GZ (cm)")
    ax.text(178, 4, "above 0 it comes back upright", ha="right", va="bottom", fontsize=8.5, color="#333")
    ax.text(178, -145, "below 0 it goes on over and floats upside down", ha="right", va="bottom", fontsize=8.5, color="#a33")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8, frameon=False, loc="lower left")
    ax.set_title("Beet-4 hybrid: does it come back?")
    b4 = [r for r in res["cases"] if r["case"] == "beet-4" and r["ok"]]
    parts = list(b4[0]["parts"])
    bottom = np.zeros(len(b4))
    cols = plt.get_cmap("tab20").colors
    for k, part in enumerate(parts):
        vals = np.array([r["parts"][part] for r in b4])
        bx.bar(range(len(b4)), vals, bottom=bottom, color=cols[k % len(cols)], label=part, width=0.6)
        bottom += vals
    for i, r in enumerate(b4):
        bx.text(i, bottom[i] + 20, f"{r['mass_kg']:.0f} kg", ha="center", fontsize=9)
    bx.set_xticks(range(len(b4)), [r["power"] for r in b4])
    bx.set_ylabel("kg")
    bx.set_title("Beet-4: where the weight goes")
    bx.legend(fontsize=7.5, frameon=False, bbox_to_anchor=(1.0, 1.0), loc="upper left")
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


TRIDENT_COLORS = {"sketch": "#8C8C8C", "balanced": "#4C72B0", "found": "#DD8452"}
TRIDENT_GROUPS = {"payload": ("person", "mission load", "cargo"), "crew kit": ("container", "seat", "hatch", "safety"),
                  "core": ("core walls", "core frame", "flotation", "nose", "bay"), "battery": ("battery",),
                  "modules": ("motors", "props", "pods", "wings", "tail", "legs", "float-feet"), "avionics": ("avionics",)}


def trident(res: dict, path: Path):
    """The Trident: each layout's righting curve (the worst way round), the three afloat side by side from the side,
    and where the found layout's weight goes, crewed and as cargo."""
    from osprey import trident as tr

    li = tr.inputs()
    fig = plt.figure(figsize=(16, 10.5))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.6, 1.0], height_ratios=[1.0, 0.85])
    ax = fig.add_subplot(gs[0, 0])
    ax.axhline(0, color="#444444", lw=0.8)
    ax.axhspan(-80, 0, color="#d62728", alpha=0.05)
    for r in res["layouts"]:
        col = TRIDENT_COLORS[r["layout_name"]]
        for p, arms in r["gz_m"].items():
            worst = float(p) == r["worst_fall_deg"]
            ax.plot(r["phi_deg"], np.array(arms) * 100, color=col, lw=2.2 if worst else 0.7, alpha=1 if worst else 0.45,
                    label=f"{li['layouts'][r['layout_name']]['label'].split(':')[0]}, {r['mass_kg']:.0f} kg" if worst else None)
    ax.set_xlim(0, 180)
    ax.set_ylim(-80, 160)
    ax.set_xticks(range(0, 181, 30))
    ax.grid(alpha=0.3)
    ax.set_xlabel("knocked over from upright (°)")
    ax.set_ylabel("righting arm GZ (cm)")
    ax.text(178, -76, "below 0 it falls further over", ha="right", fontsize=8.5, color="#a33")
    ax.text(178, 155, "above 0 it comes back upright", ha="right", va="top", fontsize=8.5, color="#333")
    ax.legend(loc="upper left", bbox_to_anchor=(0, 0.93), fontsize=8.5, frameon=False)
    ax.set_title("Righting: the worst way round bold,\nthe other directions faint", fontsize=10)
    # The three afloat, from the side: one module in the plane of the page (right), the other two behind it (left).
    bx = fig.add_subplot(gs[1, :])
    bx.axhspan(-1.4, 0, color="#4C72B0", alpha=0.10)
    bx.axhline(0, color="#4C72B0", lw=1.0)
    for i, r in enumerate(res["layouts"]):
        c = tr.params(r["layout_name"])
        c["z_prop"] = r["layout"]["z_prop"]
        lay = tr.layout(c)
        x0, w = i * 12.5, r["waterline_m"]
        col = TRIDENT_COLORS[r["layout_name"]]
        pts = np.array(tr.outline(c))
        bx.fill(np.r_[x0 + pts[:, 0], x0 - pts[::-1, 0]], np.r_[pts[:, 1], pts[::-1, 1]] - w, color=col, alpha=0.85, lw=0)
        ch, d, zp = c["wing_chord_m"], c["prop_d_m"], lay["z_prop"]
        for sgn, k, alpha in ((1, 1.0, 1.0), (-1, 0.5, 0.45)):      # in the page; the two behind, foreshortened
            r0, r1, arm = lay["r_core"] * k, lay["r_tip"] * k, lay["arm"] * k
            bx.add_patch(plt.Rectangle((x0 + sgn * r0 if sgn > 0 else x0 - r1, lay["z_wing_le"] - ch - w), r1 - r0, ch,
                                       color="#555555", alpha=0.8 * alpha, lw=0))
            bx.plot([x0 + sgn * (arm - d / 2 * k), x0 + sgn * (arm + d / 2 * k)], [zp - w] * 2, color="#222222", lw=1.6,
                    alpha=alpha)
            foot_b = c["foot_bottom_m"]
            bx.plot([x0 + sgn * arm] * 2, [zp - 0.3 - w, foot_b - w], color="#333333", lw=1.2, alpha=alpha)
            if c["foot_r_m"]:
                bx.add_patch(plt.Rectangle((x0 + sgn * arm - c["foot_r_m"], foot_b - w), 2 * c["foot_r_m"], c["foot_l_m"],
                                           color="#2e9e5b", alpha=0.85 * alpha, lw=0))
        bx.add_patch(plt.Rectangle((x0 - 0.3, c["bay_m"] * 0.2 - w), 0.6, c["bay_m"] * 0.6, color="#222222", alpha=0.6))
        bx.plot([x0], [r["zg_m"] - w], marker="o", ms=7, mfc="white", mec="#222222")
        bx.text(x0, lay["z_nose"] - w + 0.25, f"{li['layouts'][r['layout_name']]['label'].split(':')[0]}\n"
                f"margin {r['static_margin']:+.2f}, GM {r['gm_m']:.1f} m", ha="center", fontsize=9)
    bx.text(-5.6, -0.12, "water", color="#4C72B0", fontsize=9, va="top")
    bx.set_aspect("equal")
    bx.set_xlim(-6.0, 31.0)
    bx.set_ylim(-1.4, 5.6)
    bx.set_yticks(range(-1, 6))
    bx.set_xticks([])
    bx.set_ylabel("height above the water (m)")
    bx.set_title("Afloat, from the side: the battery (black), the CG (o), the wing (grey) and props (black lines);\n"
                 "one module in the page (right), the other two behind it (left, faint); float-feet green", fontsize=10)
    cx = fig.add_subplot(gs[0, 1])
    found = next(r for r in res["layouts"] if r["layout_name"] == "found")
    cases = [("crewed", found), ("cargo", res["cargo"])]
    bottom = np.zeros(2)
    for k, (grp, names) in enumerate(TRIDENT_GROUPS.items()):
        vals = np.array([sum(r["parts"].get(n, 0.0) for n in names) for _, r in cases])
        cx.bar(range(2), vals, bottom=bottom, color=PALETTE[k], label=grp, width=0.6)
        for i, v in enumerate(vals):
            if v > 40:
                cx.text(i, bottom[i] + v / 2, f"{v:.0f}", ha="center", va="center", fontsize=8.5, color="white")
        bottom += vals
    for i, (_, r) in enumerate(cases):
        cx.text(i, bottom[i] + 12, f"{r['mass_kg']:.0f} kg", ha="center", fontsize=9)
    cx.set_xticks(range(2), [n for n, _ in cases])
    cx.set_ylim(0, bottom.max() * 1.12)
    cx.set_ylabel("kg")
    cx.legend(fontsize=8, frameon=False, loc="lower right")
    cx.set_title("Found layout: where the weight goes", fontsize=10)
    fig.suptitle("The Trident: three modules round a core, a tailsitter that floats on its wings", fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(path, dpi=130)
    plt.close(fig)


TRIDENT_SIM_COLORS = {"found": "#DD8452", "found+sandwich": "#2e9e5b", "balanced": "#4C72B0"}


def trident_sim(res: dict, path: Path):
    """The Trident in MuJoCo, afloat: the tilt after being let go at each angle in calm water, one panel per craft;
    and in regular waves, the most it tilts and how close the props come to the water, by wave height."""
    from osprey import trident_sim as ts

    crafts = list(dict.fromkeys(r["craft"] for r in res["drops"]))
    fig = plt.figure(figsize=(15, 10))
    gs = fig.add_gridspec(2, 6)
    starts = sorted({r["phi_deg"] for r in res["drops"]})
    shades = plt.cm.Blues(np.linspace(0.35, 0.95, len(starts)))
    for j, cname in enumerate(crafts):
        ax = fig.add_subplot(gs[0, 2 * j:2 * j + 2])
        for r in (r for r in res["drops"] if r["craft"] == cname):
            col = shades[starts.index(r["phi_deg"])]
            ax.plot(r["t_s"], r["tilt_deg"], color=col, lw=1.6, ls="-" if r["psi_deg"] == 0 else "--",
                    label=f"{r['phi_deg']:.0f}°" if r["psi_deg"] == 0 else None)
        ax.axhspan(0, res["sim"]["upright_deg"], color="#2e9e5b", alpha=0.08, lw=0)
        ax.set_xlim(0, 12)
        ax.set_ylim(0, 185)
        ax.set_yticks(range(0, 181, 30))
        ax.grid(alpha=0.3)
        ax.set_xlabel("time after letting go (s)")
        if j == 0:
            ax.set_ylabel("tilt off upright (°)")
        ax.set_title(f"{ts._label(cname)}: let go in calm water", fontsize=10)
        if j == len(crafts) - 1:
            ax.legend(title="let go at (solid toward a module,\ndashed between two)", fontsize=8, title_fontsize=8,
                      frameon=False, loc="upper right", ncol=2)
    wcrafts = list(dict.fromkeys(r["craft"] for r in res["waves"]))
    steeps = sorted({r["steepness"] for r in res["waves"]})
    styles = ["-", "--", ":"]
    bx, cx = fig.add_subplot(gs[1, :3]), fig.add_subplot(gs[1, 3:])
    for cname in wcrafts:
        for k, s in enumerate(steeps):
            rows = [r for r in res["waves"] if r["craft"] == cname and r["steepness"] == s]
            hs = sorted({r["height_m"] for r in rows})
            worst_tilt = [max(r["tilt_max_deg"] for r in rows if r["height_m"] == h) for h in hs]
            worst_props = [min(r["props_min_m"] for r in rows if r["height_m"] == h) for h in hs]
            lab = f"{ts._label(cname)}, steepness 1/{1 / s:.0f}"
            bx.plot(hs, worst_tilt, color=TRIDENT_SIM_COLORS.get(cname, "#555555"), ls=styles[k % 3], marker="o",
                    ms=5, lw=2, label=lab)
            cx.plot(hs, worst_props, color=TRIDENT_SIM_COLORS.get(cname, "#555555"), ls=styles[k % 3], marker="o",
                    ms=5, lw=2, label=lab)
    bx.set_xlabel("wave height (m)")
    bx.set_ylabel("most tilt (°), the worse heading")
    bx.grid(alpha=0.3)
    bx.set_title("Regular waves: the most it tilts", fontsize=10)
    cx.axhline(0, color="#c94040", lw=1)
    cx.text(0.5, 0.05, "props in the water below this line", color="#c94040", fontsize=8)
    cx.set_xlabel("wave height (m)")
    cx.set_ylabel("lowest prop rim above the water (m)")
    cx.grid(alpha=0.3)
    cx.set_title("Regular waves: how close the props come to the water", fontsize=10)
    cx.legend(fontsize=8, frameon=False, loc="lower right")
    fig.suptitle("The Trident in MuJoCo, afloat: let go at an angle, and riding waves (props stopped)", fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(path, dpi=130)
    plt.close(fig)
