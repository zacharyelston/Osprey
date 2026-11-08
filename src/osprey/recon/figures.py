"""Recon figures: the sized airframe, the mission's ground track over the
task area, the flight timeline, and the capability matrix."""

from __future__ import annotations

import math

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

PHASE_COLORS = {"outbound": "#4C72B0", "task": "#DD8452", "return": "#55A868"}


def planform(p, d: dict, path):
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(11, 4.2), gridspec_kw={"width_ratios": [2.4, 1]})
    y = np.array(d["half_span_y_m"])
    c = np.array(d["chords_m"])
    fo = p.wing.fem_origin
    for s in (-1, 1):
        le = -fo * c
        ax.fill(np.r_[s * y, s * y[::-1]], np.r_[le, (le + c)[::-1]], color="#cfd8e3", ec="#34495e", lw=1.2)
        ax.plot(s * y, np.zeros_like(y), color="#c0392b", lw=2)
    bed = p.print.bed_m[2]
    for k in range(1, int(math.ceil(d["span_m"] / 2 / bed))):
        for s in (-1, 1):
            ax.axvline(s * k * bed, color="#7f8c8d", ls=":", lw=1)
    ax.set_aspect("equal")
    cm = float(c.max())
    ax.set_ylim(1.4 * cm, -0.6 * cm)
    ax.set_xlabel("span (m)")
    ax.set_ylabel("chord (m)")
    ax.set_title(f"{p.mission.name}: span {d['span_m']:.2f} m, AR {d['aspect_ratio']:.1f}, "
                 f"{d['print_panels']} printed panels (dotted), carbon spar (red)", fontsize=10)
    parts = {"fixed (body, avionics, gimbal, motor)": d["fixed_kg"], "battery": d["battery_kg"],
             "printed shell": d["skin_kg"], "carbon spar": d["spar_kg"]}
    bottom = 0.0
    for (name, kg), col in zip(parts.items(), ["#95a5a6", "#f1c40f", "#3498db", "#c0392b"]):
        bx.bar(0, kg, bottom=bottom, color=col, width=0.6, label=f"{name}: {kg:.2f} kg")
        bottom += kg
    bx.set_xlim(-0.6, 1.8)
    bx.set_xticks([])
    bx.set_ylabel("kg")
    bx.set_title(f"take-off mass {d['mass_total_kg']:.2f} kg", fontsize=10)
    bx.legend(fontsize=8, loc="upper right", frameon=False)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def track(p, r: dict, path):
    fig, ax = plt.subplots(figsize=(8, 8))
    task = r["task"]
    t_end = r["t"][-1]
    if hasattr(task, "grid"):
        g = task.grid
        off = g.datum + g.drift * t_end
        if task.kind == "search":
            shade, note = g.remaining(), "shading: where the person still is, if not found (end of flight)"
        else:
            shade, note = g.prior * (1 - g.unfound), "shading: the area imaged"
        ax.pcolormesh(g.x + off[0], g.y + off[1], shade, cmap="Purples", shading="auto", alpha=0.85,
                      vmin=0, vmax=shade.max())
    else:
        note = "the vessel's track, and the orbits round it"
    ph = r["phase"]
    for name, col in PHASE_COLORS.items():
        sel = ph == name
        if sel.any():
            ax.plot(np.where(sel, r["x"], np.nan), np.where(sel, r["y"], np.nan), color=col, lw=1.2, label=name)
    ax.plot(r["boat_x"], r["boat_y"], color="k", lw=2, label="boat")
    ax.plot(*r["boat_x"][:1], *r["boat_y"][:1], "k^", ms=8)
    if task.kind != "survey":
        d = np.array([task.where(tt) for tt in r["t"]])
        ax.plot(d[:, 0], d[:, 1], color="#8e44ad", lw=1, ls="--",
                label="datum, drifting" if task.kind == "search" else "vessel")
    w = r["wind"]
    ax.annotate("", xy=(0.12, 0.9), xytext=(0.12 - w[0] / 40, 0.9 - w[1] / 40), xycoords="axes fraction",
                arrowprops=dict(arrowstyle="->", lw=2, color="#2c3e50"))
    ax.text(0.12, 0.94, f"wind {np.linalg.norm(w) / 0.5144:.0f} kn", transform=ax.transAxes, ha="center")
    ax.set_aspect("equal")
    ax.set_xlabel("east (m)")
    ax.set_ylabel("north (m)")
    ax.legend(loc="lower right", fontsize=8)
    ax.set_title(f"{p.mission.label}\n{note}", fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def timeline(p, ac, r: dict, path):
    fig, axs = plt.subplots(4, 1, figsize=(10, 7.5), sharex=True)
    t = r["t"] / 60
    series = [("altitude (m)", r["h"]), ("electric power (W)", r["power"]),
              ("battery left (%)", 100 * r["energy"] / ac.energy_j),
              (f"{r['task'].progress_label} (%)", 100 * r["progress"])]
    for ax, (lab, y) in zip(axs, series):
        ax.plot(t, y, color="#2c3e50", lw=1)
        ax.set_ylabel(lab, fontsize=9)
        for name, col in PHASE_COLORS.items():
            sel = r["phase"] == name
            if sel.any():
                ax.axvspan(t[sel][0], t[sel][-1], color=col, alpha=0.12, lw=0)
    axs[3].axhline(100 * r["task"].goal, color="#c0392b", ls=":", lw=1)
    axs[-1].set_xlabel("minutes since launch")
    axs[0].set_title(f"{p.mission.name}: outbound (blue), {r['task'].kind} (orange), return (green)", fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def matrix(M: dict, designs: dict, missions: list[str], order: list[str], best: str | None, path):
    """Every airframe through every mission: green when it gets home with the
    goal met (shade: battery left), red when it doesn't."""
    from osprey.recon.fleet import ok

    fig, ax = plt.subplots(figsize=(1.6 * len(missions) + 3.2, 0.62 * len(order) + 1.6))
    for i, dn in enumerate(order):
        for j, mn in enumerate(missions):
            s = M[dn][mn]
            good = ok(s)
            col = plt.cm.Greens(0.35 + 0.6 * s["energy_left_frac"]) if good else "#e8a3a3"
            ax.add_patch(plt.Rectangle((j, i), 0.96, 0.9, color=col))
            txt = f"{s['energy_left_frac']:.0%} left" if good else f"{s['progress']:.0%}\n{s['progress_label']}"
            ax.text(j + 0.48, i + 0.45, txt, ha="center", va="center", fontsize=8)
    ax.set_xlim(0, len(missions))
    ax.set_ylim(len(order), 0)
    ax.set_xticks(np.arange(len(missions)) + 0.48, missions, rotation=20, ha="right", fontsize=8)
    ax.set_yticks(np.arange(len(order)) + 0.45,
                  [f"{dn}: {designs[dn]['mass_total_kg']:.2f} kg" + ("  ★" if dn == best else "") for dn in order],
                  fontsize=8)
    ax.set_xlabel("mission flown")
    ax.set_ylabel("airframe sized for")
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.tick_params(length=0)
    ax.set_title("One bird, many jobs (★: lightest airframe that does every mission)", fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def cyclone(a: dict, title: str, path):
    """The Cyclone: hover power against the tailsitter's, cruise power against airspeed, and its two shapes."""
    g, h, ts, cv = a["geometry"], a["hover"], a["tailsitter"], a["curves"]
    fig, (ax, bx, cx) = plt.subplots(1, 3, figsize=(15, 4.4), gridspec_kw={"width_ratios": [1, 1.4, 1.6]})
    bars = [("tailsitter\n(two props)", ts["hover_w"], "#95a5a6"), ("Cyclone, tricopter\n(sea lift-off only)", a["liftoff_w"], "#DD8452"),
            ("Cyclone\nspinning", h["p_shaft_w"], "#4C72B0")]
    ax.bar([b[0] for b in bars], [b[1] for b in bars], color=[b[2] for b in bars])
    for i, (_, w, _) in enumerate(bars):
        ax.text(i, w, f"{w:.0f} W", ha="center", va="bottom", fontsize=9)
    ax.set_ylabel("hover shaft power (W)")
    ax.set_title("Hovering", fontsize=10)
    v = cv["v"]
    for key, label, col in (("base", "twin-boom one-bird", "#95a5a6"), ("wing", "Cyclone in flight mode", "#4C72B0")):
        bx.plot(v, cv[key], color=col, lw=2, label=label)
    bx.axvline(cv["base_v_search"], color="#95a5a6", ls=":", lw=1)
    bx.axvline(cv["v_search"], color="#4C72B0", ls=":", lw=1)
    bx.set_xlabel("airspeed (m/s)")
    bx.set_ylabel("electric power (W)")
    bx.set_ylim(0, 450)
    bx.legend(fontsize=8, frameon=False)
    bx.set_title("Cruising (search speeds dotted)", fontsize=10)
    R, r0, c = g["R_m"], g["r0_m"], g["chord_m"] * a["resized"]["chord_scale"]
    dih = a["cyclone"]["dihedral_deg"]
    off = 2.5 * R
    # Spinning, from above: three blades in the disc, the tip motors pushing round.
    cx.add_patch(plt.Circle((0, 0), R, fill=False, ls="--", color="#7f8c8d"))
    for ang in (90, 210, 330):
        t_ = math.radians(ang)
        u, n = np.array([math.cos(t_), math.sin(t_)]), np.array([-math.sin(t_), math.cos(t_)])
        quad = np.array([r0 * u - c / 2 * n, R * u - c / 2 * n, R * u + c / 2 * n, r0 * u + c / 2 * n])
        cx.fill(quad[:, 0], quad[:, 1], color="#cfd8e3", ec="#34495e", lw=1.2)
        cx.plot(*(R * u + c / 2 * n), "o", color="#c0392b", ms=6)
    cx.add_patch(plt.Circle((0, 0), r0, color="#e67e22"))
    cx.annotate("", xy=(0.7 * R * math.cos(2.2), 0.7 * R * math.sin(2.2)), xytext=(0.7 * R * math.cos(1.4), 0.7 * R * math.sin(1.4)),
                arrowprops=dict(arrowstyle="->", color="#4C72B0", connectionstyle="arc3,rad=0.3"))
    cx.text(0, -1.25 * R, "spinning, from above", ha="center", fontsize=8)
    # Flying, from the front: two arms up at the dihedral, the fin down, the tip props facing us.
    for ang in (dih, 180 - dih, 270):
        t_ = math.radians(ang)
        cx.plot([off + r0 * math.cos(t_), off + R * math.cos(t_)], [r0 * math.sin(t_), R * math.sin(t_)],
                color="#34495e", lw=3, solid_capstyle="round")
        cx.add_patch(plt.Circle((off + R * math.cos(t_), R * math.sin(t_)), 0.12 * R, fill=False, color="#c0392b", lw=1.5))
    cx.add_patch(plt.Circle((off, 0), r0, color="#e67e22"))
    cx.text(off, -1.25 * R, f"flying, from the front: {dih:g}° dihedral, fin down", ha="center", fontsize=8)
    cx.set_aspect("equal")
    cx.set_xlim(-1.2 * R, off + 1.2 * R)
    cx.set_ylim(-1.4 * R, 1.15 * R)
    cx.set_axis_off()
    cx.set_title(f"{2 * R:.2f} m rotor, three {g['arm_m']:.2f} m arms, tip motors", fontsize=10)
    fig.suptitle(title, fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


MODE_COLORS = {1: "#DD8452", 2: "#4C72B0", 3: "#55A868", 4: "#8172B2"}


def cyclone_modes(a: dict, title: str, path):
    """The Cyclone's modes: the moves between them, and the launch and recovery mode by mode."""
    from osprey.recon.cyclone_modes import NAMES

    r = a["A+A2" if a["modes"]["a2"] else "A"]
    fig = plt.figure(figsize=(15, 4.8))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.5, 1.2, 1.2])
    ax = fig.add_subplot(gs[0])
    pos = {1: (0, 0), 2: (0, 1), 3: (1.6, 1), 4: (1.6, 0)}
    for k, (x, y) in pos.items():
        ax.add_patch(plt.Rectangle((x - 0.42, y - 0.14), 0.84, 0.28, color=MODE_COLORS[k], alpha=0.85, ec="none"))
        ax.text(x, y + 0.04, f"{k}", ha="center", va="center", fontsize=14, color="white", weight="bold")
        ax.text(x, y - 0.07, NAMES[k], ha="center", va="center", fontsize=7, color="white")
    # Each move's arrow on its own side of the pair's centre line, its label beside it.
    for row in r["matrix"]:
        a_, b_ = row["from"], row["to"]
        (x0, y0), (x1, y1) = pos[a_], pos[b_]
        lo, hi = sorted((a_, b_))
        px, py = pos[hi][0] - pos[lo][0], pos[hi][1] - pos[lo][1]
        n = math.hypot(px, py)
        sgn = 1 if a_ < b_ else -1
        ox, oy = -py / n * 0.07 * sgn, px / n * 0.07 * sgn
        dx, dy = (x1 - x0) / n, (y1 - y0) / n
        sx, sy = x0 + dx * 0.46 + ox, y0 + dy * 0.18 + oy
        ex, ey = x1 - dx * 0.46 + ox, y1 - dy * 0.18 + oy
        col = "#34495e" if row["ok"] else "#c0392b"
        ax.annotate("", xy=(ex, ey), xytext=(sx, sy),
                    arrowprops=dict(arrowstyle="->", lw=1.4, color=col, ls="-" if row["ok"] else "--"))
        sep = "\n" if not px else ": "
        label = f"{a_}→{b_}{sep}{row['t_s']:.0f} s, {row['dh_m']:+.0f} m" if row["ok"] else f"{a_}→{b_}{sep}refused"
        lx, ly = (sx + ex) / 2 + ox * 1.3, (sy + ey) / 2 + oy * 1.3
        ha = "center" if px else ("left" if ox > 0 else "right")
        ax.text(lx, ly, label, fontsize=7, ha=ha, va="center", color=col)
    ax.set_xlim(-0.85, 2.45)
    ax.set_ylim(-0.4, 1.4)
    ax.set_aspect("equal")
    ax.set_axis_off()
    ax.set_title("The modes and the moves between them", fontsize=10)
    for i, (key, name) in enumerate((("launch", "Launch"), ("recover", "Recovery"))):
        bx = fig.add_subplot(gs[1 + i])
        for ph in r[key]["phases"]:
            t0, t1 = ph["t0_s"], ph["t0_s"] + ph["dt_s"]
            bx.plot([t0, t1], [ph["h0_m"], ph["h1_m"]], color=MODE_COLORS[ph["mode"]], lw=3, solid_capstyle="butt")
        bx.axhline(a["modes"]["clearance_m"], color="#7f8c8d", ls=":", lw=1)
        bx.text(0.2, a["modes"]["clearance_m"] + 0.4, "25 ft", fontsize=7, color="#7f8c8d")
        bx.set_xlabel("time (s)")
        bx.set_ylabel("height (m)")
        bx.set_title(f"{name}: {r[key]['time_s']:.0f} s, {r[key]['energy_wh']:.1f} Wh", fontsize=10)
        bx.set_ylim(bottom=0)
        bx.grid(alpha=0.3)
    handles = [plt.Line2D([], [], color=MODE_COLORS[k], lw=3, label=f"mode {k}") for k in (1, 2, 3, 4)]
    fig.legend(handles=handles, loc="lower center", ncol=4, frameon=False, fontsize=8)
    fig.suptitle(title, fontsize=11)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(path, dpi=130)
    plt.close(fig)
