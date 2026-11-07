"""Synthetic camera data in MuJoCo: RGB, depth and class masks with exact poses.

The boat is a mocap body driven by the motion model; each camera station is
its own mocap body so a stabilized camera can hold a level, aimed frame while
an unstabilized one moves with the hull. The scene is the scenario's dock
(if any): finger pier, pilings, a neighbouring boat, a person on the pier, a
fender and a slack dock line in the water.

Per run: <cam>/rgb_NNNN.png, <cam>/depth_NNNN.png (uint16 mm),
<cam>/class_NNNN.png (uint8 class index), sheet_NNNN.png (all cameras),
classes.json and labels.jsonl (time, boat pose, per-camera intrinsics and
camera-to-world pose). This is the data contract the CV models train on.

MuJoCo cameras are pinholes, so a fisheye is rendered as five 90 deg cube
faces on one mount and remapped to its equidistant image circle (r = f theta).
Its depth is range along the ray, not z-depth; pixels outside the circle are
class VOID.
"""

from __future__ import annotations

import json
import math
import os
import platform
import shutil
import subprocess
from pathlib import Path

import numpy as np

from osprey import frames, motion
from osprey.rig import Station, stations

CLASSES = ["water", "self", "dock", "piling", "boat", "person", "fender", "line", "sky"]
VOID = 255
# Cube faces of a fisheye, in its own camera frame: (look direction, image up).
FACES = [((0, 0, -1), (0, 1, 0)), ((1, 0, 0), (0, 1, 0)), ((-1, 0, 0), (0, 1, 0)),
         ((0, 1, 0), (0, 0, 1)), ((0, -1, 0), (0, 0, -1))]


def _face_frame(look, up) -> np.ndarray:
    """Columns: a camera's x (right), y (up) and z (back) axes for a look direction."""
    z = -np.asarray(look, float)
    x = np.cross(up, z)
    return np.stack([x, np.cross(z, x), z], 1)


def _fisheye_lut(s: Station, size: int, face_px: int) -> dict:
    """For each pixel of a size x size equidistant fisheye image: which cube
    face, row and column to read, and cos(angle off that face's axis)."""
    half = math.radians(s.cam.fov_deg) / 2
    f_px = size / 2 / half
    c = (np.arange(size) + 0.5) - size / 2
    x, y = np.meshgrid(c, -c)
    theta, phi = np.hypot(x, y) / f_px, np.arctan2(y, x)
    d = np.stack([np.sin(theta) * np.cos(phi), np.sin(theta) * np.sin(phi), -np.cos(theta)], -1)
    q = np.stack([d @ _face_frame(*fc) for fc in FACES])          # (5, size, size, 3)
    face = np.argmax(-q[..., 2], 0)
    q = np.take_along_axis(q, face[None, ..., None], 0)[0]
    cosf = -q[..., 2]
    col = np.clip(((q[..., 0] / cosf + 1) / 2 * face_px).astype(int), 0, face_px - 1)
    row = np.clip(((1 - q[..., 1] / cosf) / 2 * face_px).astype(int), 0, face_px - 1)
    return {"face": face, "row": row, "col": col, "cos": cosf, "inside": theta <= half, "f_px": f_px}
COLORS = {"self": "0.92 0.92 0.9 1", "dock": "0.55 0.45 0.35 1", "piling": "0.35 0.28 0.2 1",
          "boat": "0.85 0.85 0.95 1", "person": "0.9 0.35 0.2 1", "fender": "0.1 0.2 0.8 1",
          "line": "0.95 0.95 0.95 1", "cam": "0.9 0.1 0.1 1", "mast": "0.75 0.75 0.78 1"}


