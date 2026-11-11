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
