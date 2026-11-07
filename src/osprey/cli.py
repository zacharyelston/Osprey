"""`uv run osprey calc | sim | render | all --scenario <name> [--rig <name>]`
`uv run osprey sweep [--workers N]`
`uv run osprey recon-size | recon-fly | recon | recon-render --mission <name>|all` (Osprey Recon)"""

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


def _task_rows(s: dict) -> list[tuple[str, str]]:
    """Report rows for what the drone did on its task, by kind."""
    fmt = lambda x: "never" if not math.isfinite(x) else f"{x / 60:.1f} min"
    rows = [("On scene", f"{fmt(s['on_scene_s'])} after launch"),
            (f"{s['progress_label'].capitalize()} reached", f"{s['progress']:.0%} (goal {s['goal']:.0%}); goal at "
             f"{fmt(s['t_goal_s'])}"),
            ("Time on task", fmt(s["task_s"]))]
    if s["kind"] == "search":
        rows += [("Search plan", f"{s['track_spacing_m']:.0f} m track spacing, effective sweep width "
                  f"{s['sweep_width_eff_m']:.0f} m, {s['passes']} pattern pass(es)")]
    elif s["kind"] == "survey":
        px = ", ".join(f"{k.replace('_', ' ')} {v:g} px" for k, v in s["px_across"].items())
        rows += [("Survey", f"{s['legs']} legs, {s['swath_m']:.0f} m swath at {s['track_spacing_m']:.0f} m spacing; "
                  f"ground sample {s['gsd_cm']:.1f} cm"),
                 ("Pixels across each target", px)]
    elif s["kind"] == "inspect":
        rows += [("Inspection", f"{s['standoff_m']:.0f} m standoff ({s['slant_m']:.0f} m slant); "
                  f"{s['focal_needed_mm']:.1f} mm focal needed of {s['focal_max_mm']:g} mm; "
                  f"{'resolves' if s['resolves'] else 'does NOT resolve'} it")]
    rows += [("Flight time / distance", f"{fmt(s['flight_time_s'])} / {s['distance_km']:.1f} km"),
             ("Battery left at recovery", f"{s['energy_left_frac']:.0%}"),
             ("Mean power, max bank", f"{s['power_mean_w']:.0f} W, {s['bank_max_deg']:.0f} deg")]
    return rows


