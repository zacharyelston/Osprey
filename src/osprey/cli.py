"""`uv run osprey calc | sim | render | all --scenario <name> [--rig <name>]`
`uv run osprey sweep [--workers N]`
`uv run osprey recon-size | recon-fly | recon --mission <name>|all` (Osprey Recon)"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from datetime import date
from pathlib import Path

from types import SimpleNamespace

from osprey import calcs, figures, motion, tasking
from osprey.rig import stations
from osprey.params import OUT, RIGS, ROOT, SCENARIOS, load

COLS = ("status", "group", "check", "value", "limit", "note")


def _table(rows) -> str:
    rows = [COLS] + list(rows)
    widths = [min(max(len(r[i]) for r in rows), cap) for i, cap in enumerate((6, 14, 62, 26, 14, 70))]
    out = []
    for n, r in enumerate(rows):
        out.append("  ".join(c[:w].ljust(w) for c, w in zip(r, widths)).rstrip())
        if n == 0:
            out.append("  ".join("-" * w for w in widths))
    return "\n".join(out)


def _sha() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True,
                              text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _outdir(args) -> Path:
    d = Path(args.out) if args.out else OUT / f"{args.scenario}" / args.rig_name
    d.mkdir(parents=True, exist_ok=True)
    return d.resolve()


def cmd_calc(p, args) -> int:
    checks = calcs.run(p)
    print(_table(c.row() for c in checks))
    counts = {s: sum(c.status == s for c in checks) for s in ("FAIL", "WARN", "PASS", "INFO")}
    print(f"\n{args.scenario} / {args.rig_name}: " + "  ".join(f"{v} {k}" for k, v in counts.items()))
    d = _outdir(args)
    mot = motion.from_scenario(p, duration_s=120)
    figures.motion(mot, p.scenario.heel_deg, d / "motion.png")
    figures.coverage(p, d / "coverage.png")
    figures.reach(p, d / "reach.png")
    figs = ["motion.png", "coverage.png", "reach.png"]
    if hasattr(p.requirement, "dock_band_m"):
        figures.docking(p, d / "docking.png")
        figs.append("docking.png")
    lines = [f"# {args.scenario} on {args.rig_name}: check report", "",
             f"Generated {date.today().isoformat()} at {_sha()} by `uv run osprey calc --scenario {args.scenario} "
             f"--rig {args.rig_name}`. Screening-level models; REF inputs in `design/`.", "",
             f"**Result:** {counts['FAIL']} FAIL, {counts['WARN']} WARN, {counts['PASS']} PASS", ""]
    group = None
    for c in checks:
        if c.group != group:
            group = c.group
            lines += ["", f"## {group}", "", "| | Check | Value | Limit | Note |", "|---|---|---|---|---|"]
        badge = {"FAIL": "**FAIL**", "WARN": "WARN", "PASS": "pass", "INFO": "info"}[c.status]
        lines.append(f"| {badge} | {c.name} | {c.value} | {c.limit} | {c.note} |")
    lines += ["", "## Figures", ""] + [f"![{f}]({f})" for f in figs]
    (d / "report.md").write_text("\n".join(lines) + "\n")
    (d / "calc.json").write_text(json.dumps([c.__dict__ for c in checks], indent=1))
    print(f"report: {d / 'report.md'}")
    return 1 if counts["FAIL"] else 0


def cmd_sim(p, args) -> int:
    out = tasking.Sim(p).run()
    s = tasking.summary(out)
    d = _outdir(args)
    policy = (f"watch by sectors" if getattr(p.rig, "watch", "reserve") == "sectors"
              else f"reserve {p.rig.reserve}")
    title = f"Looking groups: {args.scenario} on {args.rig_name} ({policy}, max group {p.rig.max_group})"
    figures.gantt(out, d / "groups.png", title)
    rows = []
    for tid, v in s["tasks"].items():
        m = out["task_meta"][tid]
        rows.append(f"| {tid} | {m['cls'].replace('_', ' ')} | {m['need']} | {m['priority']} | {v['met_frac']:.0%} | "
                    f"{v['group_median']:.0f} / {v['group_max']} | {v['px_median']:.0f} | "
                    f"{v['sigma_frac_median']:.1%} | {v['starved_frac']:.0%} |")
    srows = [f"| {sid} | {v['tasked']:.0%} | {v['slew']:.0%} | {v['watch']:.0%} |" for sid, v in s["stations"].items()]
    md = [f"# {title}", "",
          f"Generated {date.today().isoformat()} at {_sha()} by `uv run osprey sim --scenario {args.scenario} "
          f"--rig {args.rig_name}`.", "",
          f"A camera always on watch: **{'yes' if s['always_watch'] else 'NO'}**. "
          f"Whole horizon swept: **{s['watch_full_frac']:.0%}** of the time (worst moment "
          f"{s['watch_min_frac']:.0%}); worst-bearing revisit {s['revisit_median_s']:.0f} s median, "
          f"{s['revisit_p95_s']:.0f} s p95. Pairs in groups: {s['pairs_in_pod']} within a pod, "
          f"{s['pairs_across']} across pods (pair-ticks).", "",
          "| Task | Class | Need | Priority | Need met | Group median / max | px median | Range σ/R median | Starved |",
          "|---|---|---|---|---|---|---|---|---|", *rows, "",
          "| Station | Tasked | Slewing | Watch |", "|---|---|---|---|", *srows, "", "![groups](groups.png)", ""]
    (d / "sim.md").write_text("\n".join(md))
    (d / "sim.json").write_text(json.dumps({"summary": s, "tasks": out["tasks"]}, indent=1, default=float))
    print("\n".join(md[6:-2]))
    print(f"report: {d / 'sim.md'}")
    return 0 if s["always_watch"] else 1


def cmd_render(p, args) -> int:
    from osprey.render import scene

    d = _outdir(args) / "render"
    if args.aims == "optimized":
        aims, focals = calcs.optimize_aims(p, [s for s in stations(p) if {"exterior", "near"} & set(s.zones)])
        p.render.aim, p.render.focal_mm = SimpleNamespace(**aims), SimpleNamespace(**focals)
    info = scene.render(p, d, seconds=args.seconds, fps=args.fps, scale=args.scale)
    print(f"rendered {info['frames']} frames x {len(info['cameras'])} cameras ({info['backend']}) -> {d}")
    return 0


def _job(argv: list[str]) -> tuple[list[str], int, str]:
    import contextlib
    import io

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = main(argv)
    return argv, rc, buf.getvalue()


def cmd_sweep(args) -> int:
    """Every scenario x rig, calc and sim, in parallel processes; one summary table."""
    import os
    from concurrent.futures import ProcessPoolExecutor

    os.environ.setdefault("OMP_NUM_THREADS", "1")
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
    root = Path(args.out) if args.out else OUT / "sweep"
    rigs = [r for r in RIGS if args.rig in (None, r)]
    jobs = [[cmd, "--scenario", sc, "--rig", rig, "--out", str((root / sc / rig).resolve())]
            for sc in SCENARIOS for rig in rigs for cmd in ("calc", "sim")]
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        for argv, rc, _ in ex.map(_job, jobs):
            print(f"rc={rc}  {' '.join(argv[:5])}", flush=True)
    rows = ["| Scenario | Rig | FAIL / WARN / PASS | Always a camera on watch | Whole horizon swept | Task needs met |",
            "|---|---|---|---|---|---|"]
    for sc in SCENARIOS:
        for rig in rigs:
            d = root / sc / rig
            checks = json.loads((d / "calc.json").read_text())
            n = {k: sum(c["status"] == k for c in checks) for k in ("FAIL", "WARN", "PASS")}
            sim = json.loads((d / "sim.json").read_text())["summary"]
            met = ", ".join(f"{t} {v['met_frac']:.0%}" for t, v in sim["tasks"].items())
            rows.append(f"| {sc} | {rig} | {n['FAIL']} / {n['WARN']} / {n['PASS']} | "
                        f"{'yes' if sim['always_watch'] else 'NO'} | {sim['watch_full_frac']:.0%} "
                        f"({sim['revisit_median_s']:.0f} s revisit) | {met} |")
    md = [f"# Osprey sweep", "", f"Generated {date.today().isoformat()} at {_sha()} by `uv run osprey sweep "
          f"--workers {args.workers}`.", "", *rows, ""]
    (root / "summary.md").write_text("\n".join(md))
    print("\n".join(rows))
    print(f"summary: {root / 'summary.md'}")
    return 0


def cmd_recon(args) -> int:
    """Size the Recon airframe for a mission (OpenMDAO), then fly it (3-DOF)."""
    import warnings

    from osprey.recon import figures as rfig
    from osprey.recon import flight, sizing
    from osprey.recon.params import MISSIONS
    from osprey.recon.params import load as load_mission

    warnings.filterwarnings("ignore", module="openaerostruct")
    rc = 0
    for name in (MISSIONS if args.mission == "all" else [args.mission]):
        p = load_mission(name)
        d_ = Path(args.out) / name if args.out else OUT / "recon" / name
        d_.mkdir(parents=True, exist_ok=True)
        design_path = Path(args.design) if args.design else d_ / "design.json"
        history = []
        if args.cmd in ("recon-size", "recon") or not design_path.exists():
            design, history = sizing.size_and_fly(p)
            design_path.write_text(json.dumps(design, indent=1))
            rfig.planform(p, design, d_ / "planform.png")
        design = json.loads(design_path.read_text())
        lines = [f"# Recon {name}: {p.mission.label}", "",
                 f"Generated {date.today().isoformat()} at {_sha()} by `uv run osprey {args.cmd} --mission {name}`. "
                 "Screening-level models; REF inputs in `design/recon/`.", "",
                 "## Sized airframe (OpenMDAO + OpenAeroStruct, SLSQP)", "",
                 f"Optimizer converged: **{'yes' if design['converged'] else 'NO'}**", "",
                 "| Quantity | Value |", "|---|---|"]
        rows = [("Take-off mass", f"{design['mass_total_kg']:.2f} kg (battery {design['battery_kg']:.2f}, shell "
                 f"{design['skin_kg']:.2f}, spar {design['spar_kg']:.3f}, fixed {design['fixed_kg']:.2f})"),
                ("Span / area / aspect ratio", f"{design['span_m']:.2f} m / {design['S_m2']:.3f} m² / "
                 f"{design['aspect_ratio']:.1f}"),
                ("Root / tip chord", f"{design['root_chord_m'] * 100:.1f} / {design['tip_chord_m'] * 100:.1f} cm "
                 f"(tip Re {design['re_tip']:,.0f})"),
                ("Spar tube, root / tip", f"r {design['spar_radius_mm'][1]:.1f} / {design['spar_radius_mm'][0]:.1f} mm, "
                 f"wall {design['spar_wall_mm'][1]:.2f} / {design['spar_wall_mm'][0]:.2f} mm"),
                ("Search speed, CL, L/D", f"{design['v_search_ms']:.1f} m/s, {design['CL']:.2f}, {design['LD']:.1f}"),
                ("Stall speed (sea level)", f"{design['v_stall_ms']:.1f} m/s (limit {p.limits.stall_speed_max_ms:g})"),
                ("Search power / endurance", f"{design['power_w']:.0f} W / {design['endurance_s'] / 60:.0f} min"),
                ("Mission time estimate (+{:.0%} reserve)".format(p.mission.reserve_frac),
                 f"{design['mission_time_s'] / 60:.0f} min"),
                ("Search plan", f"{design['search_track_km']:.1f} km of track at {design['track_spacing_m']:.0f} m "
                 f"spacing (effective sweep width {design['sweep_width_eff_m']:.0f} m)"),
                ("Printed panels (220 x 220 x 250 mm bed)", f"{design['print_panels']}, chord fits: "
                 f"{'yes' if design['print_chord_ok'] else 'NO'}")]
        lines += [f"| {a} | {b} |" for a, b in rows] + ["", "![planform](planform.png)", ""]
        if history:
            lines += ["### Calibrating the mission-time model against the flight sim", "",
                      "Each round sizes the airframe, flies it with an unlimited battery, and scales the "
                      "optimizer's mission-time model by the energy the flight really used.", "",
                      "| Round | Time factor | Mass (kg) | Battery (kg) | Flown / estimated energy (Wh) | POD flown | "
                      "Search flown (min) |", "|---|---|---|---|---|---|---|"]
            lines += [f"| {i + 1} | {h['time_factor']:.2f} | {h['mass_kg']:.2f} | {h['battery_kg']:.2f} | "
                      f"{h['flown_energy_wh']:.0f} / {h['estimated_energy_wh']:.0f} | {h['flown_pod']:.0%} | "
                      f"{h['flown_search_min']:.0f} |"
                      for i, h in enumerate(history)]
            lines.append("")
        if args.cmd in ("recon-fly", "recon"):
            ac = flight.Aircraft.from_design(p, design)
            r = flight.simulate(p, ac)
            s = flight.summary(p, ac, r)
            rfig.track(p, r, d_ / "track.png")
            rfig.timeline(p, ac, r, d_ / "timeline.png")
            (d_ / "flight.json").write_text(json.dumps(s, indent=1, default=float))
            fmt = lambda x: "never" if not math.isfinite(x) else f"{x / 60:.1f} min"
            lines += ["## Flown through the mission (3-DOF point mass)", "",
                      f"Outcome: **{s['outcome']}**; left the search because: {s['left_search_because']}", "",
                      "| Quantity | Value |", "|---|---|",
                      f"| On scene | {fmt(s['on_scene_s'])} after launch |",
                      f"| POD reached | {s['pod']:.0%} (plan {s['pod_planned']:.0%}); 50 % at {fmt(s['t_pod50_s'])}, "
                      f"90 % at {fmt(s['t_pod90_s'])} |",
                      f"| Search time | {fmt(s['search_s'])} ({s['search_passes']} pattern pass"
                      f"{'es' if s['search_passes'] > 1 else ''}) |",
                      f"| Flight time / distance | {fmt(s['flight_time_s'])} / {s['distance_km']:.1f} km |",
                      f"| Battery left at recovery | {s['energy_left_frac']:.0%} |",
                      f"| Mean power, max bank | {s['power_mean_w']:.0f} W, {s['bank_max_deg']:.0f} deg |", "",
                      "![track](track.png)", "", "![timeline](timeline.png)", ""]
            ok = s["outcome"] == "recovered" and s["pod"] >= p.mission.search_pod - 1e-6
            rc |= 0 if ok else 1
            print(f"{name}: {s['outcome']}, POD {s['pod']:.0%}, battery left {s['energy_left_frac']:.0%}, "
                  f"mass {design['mass_total_kg']:.2f} kg, span {design['span_m']:.2f} m")
        else:
            print(f"{name}: sized, mass {design['mass_total_kg']:.2f} kg, span {design['span_m']:.2f} m")
        (d_ / "report.md").write_text("\n".join(lines) + "\n")
        print(f"report: {d_ / 'report.md'}")
    return rc


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="osprey", description=__doc__)
    ap.add_argument("cmd", choices=["calc", "sim", "render", "all", "sweep", "recon-size", "recon-fly", "recon"])
    ap.add_argument("--scenario", default="coastal-watch", choices=SCENARIOS)
    ap.add_argument("--rig", default=None, choices=RIGS, help="override the scenario's rig")
    ap.add_argument("--out", default=None, help="output directory (absolute); default out/<scenario>/<rig>")
    ap.add_argument("--seconds", type=float, default=6.0, help="render: clip length")
    ap.add_argument("--fps", type=float, default=5.0, help="render: frames per second")
    ap.add_argument("--scale", type=float, default=0.25, help="render: fraction of each camera's native resolution")
    ap.add_argument("--aims", choices=["scenario", "optimized"], default="scenario",
                    help="render: PTZ aims from the scenario file, or optimized for two-view docking coverage")
    ap.add_argument("--workers", type=int, default=8, help="sweep: parallel processes")
    ap.add_argument("--mission", default="sar-datum", help="recon: a design/recon/missions name, or all")
    ap.add_argument("--design", default=None, help="recon-fly: a design.json to fly instead of sizing one")
    args = ap.parse_args(argv)
    if args.cmd.startswith("recon"):
        return cmd_recon(args)
    if args.cmd == "sweep":
        return cmd_sweep(args)
    p = load(args.scenario, rig=args.rig)
    args.rig_name = p.rig.name
    rc = 0
    for cmd in (["calc", "sim", "render"] if args.cmd == "all" else [args.cmd]):
        rc |= {"calc": cmd_calc, "sim": cmd_sim, "render": cmd_render}[cmd](p, args)
    return rc


if __name__ == "__main__":
    sys.exit(main())