def _hull_mesh(b, scale: float = 1.0, name: str = "hull") -> str:
    xs = np.linspace(b.stern_x_m, b.bow_x_m, 14)
    hb = b.beam_m / 2

    def half(x):
        if x >= b.max_beam_x_m:
            return hb * (1 - ((x - b.max_beam_x_m) / (b.bow_x_m - b.max_beam_x_m)) ** 2)
        return hb * (1 - (1 - b.transom_beam_frac) * ((x - b.max_beam_x_m) / (b.stern_x_m - b.max_beam_x_m)) ** 2)

    v = []
    for x in xs:
        w = max(half(x), 0.02) * scale
        v += [(x * scale, w, b.freeboard_m), (x * scale, -w, b.freeboard_m),
              (x * scale, 0.6 * w, -0.5), (x * scale, -0.6 * w, -0.5)]
    return f'<mesh name="{name}" vertex="{" ".join(f"{a:.3f} {c:.3f} {d:.3f}" for a, c, d in v)}"/>'


def _geom(name, cls, **kw) -> str:
    attrs = " ".join(f'{k}="{v}"' for k, v in kw.items())
    return f'<geom name="{cls}__{name}" contype="0" conaffinity="0" {attrs}/>'


def mjcf(p, sts: list[Station], width: int, height: int) -> str:
    b, m, sp = p.boat, p.mast, p.sailplan
    d = p.dock
    hb = b.beam_m / 2
    self_geoms = [
        _geom("hull", "self", type="mesh", mesh="hull", rgba=COLORS["self"]),
        _geom("house", "self", type="box", pos=f"-1.6 0 {b.freeboard_m + 0.3}", size="1.8 1.1 0.3", rgba=COLORS["self"]),
        _geom("mast", "self", type="cylinder", fromto=f"0 0 {m.deck_z_m - 0.2} 0 0 {m.truck_z_m}",
              size=f"{m.radius_m}", rgba=COLORS["mast"]),
        _geom("boom", "self", type="capsule", fromto=f"-0.15 0 {sp.boom_z_m} {-sp.boom_length_m} 0 {sp.boom_z_m}",
              size="0.07", rgba=COLORS["mast"]),
        _geom("forestay", "self", type="capsule",
              fromto=f"{sp.forestay_tack_x_m} 0 {b.freeboard_m} 0.1 0 {sp.forestay_head_z_m}", size="0.008",
              rgba=COLORS["mast"]),
    ]
    for z, span in zip(m.spreaders_z_m, m.spreader_half_span_m):
        self_geoms.append(_geom(f"spreader{z:g}", "self", type="capsule", fromto=f"0 {span} {z} 0 {-span} {z}",
                                size="0.03", rgba=COLORS["mast"]))
        self_geoms.append(_geom(f"shroud{z:g}", "self", type="capsule",
                                fromto=f"0 {hb - 0.1} {b.freeboard_m} 0 {span} {z}", size="0.006",
                                rgba=COLORS["mast"]))
    for s in sts:
        if s.pod:
            continue
        x, y, z = s.pos
        self_geoms.append(_geom(f"cam_{s.id}", "self", type="sphere", pos=f"{x} {y} {z}", size="0.07",
                                rgba=COLORS["cam"]))
    for pod in p.pod:
        x, y, z = pod.pos_m
        r = getattr(p.electronics.kit, pod.kit).housing_radius_m
        self_geoms.append(_geom(f"pod_{pod.id}", "self", type="sphere", pos=f"{x} {y} {z}", size=f"{r}",
                                rgba=COLORS["cam"]))
    world = []
    if d:
        px = hb + d.pier_offset_m + d.pier_width_m / 2
        L = d.pier_length_m
        world += [
            _geom("finger", "dock", type="box", pos=f"{px} -1.5 {d.pier_height_m / 2 - 0.3}",
                  size=f"{d.pier_width_m / 2} {L / 2} {d.pier_height_m / 2 + 0.3}", rgba=COLORS["dock"]),
            _geom("main", "dock", type="box", pos=f"{px - 6} {b.bow_x_m + 4.0} {d.pier_height_m / 2 - 0.3}",
                  size=f"14 1.2 {d.pier_height_m / 2 + 0.3}", rgba=COLORS["dock"]),
        ]
        for i, y in enumerate([-1.5 - L / 2, -1.5, -1.5 + L / 2]):
            world.append(_geom(f"pile{i}", "piling", type="cylinder", pos=f"{px + d.pier_width_m / 2 + 0.2} {y} 1.0",
                               size=f"{d.piling_radius_m} 1.6", rgba=COLORS["piling"]))
        nx = -(hb + d.neighbour_offset_m + d.neighbour_beam_m / 2)
        world += [
            f'<body name="neighbour" pos="{nx} 0.5 0" euler="0 0 90">'
            + _geom("hull", "boat", type="mesh", mesh="nhull", rgba=COLORS["boat"])
            + _geom("mast", "boat", type="cylinder", fromto=f"0.5 0 1.2 0.5 0 15", size="0.1", rgba=COLORS["boat"])
            + "</body>",
            _geom("person", "person", type="capsule", fromto=f"{px} 1.0 {d.pier_height_m + 0.3} {px} 1.0 "
                                                             f"{d.pier_height_m + 1.55}", size="0.2",
                  rgba=COLORS["person"]),
            _geom("fender", "fender", type="capsule", fromto=f"{px - d.pier_width_m / 2 - 0.15} -3 0.1 "
                                                             f"{px - d.pier_width_m / 2 - 0.15} -3 0.7",
                  size="0.12", rgba=COLORS["fender"]),
            _geom("line", "line", type="capsule", fromto=f"{hb + 0.3} -6.5 0.02 {px - 0.6} -9 0.02", size="0.012",
                  rgba=COLORS["line"]),
        ]
    nb = type("nb", (), {})()
    for k_, v_ in vars(b).items():
        setattr(nb, k_, v_)
    if d:
        nb.beam_m = d.neighbour_beam_m
    cams = []
    for s in sts:
        if s.fisheye:
            faces = "".join(
                f'<camera name="{s.id}~{k}" fovy="90" xyaxes="{" ".join(f"{v:.6g}" for v in F[:, :2].T.ravel())}"/>'
                for k, F in enumerate(_face_frame(*fc) for fc in FACES))
            cams.append(f'<body name="mount_{s.id}" mocap="true">{faces}</body>')
            continue
        fovy = math.degrees(s.vfov(s.f_min))
        cams.append(f'<body name="mount_{s.id}" mocap="true"><camera name="{s.id}" fovy="{fovy:.3f}"/></body>')
    return f"""<mujoco model="osprey-{p.scenario.name}">
  <statistic extent="40" center="0 0 4"/>
  <visual>
    <global offwidth="{width}" offheight="{height}"/>
    <map znear="0.002" zfar="60"/>
    <quality shadowsize="4096"/>
    <headlight ambient="0.35 0.35 0.35" diffuse="0.4 0.4 0.4"/>
    <rgba haze="0.75 0.82 0.9 1"/>
  </visual>
  <asset>
    {_hull_mesh(b)}
    {_hull_mesh(nb, 0.9, "nhull")}
    <texture name="sea" type="2d" builtin="checker" rgb1="0.10 0.28 0.38" rgb2="0.12 0.31 0.42" width="512" height="512"/>
    <material name="sea" texture="sea" texrepeat="40 40" reflectance="0.15"/>
    <texture name="sky" type="skybox" builtin="gradient" rgb1="0.75 0.85 0.95" rgb2="0.35 0.5 0.75" width="256" height="256"/>
  </asset>
  <worldbody>
    <light directional="true" pos="0 0 30" dir="0.3 0.4 -1" diffuse="0.7 0.7 0.65" castshadow="true"/>
    <geom name="water__sea" type="plane" size="0 0 1" material="sea" contype="0" conaffinity="0"/>
    {"".join(world)}
    <body name="boat" mocap="true">{"".join(self_geoms)}
      <camera name="overview" pos="-16 -22 14" xyaxes="0.81 -0.59 0 0.27 0.37 0.89" fovy="50"/>
    </body>
    {"".join(cams)}
  </worldbody>
</mujoco>"""


