"""Renders of the Recon drone ("the bird") in MuJoCo, from a sized design:
- hero: banking over the sea, with the sailboat below;
- three-view: orthographic top, front and side;
- exploded: the printed wing panels pulled apart along the carbon spar;
- lineup: every mission's drone side by side, to scale.

The wing is the sized one; the pod, booms, tail and prop are REF geometry
(recon/geometry.py). Colours: printed LW-PLA shell in white and off-white by
panel, carbon black, a hi-vis orange pod and fins.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np

from osprey import frames
from osprey.recon import geometry

RGBA = {"shell0": "0.94 0.94 0.92 1", "shell1": "0.74 0.77 0.77 1", "spar": "0.07 0.07 0.08 1",
        "carbon": "0.09 0.09 0.10 1", "pod": "0.96 0.45 0.10 1", "gimbal": "0.16 0.16 0.18 1",
        "lens": "0.05 0.12 0.25 1", "tail": "0.96 0.45 0.10 1", "prop": "0.08 0.08 0.08 1",
        "disc": "0.3 0.3 0.3 0.12", "red": "0.95 0.1 0.1 1", "green": "0.1 0.9 0.2 1"}


def _mesh_xml(name: str, part: geometry.Part) -> str:
    v = " ".join(f"{x:.5f}" for x in part.verts.ravel())
    f = " ".join(str(i) for i in part.faces.ravel())
    return f'<mesh name="{name}" vertex="{v}" face="{f}"/>'


def _drone_xml(tag: str, parts, pos, quat) -> tuple[str, str]:
    assets, geoms = [], []
    for q in parts:
        mname = f"{tag}_{q.name}"
        assets.append(_mesh_xml(mname, q))
        mat = ' material="shell"' if q.kind.startswith("shell") or q.kind in ("pod", "tail") else ""
        geoms.append(f'<geom type="mesh" mesh="{mname}" rgba="{RGBA[q.kind]}"{mat} contype="0" conaffinity="0"/>')
    body = (f'<body name="{tag}" pos="{pos[0]:.4f} {pos[1]:.4f} {pos[2]:.4f}" '
            f'quat="{" ".join(f"{x:.6f}" for x in quat)}">{"".join(geoms)}</body>')
    return "".join(assets), body


def _cam(name: str, eye, target, *, ortho: float | None = None, fovy: float = 35.0) -> str:
    F = frames.look_frame(np.asarray(target, float) - np.asarray(eye, float))
    xy = " ".join(f"{v:.6f}" for v in np.r_[F[:, 0], F[:, 1]])
    proj = f' projection="orthographic" fovy="{ortho:.4f}"' if ortho else f' fovy="{fovy}"'
    return f'<camera name="{name}" pos="{eye[0]:.4f} {eye[1]:.4f} {eye[2]:.4f}" xyaxes="{xy}"{proj}/>'


def _quat(roll_deg: float = 0.0, pitch_deg: float = 0.0, yaw_deg: float = 0.0) -> np.ndarray:
    return frames.quat_from_matrix(frames.attitude(math.radians(roll_deg), math.radians(pitch_deg),
                                                   math.radians(yaw_deg)))


def _world(kind: str, assets: str, bodies: str, cams: str, W: int, H: int, extra: str = "",
           floor_on: bool = True) -> str:
    if kind == "sea":
        # Sparse soft white marks on a 64 px tile 25 m across: whitecaps about half a metre wide.
        env = """<texture name="sky" type="skybox" builtin="gradient" rgb1="0.80 0.88 0.96" rgb2="0.32 0.52 0.78"
                   width="512" height="512"/>
        <texture name="sea" type="2d" builtin="flat" rgb1="0.09 0.28 0.40" mark="random" random="0.004"
                 markrgb="0.42 0.56 0.64" width="48" height="48"/>
        <material name="sea" texture="sea" texrepeat="20 20" reflectance="0.08"/>"""
        floor = '<geom name="sea" type="plane" size="400 400 1" material="sea" contype="0" conaffinity="0"/>'
        haze = '<rgba haze="0.78 0.85 0.92 1"/>'
    else:
        env = """<texture name="sky" type="skybox" builtin="gradient" rgb1="0.62 0.66 0.72" rgb2="0.30 0.33 0.38"
                   width="512" height="512"/>
        <material name="floor" rgba="0.50 0.53 0.57 1" reflectance="0.15"/>"""
        floor = '<geom name="floor" type="plane" pos="0 0 -0.35" size="0 0 1" material="floor" contype="0" conaffinity="0"/>'
        haze = '<rgba haze="0.45 0.48 0.53 1"/>'
    if not floor_on:
        floor = ""
        env = env.replace('builtin="gradient" rgb1="0.62 0.66 0.72" rgb2="0.30 0.33 0.38"',
                          'builtin="flat" rgb1="0.46 0.49 0.54" rgb2="0.46 0.49 0.54"')
    return f"""<mujoco model="osprey-recon">
  <visual>
    <global offwidth="{W}" offheight="{H}"/>
    <quality shadowsize="8192" offsamples="8"/>
    <map znear="0.01" zfar="400" haze="0.6"/>
    <headlight ambient="0.30 0.30 0.30" diffuse="0.25 0.25 0.25" specular="0.1 0.1 0.1"/>
    {haze}
  </visual>
  <asset>
    {env}
    <material name="shell" specular="0.35" shininess="0.6"/>
    {assets}
  </asset>
  <worldbody>
    <light directional="true" pos="0 0 50" dir="-0.35 0.25 -1" diffuse="0.80 0.78 0.72" castshadow="true"/>
    <light directional="true" pos="0 0 50" dir="0.5 -0.4 -0.6" diffuse="0.25 0.27 0.32" castshadow="false"/>
    {floor}
    {extra}
    {bodies}
    {cams}
  </worldbody>
