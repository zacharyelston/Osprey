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


def cyclone_spin(a: dict, title: str, path):
    """The spin building (1->2) and dying (2->1): the spin, B's twist, the arms' share of the weight and A
    of its burst, against time."""
    fig, axs = plt.subplots(2, 2, figsize=(12, 6.2), sharex="col")
    for col, key, name in ((0, "build", "1 → 2: the spin builds"), (1, "die", "2 → 1: the spin dies")):
        tr = np.array(a["spin"][key]["track"])
        t = tr[:, 0]
        ax, bx = axs[0, col], axs[1, col]
        ax.plot(t, tr[:, 1], color=MODE_COLORS[2], lw=2, label="spin / hover's")
        ax.set_ylabel("spin / hover's")
        ax.set_ylim(-0.05, 1.25)
        ax2 = ax.twinx()
        ax2.plot(t, tr[:, 2], color="#444444", lw=1.6, ls="--", label="B's twist off centre")
        ax2.set_ylabel("B off centre (°)")
        ax2.set_ylim(-25, 95)
        ax.set_title(f"{name}: {a['spin'][key]['t_s']:.2f} s, {a['spin'][key]['energy_j'] / 3600:.2f} Wh", fontsize=10)
        bx.plot(t, tr[:, 4], color=MODE_COLORS[3], lw=2, label="the arms' thrust / weight")
        bx.plot(t, tr[:, 5], color=MODE_COLORS[1], lw=2, label="A, of its burst")
        bx.set_ylim(-0.1, 1.7)
        bx.set_xlabel("time (s)")
        bx.grid(alpha=0.3)
        ax.grid(alpha=0.3)
        if col == 0:
            h1, l1 = ax.get_legend_handles_labels()
            h2, l2 = ax2.get_legend_handles_labels()
            ax.legend(h1 + h2, l1 + l2, fontsize=8, loc="center right")
            bx.legend(fontsize=8, loc="center right")
    fig.suptitle(title, fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def cyclone_wind(a: dict, title: str, path):
    """The wind: mode 1's lean and A against it, mode 2's retreating arm and cyclic against their limits, and
    what spinning faster buys."""
    w = a["wind"]
    fig, (ax, bx, cx) = plt.subplots(1, 3, figsize=(15, 4.4))
    v = [r["v_ms"] for r in w["one"]]
    ax.plot(v, [r["lean_deg"] for r in w["one"]], color=MODE_COLORS[1], lw=2, label="lean into the wind (°)")
    ax2 = ax.twinx()
    ax2.plot(v, [100 * r["a_frac"] for r in w["one"]], color="#444444", lw=1.6, ls="--", label="A, % of its burst")
    ax2.axhline(100, color="#444444", lw=0.8)
    ax2.set_ylim(0, 140)
    ax2.set_ylabel("A, % of its burst")
    ax.axvline(w["one_max_ms"], color=MODE_COLORS[1], lw=1, ls=":")
    for k, sv in a["sea_winds"]:
        ax.text(sv, 0.97, k, transform=ax.get_xaxis_transform(), ha="center", va="top", fontsize=7, color="#666666")
    ax.set_xlabel("wind (m/s)")
    ax.set_ylabel("lean (°)")
    ax.set_title(f"Mode 1, three arms standing in the wind: holds to {w['one_max_ms']:.1f} m/s", fontsize=10)
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, fontsize=8, loc="center left")
    ax.grid(alpha=0.3)
    two = w["two"]
    vv = [r["v_ms"] for r in two]
    bx.plot(vv, [r["alpha_max_deg"] for r in two], color=MODE_COLORS[2], lw=2, label="retreating arm's angle of attack")
    bx.axhline(w["stall_deg"], color=MODE_COLORS[2], lw=1, ls=":", label=f"stall {w['stall_deg']:.1f}°")
    bx.plot(vv, [r["cyclic_deg"] for r in two], color=MODE_COLORS[3], lw=2, label="B's cyclic")
    bx.axhline(w["swing_deg"], color=MODE_COLORS[3], lw=1, ls=":", label=f"B's swing {w['swing_deg']:.1f}°")
    bx.set_xlim(0, max(6.0, w["two_max_ms"] + 1))
    bx.set_xlabel("wind (m/s)")
    bx.set_ylabel("degrees")
    bx.set_title(f"Mode 2, spinning: holds to {w['two_max_ms']:.2f} m/s, then {w['two_limit']}", fontsize=10)
    bx.legend(fontsize=8, loc="lower right")
    bx.grid(alpha=0.3)
    kn = a["knob"]
    cx.plot([r["hover_w"] for r in kn], [r["wind_ms"] for r in kn], "o-", color=MODE_COLORS[2], lw=2)
    for r in kn:
        fits = r["spin_peak_w"] <= a["rating_w"]
        cx.annotate(f"{r['cl_mean']:.2f}{'' if fits else ' (bigger A)'}", (r["hover_w"], r["wind_ms"]),
                    xytext=(6, -3), textcoords="offset points", fontsize=8, color="#222222" if fits else "#999999")
    lo, hi = min(r["hover_w"] for r in kn), max(r["hover_w"] for r in kn)
    cx.set_xlim(lo - 0.05 * (hi - lo), hi + 0.35 * (hi - lo))
    cx.set_xlabel("spinning hover (W shaft)")
    cx.set_ylabel("mode 2 wind limit (m/s)")
    cx.set_title("Spinning faster: the arms' mean lift coefficient", fontsize=10)
    cx.grid(alpha=0.3)
    fig.suptitle(title, fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def cyclone_control(a: dict, title: str, path):
    """What A and B do in each mode, drawn: mode 1 from above, mode 2's disc from above, mode 4 from ahead."""
    au = a["authority"]
    o, t, f = au["one"], au["two"], au["four"]["search"]
    fig, axs = plt.subplots(1, 3, figsize=(15, 5.2))
    arm = lambda ax, ang, col="#34495e", lw=6: ax.plot([0.15 * math.cos(ang), math.cos(ang)],  # noqa: E731
                                                       [0.15 * math.sin(ang), math.sin(ang)], color=col, lw=lw,
                                                       solid_capstyle="round")
    angs = [math.radians(90 + 120 * k) for k in range(3)]
    # Mode 1, from above: three A up, one more and two less tilts it; all three tilted by B yaws it.
    ax = axs[0]
    for k, g in enumerate(angs):
        arm(ax, g)
        ax.plot(math.cos(g), math.sin(g), "o", ms=16, color=MODE_COLORS[1], mec="k")
        ax.annotate("+" if k == 0 else "−", (math.cos(g), math.sin(g)), ha="center", va="center", fontsize=13,
                    fontweight="bold")
    ax.add_patch(plt.Circle((0, 0), 0.15, color="#e67e22"))
    ax.annotate("", xy=(1.25 * math.cos(math.radians(60)), 1.25 * math.sin(math.radians(60))),
                xytext=(1.25 * math.cos(math.radians(120)), 1.25 * math.sin(math.radians(120))),
                arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=-0.4", color="#444444", lw=1.5))
    ax.text(0, -1.45, f"roll, pitch: A split, {o['tilt_nm']:.1f} N m, 20° in {o['tilt20_s']:.2f} s\n"
            f"yaw: B tilts all three A {a['inputs']['b_yaw_deg']:g}°, {o['yaw_nm']:.1f} N m", ha="center", fontsize=9)
    ax.set_title("1  lift-off: a tricopter, from above", fontsize=10)
    # Mode 2, the disc from above: B's cyclic once a turn tilts it; A's PWM once a turn pushes it sideways.
    bx = axs[1]
    bx.add_patch(plt.Circle((0, 0), 1.0, color=MODE_COLORS[2], alpha=0.12))
    for g in angs:
        arm(bx, g, lw=5)
    bx.add_patch(plt.Circle((0, 0), 0.15, color="#e67e22"))
    bx.annotate("", xy=(0.35, 1.2), xytext=(0.35, 0.55), arrowprops=dict(arrowstyle="-|>", color=MODE_COLORS[3], lw=2.5))
    bx.text(0.42, 0.85, "tilt", color=MODE_COLORS[3], fontsize=9)
    bx.text(-1.15, -0.1, "push", color=MODE_COLORS[1], fontsize=9)
    bx.annotate("", xy=(-1.15, -0.2), xytext=(-0.55, -0.2), arrowprops=dict(arrowstyle="-|>", color=MODE_COLORS[1], lw=2))
    bx.annotate("", xy=(0.95, -0.55), xytext=(0.55, -0.95),
                arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0.3", color="#444444", lw=1.2))
    bx.text(0, -1.45, f"disc tilt: B's cyclic ±{t['b_swing_deg']:.1f}° at {t['rev_hz']:.1f} Hz, {t['tilt_dps']:.0f}°/s\n"
            f"sideways: A's PWM once a turn, {t['a_side_n']:.2f} N", ha="center", fontsize=9)
    bx.set_title("2  spinning: the disc from above", fontsize=10)
    # Mode 4, from ahead: two wings up at the dihedral, the fin down; A split for pitch and yaw, B rolls.
    cx = axs[2]
    dih = math.radians(a.get("dihedral_deg", 30.0))
    for g in (dih, math.pi - dih, -math.pi / 2):
        arm(cx, g, col="#8172B2")
    for g in (dih, math.pi - dih, -math.pi / 2):
        cx.plot(math.cos(g), math.sin(g), "o", ms=14, color=MODE_COLORS[1], mec="k")
    cx.add_patch(plt.Circle((0, 0), 0.15, color="#e67e22"))
    cx.annotate("", xy=(0.45, 0.75), xytext=(-0.45, 0.75),
                arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=-0.5", color=MODE_COLORS[3], lw=1.8))
    cx.text(0, -1.45, f"pitch: A, the fin's motor against the wings' ({f['fin_share']:.0%} on the fin to trim)\n"
            f"yaw: A, one wing's against the other, {f['yaw_nm']:.1f} N m\n"
            f"roll: B twists all three arms, {f['roll_dps_5deg']:.0f}°/s for 5°", ha="center", fontsize=9)
    cx.set_title("4  wing-borne: from ahead", fontsize=10)
    for x in axs:
        x.set_aspect("equal")
        x.set_xlim(-1.5, 1.5)
        x.set_ylim(-1.75, 1.4)
        x.axis("off")
    fig.suptitle(title, fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def cyclone_afloat(a: dict, t_over_c: float, title: str, path):
    """Afloat, to scale: one arm's section standing chord-up with the hub, A's motor and prop, the camera and
    the waterline; and from above, the waterplane's three strips."""
    fl = a["afloat"]
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(13, 5.4), gridspec_kw={"width_ratios": [1, 1.25]})
    c, h, zh, r0 = fl["chord_m"], fl["draft_m"], fl["z_hub_m"], fl["r0_m"]
    x = (1 - np.cos(np.linspace(0, math.pi, 120))) / 2
    yt = 5 * t_over_c * (0.2969 * np.sqrt(x) - 0.1260 * x - 0.3516 * x ** 2 + 0.2843 * x ** 3 - 0.1036 * x ** 4)
    z = (1 - x) * c - h
    ax.fill(np.r_[yt * c, -(yt * c)[::-1]], np.r_[z, z[::-1]], color="#ecf0f1", ec="#34495e", lw=1.4, zorder=3)
    ax.add_patch(plt.Circle((0, zh - h), r0, fc="none", ec="#e67e22", lw=1.5, ls="--", zorder=2))
    ax.text(-r0 - 0.01, zh - h + 0.6 * r0, "hub (behind)", ha="right", fontsize=8, color="#a04000")
    ax.add_patch(plt.Circle((0, fl["camera_height_m"] + 0.02), 0.02, color="#222222", zorder=4))
    top = c - h
    ax.add_patch(plt.Rectangle((-0.015, top), 0.03, fl["prop_height_m"] - top, color="#222222", zorder=4))
    ax.plot([-0.125, 0.125], [fl["prop_height_m"]] * 2, color="#222222", lw=3, zorder=4)
    ax.axhspan(-0.25, 0, color="#2e86c1", alpha=0.25, zorder=1)
    ax.axhline(0, color="#1b4f72", lw=1.2)
    ax.axhline(0.30, color="#c0392b", lw=1, ls=":")
    ax.text(0.14, 0.30, "props wanted here (30 cm)", va="bottom", fontsize=8, color="#c0392b")
    ax.text(0.14, fl["prop_height_m"], f"A's prop, {fl['prop_height_m'] * 100:.0f} cm up", va="center", fontsize=9)
    ax.text(0.14, -h / 2, f"draft {h * 100:.1f} cm of a {c * 100:.1f} cm chord", va="center", fontsize=9)
    ax.text(-0.14, fl["camera_height_m"] + 0.02, f"camera {fl['camera_height_m'] * 100:+.0f} cm", va="center", ha="right",
            fontsize=9)
    ax.set_xlim(-0.35, 0.45)
    ax.set_ylim(-0.2, 0.38)
    ax.set_aspect("equal")
    ax.set_xlabel("m")
    ax.set_title("One arm and the hub, seen along the arm", fontsize=10)
    R = fl["R_m"]
    for g in (math.radians(90 + 120 * k) for k in range(3)):
        bx.plot([r0 * math.cos(g), R * math.cos(g)], [r0 * math.sin(g), R * math.sin(g)], color="#1b4f72", lw=2.5)
    bx.add_patch(plt.Circle((0, 0), r0, color="#e67e22"))
    bx.set_aspect("equal")
    bx.set_xlim(-1.15 * R, 1.15 * R)
    bx.set_ylim(-0.75 * R, 1.15 * R)
    bx.set_title(f"From above: the waterplane, three thin strips out to the tips. GM {fl['gm_m']:.1f} m, "
                 f"roll period {fl['period_roll_s']:.2f} s", fontsize=10)
    bx.axis("off")
    fig.suptitle(title, fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


STATION_COLORS = {1.0: "#4C72B0", 0.75: "#DD8452", 0.5: "#55A868"}


def cyclone_sweep(rows: list[dict], title: str, path):
    """The arms-and-A sweep: each measure against the number of arms, a line for each place A sits (solid on
    every arm, dashed on every other); the design today ringed."""
    ok = [r for r in rows if r.get("ok")]
    panels = [("mass_kg", "Mass (kg)", None), ("off_wing_wh", "Launch + recovery (Wh)", None),
              ("hover_w", "Spinning hover (W shaft)", None), ("wind2_ms", "Mode 2: wind it holds station in (m/s)", None),
              ("range_km", "Mode 4: range on the battery (km)", None), ("build_s", "1->2: the spin building (s)", None),
              ("one_out_tw", "Mode 1, one A out: thrust / weight", 1.0), ("yaw4_nm", "Mode 4: yaw from A (N m)", None)]
    fig, axs = plt.subplots(2, 4, figsize=(17, 7.6))
    for ax, (key, name, line) in zip(axs.flat, panels):
        for every, ls, fill in ((1, "-", True), (2, "--", False)):
            for st, col in STATION_COLORS.items():
                pts = sorted((r["arms"], r[key]) for r in ok if r["a_station"] == st and r["a_every"] == every)
                if not pts:
                    continue
                x, y = zip(*pts)
                ax.plot(x, y, ls=ls, color=col, lw=1.8, marker="o", ms=7, mfc=col if fill else "white", mec=col,
                        label=f"A {'at the tips' if st == 1.0 else f'{st:g} out'}" + ("" if every == 1 else ", every other arm"))
        base = next(r for r in ok if r["arms"] == 3 and r["a_station"] == 1.0 and r["a_every"] == 1)
        ax.plot([3], [base[key]], "o", ms=15, mfc="none", mec="#222222", mew=1.4)
        if line is not None:
            ax.axhline(line, color="#444444", lw=0.8, ls=":")
        ax.set_xticks(list(sorted({r["arms"] for r in rows})))
        ax.set_xlabel("arms")
        ax.set_title(name, fontsize=10)
        ax.grid(alpha=0.3)
    h, lab = axs.flat[0].get_legend_handles_labels()
    fig.legend(h, lab, loc="lower center", ncol=6, fontsize=9, frameon=False)
    fig.suptitle(title + "  (ringed: the design today, 3 arms with A at the tips)", fontsize=12)
    fig.tight_layout(rect=(0, 0.05, 1, 0.96))
    fig.savefig(path, dpi=130)
    plt.close(fig)


LOITER_COLORS = {"liftbody": "#4C72B0", "tandem": "#DD8452"}


def loiter(rows: list[dict], path):
    """The loiter sweep: take-off mass and the power on station against hours on station, a line for each
    airframe (solid at the lower battery's specific energy, dashed at the higher)."""
    from osprey.recon.loiter import label

    ok = [r for r in rows if r.get("ok")]
    whs = sorted({r["wh_per_kg"] for r in rows})
    fig, axs = plt.subplots(1, 2, figsize=(12.5, 4.8))
    for ax, (key, name) in zip(axs, (("mass_total_kg", "Take-off mass (kg)"), ("power_w", "Power on station (W)"))):
        for a, col in LOITER_COLORS.items():
            for wh, ls, fill in zip(whs, ("-", "--"), (True, False)):
                pts = sorted((r["hours"], r["design"][key]) for r in ok if r["airframe"] == a and r["wh_per_kg"] == wh)
                if not pts:
                    continue
                x, y = zip(*pts)
                ax.plot(x, y, ls=ls, color=col, lw=1.8, marker="o", ms=7, mfc=col if fill else "white", mec=col,
                        label=f"{label(a)}, {wh:.0f} Wh/kg")
        ax.set_xlabel("hours on station")
        ax.set_xticks(sorted({r["hours"] for r in rows}))
        ax.set_title(name, fontsize=10)
        ax.grid(alpha=0.3)
    h, lab = axs[0].get_legend_handles_labels()
    fig.legend(h, lab, loc="lower center", ncol=4, fontsize=9, frameon=False)
    fig.suptitle("The loiter craft: each airframe sized for each time on station (missing points don't close)", fontsize=12)
    fig.tight_layout(rect=(0, 0.07, 1, 0.95))
    fig.savefig(path, dpi=130)
    plt.close(fig)