def _backend():
    if "MUJOCO_GL" not in os.environ and platform.system() == "Linux" and not os.environ.get("DISPLAY"):
        os.environ["MUJOCO_GL"] = "egl"
    return os.environ.get("MUJOCO_GL", "default")


def _shoot(r, data, cams: list[str], geom_cls: np.ndarray, lut: dict | None):
    """RGB, depth (m) and class image from one camera, or a fisheye from its cube faces."""
    rgbs, depths, segs = [], [], []
    for c in cams:
        r.update_scene(data, camera=c)
        rgbs.append(r.render())
        r.enable_depth_rendering()
        r.update_scene(data, camera=c)
        depths.append(r.render())
        r.disable_depth_rendering()
        r.enable_segmentation_rendering()
        r.update_scene(data, camera=c)
        gid = r.render()[..., 0]
        r.disable_segmentation_rendering()
        segs.append(np.where(gid >= 0, geom_cls[np.clip(gid, 0, None)], CLASSES.index("sky")).astype(np.uint8))
    if lut is None:
        return rgbs[0], depths[0], segs[0]
    idx = (lut["face"], lut["row"], lut["col"])
    inside = lut["inside"]
    rgb = np.where(inside[..., None], np.stack(rgbs)[idx], 0).astype(np.uint8)
    depth = np.where(inside, np.stack(depths)[idx] / lut["cos"], 0.0)
    cls = np.where(inside, np.stack(segs)[idx], VOID).astype(np.uint8)
    return rgb, depth, cls