</mujoco>"""


def _boat_xml() -> tuple[str, str]:
    """The reference sailboat from the Nest scene, sails down, for scale below the drone."""
    from osprey.params import load
    from osprey.render import scene

    p = load("docking")
    b, m = p.boat, p.mast
    asset = scene._hull_mesh(b)
    body = (f'<body name="boat" pos="0 0 0" euler="0 0 20">'
            f'<geom type="mesh" mesh="hull" rgba="0.95 0.95 0.93 1" contype="0" conaffinity="0"/>'
            f'<geom type="box" pos="-1.6 0 {b.freeboard_m + 0.3}" size="1.8 1.1 0.3" rgba="0.95 0.95 0.93 1" '
            f'contype="0" conaffinity="0"/>'
            f'<geom type="cylinder" fromto="0 0 {m.deck_z_m - 0.2} 0 0 {m.truck_z_m}" size="{m.radius_m}" '
            f'rgba="0.75 0.75 0.78 1" contype="0" conaffinity="0"/>'
            f'<geom type="capsule" fromto="-0.15 0 {p.sailplan.boom_z_m} {-p.sailplan.boom_length_m} 0 '
            f'{p.sailplan.boom_z_m}" size="0.07" rgba="0.75 0.75 0.78 1" contype="0" conaffinity="0"/>'
            f'</body>')
    return asset, body


def _shoot(xml: str, cams: list[str], W: int, H: int) -> dict[str, np.ndarray]:
    from osprey.render.scene import _backend

    _backend()
    import mujoco

    model = mujoco.MjModel.from_xml_string(xml)
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    out = {}
    with mujoco.Renderer(model, H, W) as r:
        for c in cams:
            r.update_scene(data, camera=c)
            out[c] = r.render().copy()
    return out


def hero(p, d: dict, path: Path, W: int = 1600, H: int = 900):
    parts = geometry.build(p, d)
    pos = np.array([-55.0, 14.0, 45.0])                      # boat at the origin, ahead and below
    a, b = _drone_xml("bird", parts, pos, _quat(roll_deg=20, pitch_deg=-2, yaw_deg=-12))
    ba, bb = _boat_xml()
    s = max(d["span_m"], 1.3)
    eye = pos + np.array([-1.25, 1.0, 0.85]) * s
    to_drone, to_boat = pos - eye, -eye
    az = math.atan2(*(0.55 * to_drone[1::-1] / np.linalg.norm(to_drone[:2])
                      + 0.45 * to_boat[1::-1] / np.linalg.norm(to_boat[:2])))
    el = 0.5 * (math.atan2(to_drone[2], np.linalg.norm(to_drone[:2]))
                + math.atan2(to_boat[2], np.linalg.norm(to_boat[:2])))
    cam = _cam("hero", eye, eye + frames.direction(az, el), fovy=48)
    img = _shoot(_world("sea", a + ba, bb + b, cam, W, H), ["hero"], W, H)["hero"]
    _save(img, path)


def threeview(p, d: dict, path: Path, W: int = 1800, H: int = 640):
    parts = geometry.build(p, d)
    lo, hi = geometry.bounds(parts)
    a, b = _drone_xml("bird", parts, np.zeros(3), _quat())
    L, Wd, Ht = hi - lo
    c = (lo + hi) / 2
    w3 = W // 3
    r = H / w3
    # Orthographic: fovy is the vertical extent in metres, the horizontal one is fovy * width / height.
    cams = (_cam("top", c + [0, 0, 5], c, ortho=1.12 * max(L, Wd * r))
            + _cam("front", c + [5, 0, 0], c, ortho=1.12 * max(Ht, Wd * r))
            + _cam("side", c + [0, 5, 0], c, ortho=1.12 * max(Ht, L * r)))
    imgs = _shoot(_world("studio", a, b, cams, w3, H, floor_on=False), ["top", "front", "side"], w3, H)
    _save(np.concatenate([imgs["top"], imgs["front"], imgs["side"]], 1), path,
          labels=[(14, f"top: {d['span_m']:.2f} m span"),
                  (w3 + 14, {"bwb": "front: winglets, payload, pusher prop",
                             "crescent": "front: upswept tips, nose pod, pusher prop"}.get(
                      d.get("airframe"), "front: 3 deg dihedral, gimbal, pusher prop")),
                  (2 * w3 + 14, f"side: {L:.2f} m long")])


def exploded(p, d: dict, path: Path, W: int = 1600, H: int = 900):
    parts = geometry.build(p, d, explode=0.07)
    a, b = _drone_xml("bird", parts, np.zeros(3), _quat())
    span = d["span_m"]
    cam = _cam("x", np.array([1.1, 0.9, 0.75]) * span, [0.0, 0.0, 0.0], fovy=40)
    _save(_shoot(_world("studio", a, b, cam, W, H), ["x"], W, H)["x"], path)


def underside(p, d: dict, path: Path, W: int = 1400, H: int = 800):
    """A close look up at the pod from below and ahead: the gimbal, or the
    fore/aft pair and the belly fisheye."""
    parts = geometry.build(p, d)
    a, b = _drone_xml("bird", parts, np.zeros(3), _quat())
    g = p.geometry
    target = np.array([g.pod_nose_x_m - 0.35 * g.pod_length_m, 0.0, -0.06])
    cam = _cam("u", target + np.array([0.55, -0.45, -0.32]), target, fovy=34)
    _save(_shoot(_world("studio", a, b, cam, W, H, floor_on=False), ["u"], W, H)["u"], path)


def turntable(p, d: dict, path: Path, W: int = 900, H: int = 520, frames_n: int = 48):
    """An orbiting studio shot, saved as a looping GIF."""
    from PIL import Image

    parts = geometry.build(p, d)
    a, b = _drone_xml("bird", parts, np.zeros(3), _quat())
    r = 1.45 * max(d["span_m"], 1.2)
    cams = "".join(_cam(f"t{k}", [r * math.cos(th), r * math.sin(th), 0.55 * r], [-0.25, 0, 0], fovy=42)
                   for k, th in enumerate(np.linspace(0, 2 * math.pi, frames_n, endpoint=False) + 0.6))
    imgs = _shoot(_world("studio", a, b, cams, W, H), [f"t{k}" for k in range(frames_n)], W, H)
    first = Image.fromarray(imgs["t0"]).quantize(colors=160, method=Image.Quantize.MEDIANCUT)
    seq = [Image.fromarray(imgs[f"t{k}"]).quantize(palette=first, dither=Image.Dither.NONE) for k in range(frames_n)]
    path.parent.mkdir(parents=True, exist_ok=True)
    seq[0].save(path, save_all=True, append_images=seq[1:], duration=80, loop=0, optimize=True)


def lineup(designs: list[tuple[object, dict, str]], path: Path, W: int = 1800, H: int = 760):
    """Every mission's drone side by side, smallest on the left, in an
    orthographic view so they are truly to the same scale."""
    assets, bodies, ys = "", "", []
    y = 0.0
    gap = 0.35
    for i, (p, d, _) in enumerate(designs):
        y += d["span_m"] / 2
        ys.append(y)
        a, b = _drone_xml(f"bird{i}", geometry.build(p, d), np.array([0.0, y, 0.0]), _quat())
        y += d["span_m"] / 2 + gap
        assets += a
        bodies += b
    mid = (ys[0] - designs[0][1]["span_m"] / 2 + ys[-1] + designs[-1][1]["span_m"] / 2) / 2
    centre = np.array([-0.3, mid, 0.0])
    eye = centre + np.array([4.0, 0.0, 4.4])
    width = (y - gap) * 1.08
    fov = width * H / W
    cam = _cam("l", eye, centre, ortho=fov)
    img = _shoot(_world("studio", assets, bodies, cam, W, H), ["l"], W, H)["l"]
    px = lambda yy: int(W / 2 + (yy - mid) / width * W)
    labels = [(max(px(yy) - 150, 8), f"{name}: {d['span_m']:.2f} m, {d['mass_total_kg']:.2f} kg")
              for yy, (_, d, name) in zip(ys, designs)]
    _save(img, path, labels=labels, y=H - 60)


def _save(img: np.ndarray, path: Path, labels: list[tuple[int, str]] = (), y: int = 12):
    from PIL import Image, ImageDraw, ImageFont

    im = Image.fromarray(img)
    dr = ImageDraw.Draw(im)
    try:
        font = ImageFont.load_default(size=24)
    except TypeError:                      # Pillow < 10.1
        font = ImageFont.load_default()
    for x, txt in labels:
        dr.text((x, y), txt, fill=(245, 245, 245), font=font, stroke_width=2, stroke_fill=(40, 40, 45))
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path)
