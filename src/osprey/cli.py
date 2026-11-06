"""`uv run osprey calc | sim | render | all --scenario <name> [--rig <name>]`
`uv run osprey sweep [--workers N]`"""

from __future__ import annotations

import argparse
import json
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
    title = f"Looking groups: {args.scenario} on {args.rig_name} (reserve {p.rig.reserve}, max group {p.rig.max_group})"
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
          f"A camera always on watch: **{'yes' if s['always_watch'] else 'NO'}**", "",
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
    rows = ["| Scenario | Rig | FAIL / WARN / PASS | Always a camera on watch | Task needs met |", "|---|---|---|---|---|"]
    for sc in SCENARIOS:
        for rig in rigs:
            d = root / sc / rig
            checks = json.loads((d / "calc.json").read_text())
            n = {k: sum(c["status"] == k for c in checks) for k in ("FAIL", "WARN", "PASS")}
            sim = json.loads((d / "sim.json").read_text())["summary"]
            met = ", ".join(f"{t} {v['met_frac']:.0%}" for t, v in sim["tasks"].items())
            rows.append(f"| {sc} | {rig} | {n['FAIL']} / {n['WARN']} / {n['PASS']} | "
                        f"{'yes' if sim['always_watch'] else 'NO'} | {met} |")
    md = [f"# Osprey sweep", "", f"Generated {date.today().isoformat()} at {_sha()} by `uv run osprey sweep "
          f"--workers {args.workers}`.", "", *rows, ""]
    (root / "summary.md").write_text("\n".join(md))
    print("\n".join(rows))
    print(f"summary: {root / 'summary.md'}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="osprey", description=__doc__)
    ap.add_argument("cmd", choices=["calc", "sim", "render", "all", "sweep"])
    ap.add_argument("--scenario", default="coastal-watch", choices=SCENARIOS)
    ap.add_argument("--rig", default=None, choices=RIGS, help="override the scenario's rig")
    ap.add_argument("--out", default=None, help="output directory (absolute); default out/<scenario>/<rig>")
    ap.add_argument("--seconds", type=float, default=6.0, help="render: clip length")
    ap.add_argument("--fps", type=float, default=5.0, help="render: frames per second")
    ap.add_argument("--scale", type=float, default=0.25, help="render: fraction of each camera's native resolution")
    ap.add_argument("--aims", choices=["scenario", "optimized"], default="scenario",
                    help="render: PTZ aims from the scenario file, or optimized for two-view docking coverage")
    ap.add_argument("--workers", type=int, default=8, help="sweep: parallel processes")
    args = ap.parse_args(argv)
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