def render(p, out: Path, *, seconds: float = 6.0, fps: float = 5.0, scale: float = 0.25) -> dict:
    backend = _backend()
    import mujoco
    from PIL import Image, ImageDraw

    sts = [s for s in stations(p) if {"exterior", "near"} & set(s.zones)]
    size = {s.id: (int(s.image_circle_px * scale),) * 2 if s.fisheye else
            (int(s.cam.width_px * scale), int(s.cam.height_px * scale)) for s in sts}
    face_px = {s.id: int(2 * size[s.id][0] / math.radians(s.cam.fov_deg)) for s in sts if s.fisheye}
    W = max([w for w, _ in size.values()] + list(face_px.values()))
    H = max([h for _, h in size.values()] + list(face_px.values()))
    model = mujoco.MjModel.from_xml_string(mjcf(p, sts, W, H))
    data = mujoco.MjData(model)
    out.mkdir(parents=True, exist_ok=True)
    geom_cls = np.array([CLASSES.index(model.geom(i).name.split("__")[0]) for i in range(model.ngeom)], np.uint8)
    (out / "classes.json").write_text(json.dumps({"classes": CLASSES, "void": VOID}, indent=1))

    mot = motion.from_scenario(p, duration_s=max(seconds, 2.0), dt=0.02)
    R_all = mot.R(p.scenario.heading_deg)
    speed = p.scenario.boat_speed_kn * motion.KN
    head = frames.heading_to_yaw(p.scenario.heading_deg)
    fwd = np.array([math.cos(head), math.sin(head), 0.0])
    aims = vars(getattr(p.render, "aim", None) or type("o", (), {})())
    focals = vars(getattr(p.render, "focal_mm", None) or type("o", (), {})())
    mocap = {s.id: model.body(f"mount_{s.id}").mocapid[0] for s in sts}
    boat_mid = model.body("boat").mocapid[0]
    rnd = {s.id: mujoco.Renderer(model, face_px[s.id], face_px[s.id]) if s.fisheye else
           mujoco.Renderer(model, size[s.id][1], size[s.id][0]) for s in sts}
    luts = {s.id: _fisheye_lut(s, size[s.id][0], face_px[s.id]) for s in sts if s.fisheye}
    overview = mujoco.Renderer(model, 270, 480)
    labels = open(out / "labels.jsonl", "w")
    n = int(seconds * fps)
    for f in range(n):
        t = f / fps
        i = min(int(t / mot.dt), len(mot.t) - 1)
        R = R_all[i]
        pos = fwd * speed * (t - seconds / 2) + np.array([0, 0, mot.heave[i]])
        data.mocap_pos[boat_mid] = pos
        data.mocap_quat[boat_mid] = frames.quat_from_matrix(R)
        rec = {"t": t, "boat": {"pos": pos.tolist(), "R": R.tolist()}, "cameras": {}}
        for s in sts:
            default = s.boresight if s.fixed else frames.direction(s.face_az, -0.3)
            aim_b = np.array(aims.get(s.id, s.pos + default * 10), float)
            focal = float(focals.get(s.id, s.f_min))
            cam_w = pos + R @ s.pos
            if s.fixed or s.cam.stabilization.outer_hz <= 0:
                Rc = R @ frames.look_frame(aim_b - s.pos)
            else:
                Rc = frames.look_frame(pos + R @ aim_b - cam_w)
            data.mocap_pos[mocap[s.id]] = cam_w
            data.mocap_quat[mocap[s.id]] = frames.quat_from_matrix(Rc)
            w_, h_ = size[s.id]
            cam = {"pos": cam_w.tolist(), "R_cam_to_world": Rc.tolist(), "focal_mm": focal, "size": [w_, h_],
                   "axes": "x right, y up, looking along -z (MuJoCo)"}
            if s.fisheye:
                f_px = luts[s.id]["f_px"]
                cam |= {"projection": "equidistant", "f_px": f_px, "c": [w_ / 2, h_ / 2], "fov_deg": s.cam.fov_deg,
                        "depth": "range along the ray"}
            else:
                model.cam(s.id).fovy[0] = math.degrees(s.vfov(focal))
                fy = h_ / 2 / math.tan(s.vfov(focal) / 2)
                cam |= {"projection": "pinhole", "K": [[fy, 0, w_ / 2], [0, fy, h_ / 2], [0, 0, 1]],
                        "depth": "z along the optical axis"}
            rec["cameras"][s.id] = cam
        mujoco.mj_forward(model, data)
        tiles = []
        for s in sts:
            d_ = out / s.id
            d_.mkdir(exist_ok=True)
            rgb, depth, cls = _shoot(rnd[s.id], data, [f"{s.id}~{k}" for k in range(len(FACES))]
                                     if s.fisheye else [s.id], geom_cls, luts.get(s.id))
            Image.fromarray(rgb).save(d_ / f"rgb_{f:04d}.png")
            Image.fromarray(np.clip(depth * 1000, 0, 65535).astype(np.uint16)).save(d_ / f"depth_{f:04d}.png")
            Image.fromarray(cls).save(d_ / f"class_{f:04d}.png")
            tiles.append((s.id, Image.fromarray(rgb)))
        overview.update_scene(data, camera="overview")
        tiles.append(("overview", Image.fromarray(overview.render())))
        labels.write(json.dumps(rec) + "\n")
        tw, th = 480, 270
        cols = 3 if len(tiles) <= 6 else 4
        sheet = Image.new("RGB", (tw * cols, th * math.ceil(len(tiles) / cols)), "black")
        for k, (sid, im) in enumerate(tiles):
            tile = Image.new("RGB", (tw, th), "black")
            im = im.resize((th, th) if im.width == im.height else (tw, th))
            tile.paste(im, ((tw - im.width) // 2, 0))
            ImageDraw.Draw(tile).text((8, 6), f"{sid}  t={t:.1f}s", fill="white")
            sheet.paste(tile, ((k % cols) * tw, (k // cols) * th))
        sheet.save(out / f"sheet_{f:04d}.png")
    labels.close()
    for r in [*rnd.values(), overview]:
        r.close()
    if shutil.which("ffmpeg") and n > 1:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i", str(out / "sheet_%04d.png"),
                        "-pix_fmt", "yuv420p", str(out / "sheets.mp4")], check=False)
    return {"frames": n, "cameras": [s.id for s in sts], "backend": backend}