def cmd_recon(args) -> int:
    """Size the Recon airframe for each mission (OpenMDAO), fly it (3-DOF),
    and with --mission all, fly every design through every mission."""
    import warnings

    from osprey.recon import figures as rfig
    from osprey.recon import fleet, flight, sizing
    from osprey.recon.params import MISSIONS
    from osprey.recon.params import load as load_mission

    warnings.filterwarnings("ignore", module="openaerostruct")
    rc = 0
    root = Path(args.out) if args.out else OUT / "recon"
    names = list(MISSIONS) if args.mission == "all" else [args.mission]
    designs = {}
    for name in names:
        p = load_mission(name)
        d_ = root / name
        d_.mkdir(parents=True, exist_ok=True)
        design_path = Path(args.design) if args.design else d_ / "design.json"
        history = []
        if args.cmd in ("recon-size", "recon") or not design_path.exists():
            design, history = sizing.size_and_fly(p)
            design_path.write_text(json.dumps(design, indent=1))
            rfig.planform(p, design, d_ / "planform.png")
        design = json.loads(design_path.read_text())
        designs[name] = design
        lines = [f"# Recon {name}: {p.mission.label}", "",
                 f"Generated {date.today().isoformat()} at {_sha()} by `uv run osprey {args.cmd} --mission {name}`. "
                 "Screening-level models; REF inputs in `design/recon/`.", "",
                 "## Sized airframe (OpenMDAO + OpenAeroStruct, SLSQP)", "",
                 f"Optimizer converged: **{'yes' if design['converged'] else 'NO'}**", "",
                 "| Quantity | Value |", "|---|---|"]
        rows = [("Task", f"{design['kind']}, {design['task_track_km']:.1f} km of track planned"),
                ("Take-off mass", f"{design['mass_total_kg']:.2f} kg (battery {design['battery_kg']:.2f}, shell "
                 f"{design['skin_kg']:.2f}, spar {design['spar_kg']:.3f}, fixed {design['fixed_kg']:.2f})"),
                ("Span / area / aspect ratio", f"{design['span_m']:.2f} m / {design['S_m2']:.3f} m² / "
                 f"{design['aspect_ratio']:.1f}"),
                ("Root / tip chord", f"{design['root_chord_m'] * 100:.1f} / {design['tip_chord_m'] * 100:.1f} cm "
                 f"(tip Re {design['re_tip']:,.0f})"),
                ("Spar tube, root / tip", f"r {design['spar_radius_mm'][1]:.1f} / {design['spar_radius_mm'][0]:.1f} mm, "
                 f"wall {design['spar_wall_mm'][1]:.2f} / {design['spar_wall_mm'][0]:.2f} mm"),
                ("Task speed, CL, L/D", f"{design['v_search_ms']:.1f} m/s, {design['CL']:.2f}, {design['LD']:.1f}"),
                ("Stall speed (sea level)", f"{design['v_stall_ms']:.1f} m/s (limit {p.limits.stall_speed_max_ms:g})"),
                ("Task power / endurance", f"{design['power_w']:.0f} W / {design['endurance_s'] / 60:.0f} min"),
                ("Mission time estimate (+{:.0%} reserve)".format(p.mission.reserve_frac),
                 f"{design['mission_time_s'] / 60:.0f} min"),
                ("Printed panels (220 x 220 x 250 mm bed)", f"{design['print_panels']}, chord fits: "
                 f"{'yes' if design['print_chord_ok'] else 'NO'}")]
        lines += [f"| {a} | {b} |" for a, b in rows] + ["", "![planform](planform.png)", ""]
        if history:
            lines += ["### Calibrating the mission-time model against the flight sim", "",
                      "Each round sizes the airframe, flies it with an unlimited battery, and scales the "
                      "optimizer's mission-time model by the energy the flight really used.", "",
                      "| Round | Time factor | Mass (kg) | Battery (kg) | Flown / estimated energy (Wh) | Progress flown | "
                      "Task flown (min) |", "|---|---|---|---|---|---|---|"]
            lines += [f"| {i + 1} | {h['time_factor']:.2f} | {h['mass_kg']:.2f} | {h['battery_kg']:.2f} | "
                      f"{h['flown_energy_wh']:.0f} / {h['estimated_energy_wh']:.0f} | {h['flown_progress']:.0%} | "
                      f"{h['flown_task_min']:.0f} |" for i, h in enumerate(history)]
            lines.append("")
        if args.cmd in ("recon-fly", "recon"):
            ac = flight.Aircraft.from_design(p, design)
            r = flight.simulate(p, ac)
            s = flight.summary(p, ac, r)
            rfig.track(p, r, d_ / "track.png")
            rfig.timeline(p, ac, r, d_ / "timeline.png")
            (d_ / "flight.json").write_text(json.dumps(s, indent=1, default=float))
            lines += ["## Flown through the mission (3-DOF point mass)", "",
                      f"Outcome: **{s['outcome']}**; left the task because: {s['left_task_because']}", "",
                      "| Quantity | Value |", "|---|---|", *[f"| {a} | {b} |" for a, b in _task_rows(s)], "",
                      "![track](track.png)", "", "![timeline](timeline.png)", ""]
            rc |= 0 if fleet.ok(s) else 1
            print(f"{name}: {s['outcome']}, {s['progress_label']} {s['progress']:.0%}, battery left "
                  f"{s['energy_left_frac']:.0%}, mass {design['mass_total_kg']:.2f} kg, span {design['span_m']:.2f} m")
        else:
            print(f"{name}: sized, mass {design['mass_total_kg']:.2f} kg, span {design['span_m']:.2f} m")
        (d_ / "report.md").write_text("\n".join(lines) + "\n")
        print(f"report: {d_ / 'report.md'}")
    if args.cmd == "recon" and len(names) > 1:
        rc |= _recon_matrix(root, designs, names)
    return rc


