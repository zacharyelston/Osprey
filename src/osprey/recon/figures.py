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