def _recon_matrix(root: Path, designs: dict, names: list[str]) -> int:
    from osprey.recon import figures as rfig
    from osprey.recon import fleet

    M = fleet.capability(designs, names)
    best = fleet.one_bird(M, designs)
    order = sorted(designs, key=lambda dn: designs[dn]["mass_total_kg"])
    head = "| Airframe sized for | Mass, span | " + " | ".join(names) + " |"
    lines = ["# Recon: one bird, many jobs", "",
             f"Generated {date.today().isoformat()} at {_sha()} by `uv run osprey recon --mission all`. Each row "
             "is the airframe sized for one mission, flown through every mission in the 3-DOF sim. A cell is "
             "✓ when it gets back aboard with the task's goal met; the number is the battery left (or how far it "
             "got).", "", head, "|" + "---|" * (len(names) + 2)]
    for dn in order:
        d = designs[dn]
        cells = [(f"✓ {s['energy_left_frac']:.0%}" if fleet.ok(s) else f"✗ {s['progress']:.0%} {s['progress_label']}")
                 for s in (M[dn][mn] for mn in names)]
        mark = " **(lightest that does everything)**" if dn == best else ""
        lines.append(f"| {dn}{mark} | {d['mass_total_kg']:.2f} kg, {d['span_m']:.2f} m | " + " | ".join(cells) + " |")
    (root / "matrix.md").write_text("\n".join(lines) + "\n")
    (root / "matrix.json").write_text(json.dumps({"order": order, "missions": names, "one_bird": best,
                                                  "designs": {dn: {k: designs[dn][k] for k in
                                                                   ("mass_total_kg", "span_m", "battery_kg")}
                                                              for dn in designs},
                                                  "cells": M}, indent=1, default=float))
    rfig.matrix(M, designs, names, order, best, root / "matrix.png")
    print("\n".join(lines[4:]))
    print(f"one bird: {best}; matrix: {root / 'matrix.md'}")
    return 0 if best else 1


def cmd_recon_render(args) -> int:
    """Render each mission's sized drone: hero over the sea, three-view,
    exploded print panels, a turntable GIF, and all of them side by side."""
    from osprey.recon import render as rr
    from osprey.recon.params import MISSIONS
    from osprey.recon.params import load as load_mission

    src = Path(args.run) if args.run else OUT / "recon"
    dst = Path(args.out) if args.out else OUT / "recon"
    names = MISSIONS if args.mission == "all" else [args.mission]
    lineup = []
    for name in names:
        f = src / name / "design.json"
        if not f.exists():
            print(f"{name}: no {f}; run `osprey recon --mission {name}` first")
            return 1
        p, d = load_mission(name), json.loads(f.read_text())
        o = dst / name
        rr.hero(p, d, o / "bird-hero.png")
        rr.threeview(p, d, o / "bird-threeview.png")
        rr.exploded(p, d, o / "bird-exploded.png")
        rr.turntable(p, d, o / "bird-turntable.gif")
        lineup.append((p, d, name))
        print(f"{name}: renders in {o}")
    if len(lineup) > 1:
        lineup.sort(key=lambda x: x[1]["span_m"])
        rr.lineup(lineup, dst / "bird-lineup.png")
        print(f"lineup: {dst / 'bird-lineup.png'}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="osprey", description=__doc__)
    ap.add_argument("cmd", choices=["calc", "sim", "render", "all", "sweep", "recon-size", "recon-fly", "recon",
                                    "recon-render"])
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
    ap.add_argument("--run", default=None, help="recon-render: a run directory holding <mission>/design.json "
                                                "(default out/recon)")
    args = ap.parse_args(argv)
    if args.cmd == "recon-render":
        return cmd_recon_render(args)
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
